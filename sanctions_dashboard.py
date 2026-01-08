import streamlit as st
import requests
import sqlite3
import pandas as pd
from datetime import datetime
import time
import os
import json
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# ==========================================
# 0. CONFIGURATION & SETUP
# ==========================================
# Load environment variables (API Keys)
load_dotenv()

# Configure Gemini (for the China Agent)
if os.getenv("GEMINI_API_KEY"):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 1. DATABASE & STORAGE LAYER
# ==========================================
DB_FILE = "sanctions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS china_list
                 (name TEXT, entity_type TEXT, date_added TEXT, source_url TEXT, notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS agent_logs
                 (timestamp TEXT, action TEXT, details TEXT)''')
    conn.commit()
    conn.close()

def log_agent_action(action, details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO agent_logs VALUES (?, ?, ?)", 
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, details))
    conn.commit()
    conn.close()

# ==========================================
# 2. USA AGENT (Official API - Debug Mode)
# ==========================================
class USASanctionsAgent:
    API_URL = "https://data.trade.gov/consolidated_screening_list/v1/search"
    
    def __init__(self):
        # Support both naming conventions
        self.API_KEY = os.getenv('USA_TRADE_GOV_API_KEY')

    def search(self, search_params):
        """
        Queries the US Trade.gov API with debug logging.
        """
        # 1. Check Key
        if not self.API_KEY:
            return [{"error": "Missing API Key. Check your .env file."}]

        # 2. Prepare Params
        clean_params = {k: v for k, v in search_params.items() if v}
        if "fuzzy_name" not in clean_params:
            clean_params["fuzzy_name"] = "true"

        headers = {
            'Cache-Control': 'no-cache',
            'subscription-key': self.API_KEY
        }

        # --- DEBUG LOG 1: THE REQUEST ---
        print(f"\n[DEBUG] Requesting URL: {self.API_URL}")
        print(f"[DEBUG] Params: {clean_params}")
        # Don't print the full key for security, just the first few chars
        masked_key = self.API_KEY[:4] + "..." if self.API_KEY else "None"
        print(f"[DEBUG] Headers: {{'Subscription-Key': '{masked_key}'}}")

        try:
            response = requests.get(self.API_URL, params=clean_params, headers=headers, timeout=15)
            
            # --- DEBUG LOG 2: THE RESPONSE ---
            print(f"[DEBUG] Status Code: {response.status_code}")
            
            # If the response is not 200 OK, print the raw text to see the error message
            if response.status_code != 200:
                print(f"[DEBUG] RAW ERROR RESPONSE: {response.text}")
                return [{"error": f"API Error {response.status_code}: {response.text[:200]}"}]

            # If it IS 200, try to parse JSON
            try:
                data = response.json()
                results = data.get('results', [])
                print(f"[DEBUG] Success. Found {len(results)} results.")
                
                if not results:
                    return []
                return self._format_results(results)
                
            except json.JSONDecodeError:
                # This is where your error was happening
                print(f"[DEBUG] JSON PARSE FAILED. Raw Response:\n{response.text}")
                return [{"error": "Server returned invalid JSON. Check terminal for raw output."}]

        except Exception as e:
            print(f"[DEBUG] CRITICAL FAILURE: {str(e)}")
            return [{"error": f"Connection failed: {str(e)}"}]

    def _format_results(self, results):
        formatted = []
        for r in results:
            addresses = r.get('addresses', [])
            first_addr = addresses[0].get('address') if addresses else "N/A"
            city = addresses[0].get('city') if addresses else ""
            country = addresses[0].get('country') if addresses else ""
            
            full_loc = f"{first_addr}, {city} ({country})"
            
            formatted.append({
                "Score": r.get('score', 'N/A'),
                "Name": r.get('name'),
                "List": r.get('source', 'USA'),
                "Type": r.get('type', 'Entity'),
                "Address": full_loc,
                "Remark": r.get('remarks') or r.get('federal_register_notice', 'See official link'),
                "Link": r.get('source_list_url')
            })
        return formatted

# ==========================================
# 3. CHINA AGENT (Playwright + Gemini)
# ==========================================
class ChinaMonitorAgent:
    """
    Uses Playwright to browse websites and Gemini to read/parse the news.
    """
    TARGET_URL = "http://english.mofcom.gov.cn/article/newsrelease/significantnews/"
    
    def scan_for_updates(self):
        if not os.getenv("GEMINI_API_KEY"):
            return "Error: Missing GEMINI_API_KEY in .env file."

        new_findings = []
        log_agent_action("START_SCAN", "Launching Playwright Browser...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                log_agent_action("BROWSER", f"Navigating to {self.TARGET_URL}")
                page.goto(self.TARGET_URL, timeout=60000)
                page.wait_for_selector('a', timeout=10000)
                
                # Extract links using JS in the browser
                articles = page.evaluate("""() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return links.map(a => ({
                        text: a.innerText.trim(),
                        href: a.href
                    })).filter(item => item.text.length > 20); 
                }""")
                
                log_agent_action("ANALYSIS", f"Found {len(articles)} links. Analyzing with Gemini...")

                count_relevant = 0
                # Analyze top 10 most recent to save time/tokens
                for article in articles[:10]:
                    analysis = self._ask_gemini(article['text'])
                    if analysis and analysis.get('is_sanction_related'):
                        count_relevant += 1
                        for entity in analysis.get('entities', []):
                            self._save_finding(entity, article['text'], article['href'])
                
                browser.close()
                log_agent_action("SCAN_COMPLETE", f"Scan finished. Found {count_relevant} relevant updates.")
                return f"Agent Report: Scanned {len(articles)} headlines. Identified {count_relevant} sanction-related items."

        except Exception as e:
            log_agent_action("CRITICAL_FAILURE", str(e))
            return f"Agent crashed: {str(e)}"

    def _ask_gemini(self, text):
        prompt = f"""
        Analyze this MOFCOM headline: "{text}"
        Does it indicate a sanction, 'Unreliable Entity' list addition, or restriction?
        Return JSON: {{ "is_sanction_related": true/false, "entities": ["Company A"] }}
        """
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except:
            return None

    def _save_finding(self, entity_name, headline, url):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM china_list WHERE name=?", (entity_name,))
        if not c.fetchone():
            c.execute("INSERT INTO china_list VALUES (?, ?, ?, ?, ?)", 
                      (entity_name, "Sanctioned Entity", datetime.now().strftime("%Y-%m-%d"), url, f"Source: {headline}"))
            conn.commit()
        conn.close()

    def search_local_db(self, query):
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query(f"SELECT * FROM china_list WHERE name LIKE '%{query}%'", conn)
        conn.close()
        return df

# ==========================================
# 4. DASHBOARD UI
# ==========================================
def main():
    st.set_page_config(page_title="Global Sanctions Checker", layout="wide")
    init_db()
    
    st.title("🛡️ Sanctions Compliance Dashboard")
    
    # --- SECTION A: SEARCH FORM ---
    with st.container():
        st.subheader("1. Entity Search")
        
        # Primary Inputs
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            name_input = st.text_input("Entity Name", placeholder="e.g. Huawei")
        with col2:
            country_input = st.selectbox("Country", ["", "CN", "RU", "IR", "NK", "US"])
        with col3:
            fuzzy_toggle = st.checkbox("Fuzzy Match", value=True)

        # Advanced Inputs (Collapsible)
        with st.expander("Advanced Filters (Address, City, Sources, etc.)"):
            adv_c1, adv_c2, adv_c3 = st.columns(3)
            with adv_c1:
                city_input = st.text_input("City")
                address_input = st.text_input("Address")
            with adv_c2:
                state_input = st.text_input("State/Province")
                postal_input = st.text_input("Postal Code")
            with adv_c3:
                # Sources: CAP, DPL, EL, etc.
                sources_input = st.text_input("Sources (Codes)", placeholder="e.g. BIS, OFAC")
                full_addr_input = st.text_input("Full Address String")

        if st.button("Check Sanctions Lists", type="primary"):
            if not name_input:
                st.warning("Please enter at least a name.")
            else:
                with st.spinner(f"Scanning databases..."):
                    
                    # 1. Build US Params
                    us_params = {
                        "name": name_input,
                        "countries": country_input,
                        "city": city_input,
                        "address": address_input,
                        "postal_code": postal_input,
                        "full_address": full_addr_input,
                        "sources": sources_input,
                        "fuzzy_name": "true" if fuzzy_toggle else "false",
                        "size": 50 # listed maximum on their docs
                    }

                    # 2. Execute Searches
                    us_agent = USASanctionsAgent()
                    us_results = us_agent.search(us_params)
                    
                    cn_agent = ChinaMonitorAgent()
                    cn_results = cn_agent.search_local_db(name_input)
                
                # 3. Display Results
                st.divider()
                
                # USA
                st.markdown(f"### 🇺🇸 USA Matches ({len(us_results) if us_results and 'error' not in us_results[0] else 0})")
                if us_results and "error" in us_results[0]:
                    st.error(us_results[0]["error"])
                elif us_results:
                    st.dataframe(pd.DataFrame(us_results), use_container_width=True)
                else:
                    st.success("No matches found in USA Consolidated List.")

                # China
                st.markdown("### 🇨🇳 China Matches (Internal Database)")
                if not cn_results.empty:
                    st.dataframe(cn_results, use_container_width=True)
                    st.warning("⚠️ Match found in China Monitoring Database.")
                else:
                    st.success("No matches found in local China cache.")

    st.divider()

    # --- SECTION B: AGENT CONTROL ---
    with st.container():
        st.subheader("2. AI Agent Control")
        col_a, col_b = st.columns([1, 3])
        
        with col_a:
            st.info("Agent: **Playwright** (Browser) + **Gemini** (Analysis)")
            if st.button("🔄 Run China News Scan"):
                with st.spinner("Agent is reading Ministry of Commerce news..."):
                    agent = ChinaMonitorAgent()
                    report = agent.scan_for_updates()
                    st.success(report)
                    time.sleep(2)
                    st.rerun()
                    
        with col_b:
            st.markdown("**Agent Activity Log**")
            conn = sqlite3.connect(DB_FILE)
            logs = pd.read_sql_query("SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT 5", conn)
            conn.close()
            st.dataframe(logs, hide_index=True)

if __name__ == "__main__":
    main()