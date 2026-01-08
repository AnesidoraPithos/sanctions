import os
import json
from playwright.sync_api import sync_playwright
from config import get_gemini_model
import database as db

class ChinaActiveAgent:
    BASE_URL = "http://english.mofcom.gov.cn/"
    
    def run_search_mission(self, keywords=["Unreliable Entity", "Sanctions"]):
        model = get_gemini_model()
        if not model:
            return "Error: Gemini API Key missing."

        db.log_agent_action("MISSION_START", f"Starting active search for: {keywords}")
        findings_count = 0
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # 1. NAVIGATE
                db.log_agent_action("NAVIGATE", f"Going to {self.BASE_URL}")
                page.goto(self.BASE_URL, timeout=60000)
                
                # 2. SEARCH
                try:
                    db.log_agent_action("INTERACT", "Locating search bar...")
                    # Generic selector for search input
                    search_input = page.locator("input[type='text'], input[name='q'], input[id='search']").first
                    search_input.click()
                    search_input.fill(keywords[0])
                    page.press("body", "Enter")
                    page.wait_for_timeout(3000)
                except Exception as e:
                    return f"Failed to interact with search bar: {str(e)}"

                # 3. PAGINATION LOOP
                max_pages = 3
                current_page = 1
                
                while current_page <= max_pages:
                    db.log_agent_action("SCANNING", f"Processing Page {current_page}...")
                    
                    page_results = page.evaluate("""() => {
                        const items = Array.from(document.querySelectorAll('a'));
                        return items.map(a => ({
                            text: a.innerText.trim(),
                            href: a.href
                        })).filter(i => i.text.length > 20);
                    }""")
                    
                    # 4. GEMINI ANALYSIS
                    for item in page_results[:10]:
                        analysis = self._analyze_with_gemini(model, item['text'])
                        
                        if analysis and analysis.get('is_relevant_announcement'):
                            entities = analysis.get('entities', [])
                            for entity in entities:
                                db.save_china_finding(entity, item['text'], item['href'])
                            findings_count += 1
                    
                    # 5. NEXT PAGE
                    try:
                        next_btn = page.get_by_text("Next", exact=False).or_(page.get_by_text(">", exact=True)).first
                        if next_btn.is_visible():
                            next_btn.click()
                            page.wait_for_timeout(3000)
                            current_page += 1
                        else:
                            break
                    except:
                        break

                browser.close()
                db.log_agent_action("MISSION_COMPLETE", f"Found {findings_count} entities.")
                return f"Mission Complete. Scanned {current_page} pages. Added {findings_count} new entities."

        except Exception as e:
            db.log_agent_action("CRITICAL_FAILURE", str(e))
            return f"Agent crashed: {str(e)}"

    def _analyze_with_gemini(self, model, text):
        prompt = f"""
        Analyze this search result title from MOFCOM: "{text}"
        Does it indicate a sanction, 'Unreliable Entity List' addition, or restriction?
        Return JSON ONLY: {{ "is_relevant_announcement": true/false, "entities": ["Company A"] }}
        """
        try:
            response = model.generate_content(prompt)
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_json)
        except:
            return None