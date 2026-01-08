import streamlit as st
import pandas as pd
import time
import database as db
from usa_agent import USASanctionsAgent
from china_agent import ChinaActiveAgent

def main():
    st.set_page_config(page_title="Global Sanctions Checker", layout="wide")
    db.init_db()
    
    st.title("🛡️ Sanctions Compliance Dashboard")
    
    # --- SECTION A: SEARCH FORM ---
    with st.container():
        st.subheader("1. Entity Search")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            name_input = st.text_input("Entity Name", placeholder="e.g. Huawei")
        with col2:
            country_input = st.selectbox("Country", ["", "CN", "RU", "IR", "NK", "US"])
        with col3:
            fuzzy_toggle = st.checkbox("Fuzzy Match", value=True)

        with st.expander("Advanced Filters"):
            adv_c1, adv_c2, adv_c3 = st.columns(3)
            with adv_c1:
                city_input = st.text_input("City")
                address_input = st.text_input("Address")
            with adv_c2:
                sources_input = st.text_input("Sources (Codes)", placeholder="e.g. BIS")
            with adv_c3:
                full_addr_input = st.text_input("Full Address String")

        if st.button("Check Sanctions Lists", type="primary"):
            if not name_input:
                st.warning("Please enter at least a name.")
            else:
                with st.spinner(f"Scanning databases..."):
                    us_params = {
                        "name": name_input,
                        "countries": country_input,
                        "city": city_input,
                        "address": address_input,
                        "full_address": full_addr_input,
                        "sources": sources_input,
                        "fuzzy_name": "true" if fuzzy_toggle else "false",
                        "size": 100
                    }
                    
                    # Call Agents
                    us_agent = USASanctionsAgent()
                    us_results = us_agent.search(us_params)
                    cn_results = db.search_china_db(name_input)
                
                st.divider()
                
                # Render Results
                match_count = len(us_results) if us_results and 'error' not in us_results[0] else 0
                st.markdown(f"### 🇺🇸 USA Matches ({match_count})")
                
                if us_results and "error" in us_results[0]:
                    st.error(us_results[0]["error"])
                elif us_results:
                    st.dataframe(pd.DataFrame(us_results), use_container_width=True)
                else:
                    st.success("No matches found in USA Consolidated List.")

                st.markdown("### 🇨🇳 China Matches (Internal Database)")
                if not cn_results.empty:
                    st.dataframe(cn_results, use_container_width=True)
                    st.warning("⚠️ Match found in China Monitoring Database.")
                else:
                    st.success("No matches found in local China cache.")

    st.divider()

    # --- SECTION B: ACTIVE AGENT CONTROL ---
    with st.container():
        st.subheader("2. 🤖 China Active Search Agent")
        
        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.info("Active Search: Types keywords, paginates results, and uses Gemini to extract entities.")
            search_term = st.text_input("Search Keywords", value="Unreliable Entity List")
            
            if st.button("🚀 Launch Search Mission"):
                with st.spinner(f"Agent is searching for '{search_term}'..."):
                    agent = ChinaActiveAgent()
                    report = agent.run_search_mission([search_term])
                    st.success(report)
                    time.sleep(2)
                    st.rerun()
                    
        with col_b:
            st.markdown("**Agent Activity Log (Real-time)**")
            logs = db.get_recent_logs(limit=10)
            st.dataframe(logs, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()