import streamlit as st
import pandas as pd
import database as db
from usa_agent import USASanctionsAgent
from research_agent import SanctionsResearchAgent 

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Entity Background Check Bot | INTEL OPS",
    page_icon="::", # Minimal text icon
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DEFENSE / CYBER THEME CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');

    /* GLOBAL THEME OVERRIDES */
    .stApp {
        background-color: #0b1121; /* Darker Navy/Black */
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* REMOVE STREAMLIT DEFAULT PADDING */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, h4, .stMarkdown, p {
        color: #e2e8f0 !important;
    }
    
    h1 {
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: -1px;
        border-left: 5px solid #3b82f6;
        padding-left: 15px;
        margin-bottom: 0px;
    }
    
    .stSubheader {
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8 !important;
        font-size: 0.85em !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 1px solid #334155;
        padding-bottom: 5px;
        margin-top: 20px;
    }

    /* CUSTOM ALERTS (To replace st.success/warning with no emojis) */
    .alert-box {
        padding: 12px 15px;
        border-radius: 0px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9em;
        margin-bottom: 10px;
        border-left: 4px solid;
    }
    .alert-info { background: #1e293b; border-color: #3b82f6; color: #bfdbfe; }
    .alert-success { background: #064e3b; border-color: #10b981; color: #d1fae5; }
    .alert-warning { background: #451a03; border-color: #f59e0b; color: #fef3c7; }
    .alert-error { background: #450a0a; border-color: #ef4444; color: #fee2e2; }

    /* INPUT FIELDS - MILITARY STYLE */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #172033 !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        font-family: 'JetBrains Mono', monospace;
        border-radius: 0px !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    
    /* ACTION BUTTONS */
    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 0px; /* Square corners */
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 1px;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
        border: 1px solid #60a5fa;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8;
        border-color: #93c5fd;
    }

    /* THREAT LEVEL INDICATORS */
    .risk-badge {
        font-family: 'JetBrains Mono', monospace;
        padding: 4px 12px;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.8em;
        display: inline-block;
        border: 1px solid;
    }
    .safe { background: rgba(16, 185, 129, 0.1); color: #34d399; border-color: #059669; }
    .low  { background: rgba(234, 179, 8, 0.1); color: #facc15; border-color: #a16207; }
    .mid  { background: rgba(249, 115, 22, 0.1); color: #fb923c; border-color: #c2410c; }
    .high { background: rgba(239, 68, 68, 0.1); color: #f87171; border-color: #dc2626; }
    .very-high { background: rgba(153, 27, 27, 0.2); color: #fca5a5; border-color: #991b1b; font-weight: 900; }

    /* THREAT BADGE BUTTON STYLING */
    .threat-badge-wrapper button {
        font-family: 'JetBrains Mono', monospace !important;
        padding: 4px 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        font-size: 0.8em !important;
        border: 1px solid !important;
        border-radius: 0px !important;
        width: 100% !important;
        text-align: left !important;
        cursor: pointer !important;
        transition: opacity 0.2s !important;
        letter-spacing: 0.5px !important;
    }

    .threat-badge-wrapper button:hover {
        opacity: 0.85 !important;
    }

    /* Apply risk level colors to button */
    .threat-badge-wrapper.safe button {
        background: rgba(16, 185, 129, 0.1) !important;
        color: #34d399 !important;
        border-color: #059669 !important;
    }
    .threat-badge-wrapper.low button {
        background: rgba(234, 179, 8, 0.1) !important;
        color: #facc15 !important;
        border-color: #a16207 !important;
    }
    .threat-badge-wrapper.mid button {
        background: rgba(249, 115, 22, 0.1) !important;
        color: #fb923c !important;
        border-color: #c2410c !important;
    }
    .threat-badge-wrapper.high button {
        background: rgba(239, 68, 68, 0.1) !important;
        color: #f87171 !important;
        border-color: #dc2626 !important;
    }
    .threat-badge-wrapper.very-high button {
        background: rgba(153, 27, 27, 0.2) !important;
        color: #fca5a5 !important;
        border-color: #991b1b !important;
        font-weight: 900 !important;
    }

    /* Threat details dropdown box */
    .threat-details-box {
        background: #1e293b;
        color: #e2e8f0;
        padding: 12px 16px;
        margin-top: 8px;
        border: 1px solid #475569;
        border-radius: 4px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85em;
        line-height: 1.5;
        border-left: 4px solid #3b82f6;
        animation: slideDown 0.2s ease-out;
    }

    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* INTEL CARDS */
    .intel-card {
        background-color: #172033;
        border: 1px solid #334155;
        padding: 15px;
        margin-bottom: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85em;
    }
    .intel-card-header {
        display: flex;
        justify-content: space-between;
        border-bottom: 1px solid #334155;
        padding-bottom: 8px;
        margin-bottom: 8px;
        color: #94a3b8;
    }
    .intel-card h4 {
        color: #f1f5f9 !important;
        margin: 0;
        font-size: 1.1em;
        font-weight: 700;
    }
    .intel-card a {
        color: #60a5fa !important;
        text-decoration: none;
    }
    
    /* DATAFRAME OVERRIDE */
    div[data-testid="stDataFrame"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8em;
    }
    
    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

def main():
    db.init_db()

    # Initialize session state for search persistence
    if 'current_search_id' not in st.session_state:
        st.session_state.current_search_id = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    # --- HEADER ---
    c_head1, c_head2 = st.columns([12, 2])
    with c_head1:
        st.markdown("<h1>Background Check Research Agent<span style='color:#3b82f6; opacity: 0.5'>//</span> ENTITY INTELLIGENCE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-family: JetBrains Mono; color: #64748b; font-size: 0.8em; margin-top: 5px; margin-left: 20px;'>:: SYSTEM READY :: OFFICIAL USE ONLY :: V 2.0.0</p>", unsafe_allow_html=True)
    with c_head2:
        # Minimal status indicator instead of emoji
        st.markdown("<div style='text-align: right; font-family: JetBrains Mono; color: #10b981; font-size: 0.8em; border: 1px solid #10b981; padding: 4px;'>ONLINE</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- DATABASE MANAGEMENT PANEL ---
    with st.expander("🗄️ DATABASE MANAGEMENT"):
        st.markdown("### External Sources Management")
        st.markdown("Manage entities from DOD Section 1260H and FCC Covered List.")

        # Show current database stats
        col_stats1, col_stats2, col_stats3 = st.columns(3)

        entity_counts = db.get_local_entity_count()

        with col_stats1:
            st.metric("DOD Section 1260H", entity_counts.get('DOD_1260H', 0))
        with col_stats2:
            st.metric("FCC Covered List", entity_counts.get('FCC_COVERED', 0))
        with col_stats3:
            st.metric("Total Local Entities", entity_counts.get('TOTAL', 0))

        st.markdown("---")

        # Refresh buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("🔄 Refresh DOD List", use_container_width=True):
                with st.spinner("Loading DOD entities from PDF..."):
                    import subprocess
                    result = subprocess.run(
                        ["python3", "load_external_sources.py", "--dod", "--refresh"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        st.success(f"✓ DOD list refreshed successfully")
                        st.code(result.stdout, language="text")
                        st.rerun()
                    else:
                        st.error(f"✗ Failed to refresh DOD list")
                        st.code(result.stderr, language="text")

        with col_btn2:
            if st.button("🔄 Refresh FCC List", use_container_width=True):
                with st.spinner("Loading FCC entities from web..."):
                    import subprocess
                    result = subprocess.run(
                        ["python3", "load_external_sources.py", "--fcc", "--refresh"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        st.success(f"✓ FCC list refreshed successfully")
                        st.code(result.stdout, language="text")
                        st.rerun()
                    else:
                        st.error(f"✗ Failed to refresh FCC list")
                        st.code(result.stderr, language="text")

        with col_btn3:
            if st.button("🔄 Refresh All", use_container_width=True):
                with st.spinner("Loading all external sources..."):
                    import subprocess
                    result = subprocess.run(
                        ["python3", "load_external_sources.py", "--all", "--refresh"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        st.success(f"✓ All lists refreshed successfully")
                        st.code(result.stdout, language="text")
                        st.rerun()
                    else:
                        st.error(f"✗ Failed to refresh lists")
                        st.code(result.stderr, language="text")

        st.markdown("---")
        st.markdown("**Note:** Refresh operations will clear existing data and reload from source files/URLs.")

    st.markdown("---")

    # --- CONTROL PANEL ---
    st.subheader("01 // SEARCH PARAMS")
    
    # Use a container with a custom border look
    with st.container():
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        with c1:
            name_input = st.text_input("ENTITY NAME", placeholder="INPUT ENTITY NAME")
        with c2:
            country_input = st.selectbox("COUNTRY OF ORIGIN", ["GLOBAL", "CN", "RU", "IR", "NK", "US"])
        with c3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Spacer alignment
            fuzzy = st.toggle("FUZZY LOGIC", value=True)
            conglomerate = st.toggle("CONGLOMERATE SEARCH", value=False)

            # Show depth selector and sister companies option when conglomerate search is enabled
            if conglomerate:
                depth = st.selectbox("SEARCH DEPTH", [1, 2, 3], index=0,
                                   help="1 = Direct subsidiaries only, 2 = Subsidiaries + their children, 3 = Three levels deep")
                include_sisters = st.checkbox("INCLUDE SISTER COMPANIES", value=True,
                                            help="Also search for companies with the same parent (sister companies)")
            else:
                depth = 1  # Default when disabled
                include_sisters = False
        with c4:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                run_btn = st.button("EXECUTE QUERY", use_container_width=True)
            with col_btn2:
                if st.session_state.analysis_complete:
                    if st.button("🗑️", use_container_width=True, help="Clear results"):
                        # Clear all session state
                        st.session_state.analysis_complete = False
                        st.session_state.current_search_id = None
                        if 'threat_expanded' in st.session_state:
                            st.session_state.threat_expanded = False
                        # Clear cache
                        fetch_analysis_data.clear()
                        st.rerun()

    if run_btn and name_input:
        # Store search parameters
        st.session_state.search_name = name_input
        st.session_state.search_country = country_input
        st.session_state.search_fuzzy = fuzzy
        st.session_state.search_conglomerate = conglomerate
        st.session_state.search_depth = depth if conglomerate else 1
        st.session_state.include_sisters = include_sisters if conglomerate else False

        # If conglomerate search, show subsidiary selection interface first
        if conglomerate:
            st.session_state.show_subsidiary_selection = True
            st.session_state.analysis_complete = False
        else:
            st.session_state.analysis_complete = True

    # Display subsidiary selection interface if needed
    if st.session_state.get('show_subsidiary_selection', False):
        display_subsidiary_selection(
            st.session_state.search_name,
            st.session_state.search_depth
        )

    # Display results if analysis has been run
    if st.session_state.analysis_complete:
        if st.session_state.get('search_conglomerate', False):
            run_conglomerate_analysis(
                st.session_state.search_name,
                st.session_state.selected_subsidiaries,
                st.session_state.search_country,
                st.session_state.search_fuzzy
            )
        else:
            run_analysis(
                st.session_state.search_name,
                st.session_state.search_country,
                st.session_state.search_fuzzy
            )

@st.cache_data(show_spinner=False)
def fetch_analysis_data(name_input, country_input, fuzzy):
    """Fetch all data from APIs - this is cached to avoid re-fetching"""
    us_agent = USASanctionsAgent()
    research_agent = SanctionsResearchAgent()

    # Translation if needed
    final_query_name = name_input
    if not name_input.isascii():
        final_query_name = research_agent.translate_name(name_input)

    # Database search
    us_params = {
        "name": final_query_name,
        "countries": "" if country_input == "GLOBAL" else country_input,
        "fuzzy_name": "true" if fuzzy else "false",
        "size": 100
    }
    us_results = us_agent.search(us_params, query_name=final_query_name)

    # OSINT
    official_media = research_agent.get_sanction_news(final_query_name)
    general_media = research_agent.get_general_media(final_query_name)
    media_hits = official_media + general_media

    # Generate report
    report = research_agent.generate_intelligence_report(final_query_name)
    pdf_bytes = research_agent.export_report_to_pdf(final_query_name, report)

    return {
        'final_query_name': final_query_name,
        'us_results': us_results,
        'media_hits': media_hits,
        'report': report,
        'pdf_bytes': pdf_bytes
    }

def display_subsidiary_selection(parent_company, depth):
    """
    Display interface for users to select which subsidiaries and sister companies to search.
    """
    st.markdown("---")
    st.subheader("02 // SUBSIDIARY SELECTION")

    # Initialize session state for related companies if not exists
    if 'related_companies_found' not in st.session_state:
        # Create progress log container
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔍 Search Progress")
            progress_log = st.empty()

        # Initialize log messages list
        log_messages = []

        # Define callback function for progress updates
        def progress_callback(message, level):
            # Add emoji based on level
            emoji_map = {
                'SEARCH': '🔎',
                'INFO': 'ℹ️',
                'SUCCESS': '✅',
                'WARN': '⚠️',
                'ERROR': '❌'
            }
            emoji = emoji_map.get(level, '•')

            # Add message to list
            log_messages.append(f"{emoji} {message}")

            # Display all messages in the log container
            log_html = "<div style='background: #1e293b; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.85em; max-height: 300px; overflow-y: auto;'>"
            for msg in log_messages:
                log_html += f"<div style='margin: 5px 0; color: #e2e8f0;'>{msg}</div>"
            log_html += "</div>"
            progress_log.markdown(log_html, unsafe_allow_html=True)

        # Perform search with progress callback
        with st.spinner(f"Searching for related companies of {parent_company}..."):
            research_agent = SanctionsResearchAgent()
            include_sisters = st.session_state.get('include_sisters', False)
            results = research_agent.find_subsidiaries(parent_company, depth, include_sisters, progress_callback)
            st.session_state.related_companies_found = results

        # Show final completion message
        progress_callback("✨ Search complete!", "SUCCESS")

    results = st.session_state.related_companies_found
    subsidiaries = results.get('subsidiaries', [])
    sisters = results.get('sisters', [])
    method = results.get('method', 'unknown')

    # Combine for display
    all_companies = subsidiaries + sisters

    if not all_companies:
        st.warning(f"No subsidiaries or sister companies found for {parent_company}. Proceeding with parent company search only.")
        st.session_state.selected_subsidiaries = []
        st.session_state.show_subsidiary_selection = False
        st.session_state.analysis_complete = True
        st.rerun()
        return

    # Display count with method info
    method_labels = {
        'api': 'OpenCorporates API',
        'sec_edgar': 'SEC EDGAR (10-K Filings)',
        'sec_edgar+duckduckgo': 'SEC EDGAR + DuckDuckGo',
        'duckduckgo': 'DuckDuckGo Search'
    }
    method_label = method_labels.get(method, 'Unknown')

    # Get source URL and filing date if available
    source_url = results.get('source_url')
    filing_date = results.get('filing_date')

    # Build the info box HTML
    info_html = f"""
    <div class='alert-box alert-info'>
        Found {len(subsidiaries)} subsidiaries and {len(sisters)} sister companies for {parent_company}<br>
        <span style='font-size: 0.85em;'>Search Method: {method_label}</span>
    """

    # Add source link if available (SEC EDGAR)
    if source_url:
        info_html += f"""<br>
        <span style='font-size: 0.85em;'>
            📋 <a href="{source_url}" target="_blank" style="color: #3b82f6; text-decoration: underline;">View Original SEC Exhibit 21</a>
            {f' (Filed: {filing_date})' if filing_date else ''}
        </span>
        """

    info_html += "</div>"

    st.markdown(info_html, unsafe_allow_html=True)

    # Select/Deselect All buttons
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        if st.button("SELECT ALL", use_container_width=True):
            st.session_state.selected_sub_indices = list(range(len(all_companies)))
            st.rerun()
    with col2:
        if st.button("CLEAR ALL", use_container_width=True):
            st.session_state.selected_sub_indices = []
            st.rerun()

    # Initialize selected indices
    if 'selected_sub_indices' not in st.session_state:
        st.session_state.selected_sub_indices = []

    # Display related companies with checkboxes
    st.markdown("### Select companies to search:")

    # Display subsidiaries grouped by level
    if subsidiaries:
        for level in sorted(set(s['level'] for s in subsidiaries)):
            level_subs = [s for s in subsidiaries if s['level'] == level]
            with st.expander(f"🏢 Level {level} Subsidiaries ({len(level_subs)})", expanded=(level==1)):
                for idx, sub in enumerate(level_subs):
                    actual_idx = all_companies.index(sub)
                    # Create unique key using level and position
                    unique_key = f"sub_L{level}_{idx}_{actual_idx}"
                    col_check, col_info = st.columns([1, 11])
                    with col_check:
                        is_selected = actual_idx in st.session_state.selected_sub_indices
                        if st.checkbox(f"Select {sub['name']}", value=is_selected, key=unique_key, label_visibility="collapsed"):
                            if actual_idx not in st.session_state.selected_sub_indices:
                                st.session_state.selected_sub_indices.append(actual_idx)
                        else:
                            if actual_idx in st.session_state.selected_sub_indices:
                                st.session_state.selected_sub_indices.remove(actual_idx)
                    with col_info:
                        status_color = "#10b981" if sub['status'].lower() == 'active' else "#64748b"

                        # Get source and create badge
                        source = sub.get('source', 'unknown')
                        source_labels = {
                            'sec_edgar': '📋 SEC EDGAR',
                            'opencorporates_api': '🌐 OpenCorporates API',
                            'duckduckgo': '🔍 DuckDuckGo'
                        }
                        source_colors = {
                            'sec_edgar': '#10b981',
                            'opencorporates_api': '#3b82f6',
                            'duckduckgo': '#94a3b8'
                        }
                        source_label = source_labels.get(source, '❓ Unknown')
                        source_color = source_colors.get(source, '#64748b')

                        st.markdown(f"""
                        <div style='padding: 8px; background: #172033; border-left: 3px solid {status_color}; margin-bottom: 5px;'>
                            <strong style='color: #e2e8f0;'>{sub['name']}</strong>
                            <span style='background: {source_color}; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{source_label}</span><br>
                            <span style='color: #94a3b8; font-size: 0.85em;'>
                                📍 {sub['jurisdiction']} | Level: {sub.get('level', 1)} | Status: {sub['status']}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

    # Display sister companies
    if sisters:
        with st.expander(f"🤝 Sister Companies ({len(sisters)})", expanded=True):
            for idx, sister in enumerate(sisters):
                actual_idx = all_companies.index(sister)
                # Create unique key using sister prefix and both indices
                unique_key = f"sister_{idx}_{actual_idx}"
                col_check, col_info = st.columns([1, 11])
                with col_check:
                    is_selected = actual_idx in st.session_state.selected_sub_indices
                    if st.checkbox(f"Select {sister['name']}", value=is_selected, key=unique_key, label_visibility="collapsed"):
                        if actual_idx not in st.session_state.selected_sub_indices:
                            st.session_state.selected_sub_indices.append(actual_idx)
                    else:
                        if actual_idx in st.session_state.selected_sub_indices:
                            st.session_state.selected_sub_indices.remove(actual_idx)
                with col_info:
                    status_color = "#3b82f6"  # Blue for sister companies

                    # Get source and create badge
                    source = sister.get('source', 'unknown')
                    source_labels = {
                        'sec_edgar': '📋 SEC EDGAR',
                        'opencorporates_api': '🌐 OpenCorporates API',
                        'duckduckgo': '🔍 DuckDuckGo'
                    }
                    source_colors = {
                        'sec_edgar': '#10b981',
                        'opencorporates_api': '#3b82f6',
                        'duckduckgo': '#94a3b8'
                    }
                    source_label = source_labels.get(source, '❓ Unknown')
                    source_color = source_colors.get(source, '#64748b')

                    st.markdown(f"""
                    <div style='padding: 8px; background: #172033; border-left: 3px solid {status_color}; margin-bottom: 5px;'>
                        <strong style='color: #e2e8f0;'>{sister['name']}</strong>
                        <span style='background: {source_color}; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{source_label}</span><br>
                        <span style='color: #94a3b8; font-size: 0.85em;'>
                            📍 {sister['jurisdiction']} | Relationship: Sister Company | Status: {sister['status']}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    # Proceed button
    st.markdown("---")
    col1, col2, col3 = st.columns([3, 3, 6])
    with col1:
        if st.button("PROCEED WITH SEARCH", use_container_width=True, type="primary"):
            selected_companies = [all_companies[i] for i in st.session_state.selected_sub_indices]
            st.session_state.selected_subsidiaries = selected_companies
            st.session_state.show_subsidiary_selection = False
            st.session_state.analysis_complete = True
            st.rerun()
    with col2:
        if st.button("CANCEL", use_container_width=True):
            # Reset and go back to search form
            st.session_state.show_subsidiary_selection = False
            st.session_state.analysis_complete = False
            if 'related_companies_found' in st.session_state:
                del st.session_state.related_companies_found
            st.rerun()

def run_analysis(name_input, country_input, fuzzy):
    """Display analysis results - fetches from cache if available"""
    # Fetch data (cached - won't re-fetch on button clicks)
    data = fetch_analysis_data(name_input, country_input, fuzzy)

    final_query_name = data['final_query_name']
    us_results = data['us_results']
    media_hits = data['media_hits']
    report = data['report']
    pdf_bytes = data['pdf_bytes']

    # Initialize
    analysis_id = pd.Timestamp.now().strftime('%Y%m%d-%H%M%S')

    st.markdown("---")
    st.subheader("02 // THINKING PROCESS LOGS")

    # Custom Log Container
    log_container = st.empty()

    def log(message, status="INFO"):
        colors = {"INFO": "#94a3b8", "WARN": "#fb923c", "CRIT": "#f87171", "OK": "#34d399"}
        log_container.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.8em; color: {colors[status]};'>[{pd.Timestamp.now().strftime('%H:%M:%S')}] :: {message}</div>", unsafe_allow_html=True)

    # Show processing logs
    if final_query_name != name_input:
        log(f"SCRIPT DETECTED. TRANSLATED: **{final_query_name}**", "INFO")

    match_exists = us_results and 'error' not in us_results[0]
    match_count = len(us_results) if match_exists else 0

    if match_exists:
        log(f"DATABASE HIT: {match_count} RECORDS IDENTIFIED.", "CRIT")
    else:
        log("DATABASE SCAN COMPLETE. NO DIRECT MATCHES.", "OK")

    media_count = len(media_hits)

    # Count official sources specifically
    official_count = len([hit for hit in media_hits if hit.get('source_type') == 'official'])

    log(f"INTELLIGENCE GATHERED: {media_count} RELEVANT SIGNALS ({official_count} OFFICIAL).",
        "INFO" if media_count > 0 else "WARN")

    # --- THREAT CALCULATION ---
    # Use combined_score instead of API score for more granular threat assessment
    max_score = 0
    if match_exists:
        scores = [float(r.get('combined_score', r.get('Score', 0))) for r in us_results if r.get('combined_score') or r.get('Score')]
        max_score = max(scores) if scores else 0

    # Determine match type with granular thresholds
    has_exact_match = match_exists and max_score >= 92
    has_high_match = match_exists and 80 <= max_score < 92
    has_medium_match = match_exists and 65 <= max_score < 80
    has_low_match = match_exists and max_score < 65

    # New 5-level classification system with granular fuzzy matching
    if not match_exists:
        # No database matches at all
        risk_level = "SAFE"
        risk_class = "safe"
    elif has_low_match:
        # Weak match, likely false positive
        risk_level = "LOW"
        risk_class = "low"
    elif has_medium_match:
        # Moderate match, requires investigation
        risk_level = "LOW"
        risk_class = "low"
    elif has_high_match:
        # Strong fuzzy match
        if media_count <= 1:
            risk_level = "MID"
            risk_class = "mid"
        elif official_count > 3:
            risk_level = "VERY HIGH"
            risk_class = "very-high"
        else:
            risk_level = "HIGH"
            risk_class = "high"
    elif has_exact_match:
        # High confidence exact match
        if media_count <= 1:
            risk_level = "MID"
            risk_class = "mid"
        elif official_count > 3:
            risk_level = "VERY HIGH"
            risk_class = "very-high"
        else:
            risk_level = "HIGH"
            risk_class = "high"
    else:
        # Fallback (shouldn't happen)
        risk_level = "LOW"
        risk_class = "low"

    # Define threat level descriptions for tooltips
    threat_descriptions = {
        "SAFE": "No matches found in sanctions databases. Entity appears clear of federal restrictions.",
        "LOW": f"Weak or fuzzy database match (score: {max_score:.0f}). Likely false positive or unrelated entity. Manual verification recommended.",
        "MID": f"Exact database match found (score: {max_score:.0f}) with minimal media coverage ({media_count} source{'s' if media_count != 1 else ''}). Entity is on sanctions list but has low public profile.",
        "HIGH": f"Exact database match (score: {max_score:.0f}) with significant media coverage ({media_count} sources, {official_count} official). Entity is actively sanctioned with public documentation.",
        "VERY HIGH": f"Exact database match (score: {max_score:.0f}) with extensive media coverage ({media_count} sources, {official_count} official government sources). Major sanctioned entity with widespread enforcement."
    }

    tooltip_text = threat_descriptions.get(risk_level, "Classification in progress.")

    # Log to DB
    db.log_analysis_run(analysis_id, name_input, final_query_name, match_count, risk_level)

    # --- REPORT DASHBOARD ---
    st.markdown("---")
    st.subheader(f"03 // SEARCH RESULTS [{analysis_id}]")
    
    # STATUS BAR
    c_stat1, c_stat2, c_stat3 = st.columns([2, 4, 2])
    with c_stat1:
        # Initialize session state for threat dropdown
        if 'threat_expanded' not in st.session_state:
            st.session_state.threat_expanded = False

        # Add custom CSS class wrapper for the button
        st.markdown(f'<div class="threat-badge-wrapper {risk_class}">', unsafe_allow_html=True)

        # Clickable threat badge with icon
        arrow = "▲" if st.session_state.threat_expanded else "▼"
        if st.button(f"THREAT: {risk_level}  {arrow}", key="threat_badge", use_container_width=True):
            st.session_state.threat_expanded = not st.session_state.threat_expanded

        st.markdown('</div>', unsafe_allow_html=True)

        # Show details if expanded
        if st.session_state.threat_expanded:
            st.markdown(f"""
            <div class="threat-details-box">
                {tooltip_text}
            </div>
            """, unsafe_allow_html=True)
    with c_stat2:
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.9em; color: #94a3b8; padding-top: 5px;'>SUBJECT: {final_query_name.upper()}</div>", unsafe_allow_html=True)
    with c_stat3:
        st.markdown(f"<div style='text-align: right; font-family: JetBrains Mono; font-size: 0.9em; color: #64748b; padding-top: 5px;'>CONFIDENCE: {'HIGH' if match_count > 0 else 'STANDARD'}</div>", unsafe_allow_html=True)

    # TABS
    tab1, tab2, tab3 = st.tabs(["[1] ENTITY LIST", "[2] INFO SUMMARY", "[3] NEWS REPORT"])
    
    # TAB 1: DB RECORDS
    with tab1:
        if match_exists:
            for row in us_results:
                # Determine match quality badge color
                match_quality = row.get('match_quality', 'MEDIUM')
                if match_quality == 'EXACT':
                    badge_color = '#10b981'  # Green
                    badge_icon = '✓'
                elif match_quality == 'HIGH':
                    badge_color = '#3b82f6'  # Blue
                    badge_icon = '⚡'
                elif match_quality == 'MEDIUM':
                    badge_color = '#f59e0b'  # Yellow
                    badge_icon = '⚠'
                else:  # LOW
                    badge_color = '#64748b'  # Gray
                    badge_icon = '?'

                # Get scores
                api_score = row.get('api_score', row.get('Score', 'N/A'))
                local_score = row.get('local_score', 'N/A')
                combined_score = row.get('combined_score', api_score)

                # Get similarity breakdown
                breakdown = row.get('similarity_breakdown', {})
                has_breakdown = bool(breakdown)

                # Determine source display name
                source_list = row.get('List', 'Unknown')
                if source_list == 'DOD_1260H':
                    source_display = "DOD Section 1260H (Chinese Military Companies)"
                    source_badge = "🎖️ DOD"
                elif source_list == 'FCC_COVERED':
                    source_display = "FCC Covered List (Secure Networks Act)"
                    source_badge = "📡 FCC"
                else:
                    source_display = "USA Consolidated Screening List"
                    source_badge = "🇺🇸 USA API"

                # Build optional API reference text
                api_reference_html = ""
                if api_score is not None:
                    api_reference_html = f"&nbsp;|&nbsp; <span style='color: #94a3b8;'>API Reference: {api_score}</span>"

                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span>{source_badge} SOURCE: {source_display}</span>
                        <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">
                            {badge_icon} {match_quality}
                        </span>
                    </div>
                    <h4>{row.get('Name')}</h4>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #cbd5e1;">
                        TYPE: {row.get('Type')} // LOC: {row.get('Address')}
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #e2e8f0;">
                        <strong>MATCH SCORE:</strong> {combined_score}{api_reference_html}
                    </div>
                    <div style="margin-top: 10px; background: rgba(0,0,0,0.2); padding: 8px; font-style: italic; color: #94a3b8;">
                        NOTES: {row.get('Remark')}
                    </div>
                    <div style="margin-top: 10px; text-align: right;">
                        <a href="{row.get('Link')}" target="_blank">>> VIEW SOURCE DOCUMENT</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Show expandable similarity breakdown if available
                if has_breakdown:
                    with st.expander("📊 View Detailed Similarity Breakdown"):
                        st.markdown(f"""
                        **How this match was scored:**

                        This system uses **local-only scoring** for uniform match quality across all sources.
                        - **Match Score** ({combined_score}): Weighted average of 5 fuzzy matching algorithms
                        {f"- **API Score** ({api_score}): Shown for reference only (not used in scoring)" if api_score else "- **Source**: Local database entity (no API score)"}

                        **Local Algorithm Breakdown:**
                        """)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Token Set Ratio", f"{breakdown.get('token_set', 0):.1f}",
                                     help="Ignores extra words, focuses on shared tokens")
                            st.metric("Jaro-Winkler", f"{breakdown.get('jaro_winkler', 0):.1f}",
                                     help="Name matching with prefix bonus")
                            st.metric("Levenshtein", f"{breakdown.get('levenshtein', 0):.1f}",
                                     help="Edit distance (character-level)")
                        with col2:
                            st.metric("Token Sort", f"{breakdown.get('token_sort', 0):.1f}",
                                     help="Handles word order variations")
                            st.metric("Phonetic Match", f"{breakdown.get('phonetic', 0):.1f}",
                                     help="Pronunciation-based matching")

                        st.markdown(f"""
                        **Scoring Formula:**
                        ```
                        Match Score = (Token Set × 30%) + (Jaro-Winkler × 25%) +
                                     (Levenshtein × 20%) + (Token Sort × 15%) +
                                     (Phonetic × 10%)

                        = ({breakdown.get('token_set', 0):.1f} × 0.30) + ({breakdown.get('jaro_winkler', 0):.1f} × 0.25) +
                          ({breakdown.get('levenshtein', 0):.1f} × 0.20) + ({breakdown.get('token_sort', 0):.1f} × 0.15) +
                          ({breakdown.get('phonetic', 0):.1f} × 0.10)

                        = {combined_score}
                        ```

                        **Match Quality Thresholds (Local-Only Scoring):**
                        - EXACT: ≥ 95 (Very high confidence)
                        - HIGH: 85-94 (Strong fuzzy match)
                        - MEDIUM: 70-84 (Moderate match, investigate)
                        - LOW: < 70 (Weak match, likely false positive)

                        See `SCORING_SYSTEM.md` for full documentation.
                        """)
        else:
            st.markdown(f"""
            <div class="alert-box alert-success">
                [SYSTEM] NO MATCHES FOUND IN CONSOLIDATED SCREENING LIST.<br>
                Subject appears clear of federal sanctions at this time.
            </div>
            """, unsafe_allow_html=True)

    # TAB 2: AI REPORT
    with tab2:
        # Disclaimer banner
        st.markdown("""
        <div class="alert-box alert-warning">
            <strong>⚠ DISCLAIMER:</strong> The information provided in this report is generated by AI and compiled from various sources.
            Users are required to conduct their own due diligence checks and verify all information independently.
            Please review and validate all references cited before making any decisions.
        </div>
        """, unsafe_allow_html=True)

        # Report and PDF are already generated in cached data
        c_rep, c_dl = st.columns([5, 1])
        with c_rep:
            st.markdown(report)
        with c_dl:
            st.download_button("DOWNLOAD PDF", pdf_bytes, f"{final_query_name}_INTEL.pdf", "application/pdf", use_container_width=True)

    # TAB 3: MEDIA
    with tab3:
        # Disclaimer banner
        st.markdown("""
        <div class="alert-box alert-warning">
            <strong>⚠ DISCLAIMER:</strong> News articles and media reports are provided for reference only.
            Users must perform independent verification of all sources and information presented.
            Cross-reference with official government sources and conduct your own due diligence before acting on this information.
        </div>
        """, unsafe_allow_html=True)

        if media_count > 0:
            for hit in media_hits:
                # Determine source type and badge style
                source_type = hit.get('source_type', 'general')
                if source_type == 'official':
                    badge_color = '#10b981'  # Green for official
                    badge_text = 'OFFICIAL GOV SOURCE'
                else:
                    badge_color = '#60a5fa'  # Blue for general
                    badge_text = 'GENERAL MEDIA'

                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span style="color: {badge_color}; font-weight: 700;">[{badge_text}]</span>
                        <span style="color: #f59e0b;">RELEVANCE VERIFIED</span>
                    </div>
                    <h4>{hit['title']}</h4>
                    <div style="margin-top: 5px; color: #94a3b8;">LINK: <a href="{hit['url']}" target="_blank">{hit['url']}</a></div>
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px dashed #334155;">
                        ANALYSIS: {hit.get('relevance', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
             st.markdown(f"""
            <div class="alert-box alert-info">
                [SYSTEM] NO VERIFIED ADVERSE MEDIA DETECTED.<br>
                Standard cross-reference complete.
            </div>
            """, unsafe_allow_html=True)

    # --- FOOTER ---
    st.markdown("---")

    with st.expander("📜 SEARCH HISTORY"):
        if st.button("REFRESH LOGS"):
            st.dataframe(db.get_analysis_history(20), use_container_width=True, hide_index=True)
        else:
            st.dataframe(db.get_analysis_history(5), use_container_width=True, hide_index=True)

def display_entity_results(entity_name, data, country_input, fuzzy):
    """
    Display results for a single entity (reusable for both single and conglomerate searches).
    This is extracted from run_analysis() for code reuse.
    """
    final_query_name = data['final_query_name']
    us_results = data['us_results']
    media_hits = data['media_hits']
    report = data['report']
    pdf_bytes = data['pdf_bytes']

    # Threat calculation (same as run_analysis)
    match_exists = us_results and 'error' not in us_results[0]
    match_count = len(us_results) if match_exists else 0
    media_count = len(media_hits)
    official_count = len([hit for hit in media_hits if hit.get('source_type') == 'official'])

    max_score = 0
    if match_exists:
        scores = [float(r.get('combined_score', r.get('Score', 0))) for r in us_results if r.get('combined_score') or r.get('Score')]
        max_score = max(scores) if scores else 0

    has_exact_match = match_exists and max_score >= 92
    has_high_match = match_exists and 80 <= max_score < 92
    has_medium_match = match_exists and 65 <= max_score < 80
    has_low_match = match_exists and max_score < 65

    # Risk level calculation
    if not match_exists:
        risk_level = "SAFE"
        risk_class = "safe"
    elif has_low_match:
        risk_level = "LOW"
        risk_class = "low"
    elif has_medium_match:
        risk_level = "LOW"
        risk_class = "low"
    elif has_high_match:
        if media_count <= 1:
            risk_level = "MID"
            risk_class = "mid"
        elif official_count > 3:
            risk_level = "VERY HIGH"
            risk_class = "very-high"
        else:
            risk_level = "HIGH"
            risk_class = "high"
    elif has_exact_match:
        if media_count <= 1:
            risk_level = "MID"
            risk_class = "mid"
        elif official_count > 3:
            risk_level = "VERY HIGH"
            risk_class = "very-high"
        else:
            risk_level = "HIGH"
            risk_class = "high"
    else:
        risk_level = "LOW"
        risk_class = "low"

    # STATUS BAR
    c_stat1, c_stat2, c_stat3 = st.columns([2, 4, 2])
    with c_stat1:
        st.markdown(f'<div class="threat-badge-wrapper {risk_class}"><div class="risk-badge {risk_class}">THREAT: {risk_level}</div></div>', unsafe_allow_html=True)
    with c_stat2:
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.9em; color: #94a3b8; padding-top: 5px;'>SUBJECT: {final_query_name.upper()}</div>", unsafe_allow_html=True)
    with c_stat3:
        st.markdown(f"<div style='text-align: right; font-family: JetBrains Mono; font-size: 0.9em; color: #64748b; padding-top: 5px;'>MATCHES: {match_count}</div>", unsafe_allow_html=True)

    # TABS (same as run_analysis but simplified)
    tab1, tab2, tab3 = st.tabs(["[1] ENTITY LIST", "[2] INFO SUMMARY", "[3] NEWS REPORT"])

    with tab1:
        if match_exists:
            for row in us_results:
                match_quality = row.get('match_quality', 'MEDIUM')
                if match_quality == 'EXACT':
                    badge_color = '#10b981'
                    badge_icon = '✓'
                elif match_quality == 'HIGH':
                    badge_color = '#3b82f6'
                    badge_icon = '⚡'
                elif match_quality == 'MEDIUM':
                    badge_color = '#f59e0b'
                    badge_icon = '⚠'
                else:
                    badge_color = '#64748b'
                    badge_icon = '?'

                source_list = row.get('List', 'Unknown')
                if source_list == 'DOD_1260H':
                    source_display = "DOD Section 1260H"
                    source_badge = "🎖️ DOD"
                elif source_list == 'FCC_COVERED':
                    source_display = "FCC Covered List"
                    source_badge = "📡 FCC"
                else:
                    source_display = "USA Consolidated Screening List"
                    source_badge = "🇺🇸 USA API"

                combined_score = row.get('combined_score', row.get('Score', 'N/A'))

                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span>{source_badge} SOURCE: {source_display}</span>
                        <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">
                            {badge_icon} {match_quality}
                        </span>
                    </div>
                    <h4>{row.get('Name')}</h4>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #cbd5e1;">
                        TYPE: {row.get('Type')} // LOC: {row.get('Address')}
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #e2e8f0;">
                        <strong>MATCH SCORE:</strong> {combined_score}
                    </div>
                    <div style="margin-top: 10px; text-align: right;">
                        <a href="{row.get('Link')}" target="_blank">>> VIEW SOURCE</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-success">[SYSTEM] NO MATCHES FOUND</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown(report)

    with tab3:
        if media_count > 0:
            for hit in media_hits:
                source_type = hit.get('source_type', 'general')
                badge_color = '#10b981' if source_type == 'official' else '#60a5fa'
                badge_text = 'OFFICIAL GOV SOURCE' if source_type == 'official' else 'GENERAL MEDIA'

                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span style="color: {badge_color}; font-weight: 700;">[{badge_text}]</span>
                    </div>
                    <h4>{hit['title']}</h4>
                    <div style="margin-top: 5px; color: #94a3b8;">LINK: <a href="{hit['url']}" target="_blank">{hit['url']}</a></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-info">[SYSTEM] NO MEDIA DETECTED</div>', unsafe_allow_html=True)

def run_conglomerate_analysis(parent_company, selected_subsidiaries, country_input, fuzzy):
    """
    Run analysis for parent company and all selected subsidiaries.
    Display results in grouped format.
    """
    import time

    st.markdown("---")
    st.subheader("02 // THINKING PROCESS LOGS")

    # Log container
    log_container = st.empty()

    def log(message, status="INFO"):
        colors = {"INFO": "#94a3b8", "WARN": "#fb923c", "CRIT": "#f87171", "OK": "#34d399"}
        log_container.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.8em; color: {colors[status]};'>[{pd.Timestamp.now().strftime('%H:%M:%S')}] :: {message}</div>", unsafe_allow_html=True)

    # Initialize
    analysis_id = pd.Timestamp.now().strftime('%Y%m%d-%H%M%S')

    # Prepare entity list (parent + subsidiaries + sisters)
    entities_to_search = [{'name': parent_company, 'type': 'PARENT', 'level': 0}]
    for sub in selected_subsidiaries:
        entities_to_search.append({
            'name': sub['name'],
            'type': 'SUBSIDIARY',
            'level': sub.get('level', 1),
            'jurisdiction': sub.get('jurisdiction', 'Unknown'),
            'relationship': sub.get('relationship', 'subsidiary')
        })

    log(f"CONGLOMERATE SEARCH MODE ACTIVATED. ENTITIES TO SEARCH: {len(entities_to_search)}", "INFO")

    # Search each entity
    all_entity_results = []

    progress_bar = st.progress(0)
    for idx, entity in enumerate(entities_to_search):
        log(f"SEARCHING: {entity['name']} ({entity['type']})", "INFO")

        # Fetch analysis data for this entity
        data = fetch_analysis_data(entity['name'], country_input, fuzzy)

        # Store results
        all_entity_results.append({
            'entity': entity,
            'data': data
        })

        # Update progress
        progress_bar.progress((idx + 1) / len(entities_to_search))
        time.sleep(0.1)  # Brief pause for UI update

    progress_bar.empty()
    log(f"SEARCH COMPLETE. ANALYZED {len(entities_to_search)} ENTITIES.", "OK")

    # Calculate overall threat
    total_matches = sum(len(r['data']['us_results']) for r in all_entity_results if r['data']['us_results'] and 'error' not in r['data']['us_results'][0])

    log(f"TOTAL DATABASE MATCHES ACROSS ALL ENTITIES: {total_matches}", "CRIT" if total_matches > 0 else "OK")

    # Display results
    st.markdown("---")
    st.subheader(f"03 // CONGLOMERATE SEARCH RESULTS [{analysis_id}]")

    # Overall summary
    st.markdown(f"""
    <div style='background: #172033; border: 1px solid #334155; padding: 15px; margin-bottom: 20px;'>
        <h4 style='color: #e2e8f0; margin: 0;'>SEARCH SUMMARY</h4>
        <div style='color: #94a3b8; margin-top: 10px;'>
            Parent Company: <strong style='color: #3b82f6;'>{parent_company}</strong><br>
            Subsidiaries Checked: <strong style='color: #3b82f6;'>{len(selected_subsidiaries)}</strong><br>
            Total Entities Searched: <strong style='color: #3b82f6;'>{len(entities_to_search)}</strong><br>
            Total Database Matches: <strong style='color: {"#f87171" if total_matches > 0 else "#34d399"};'>{total_matches}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display each entity's results
    for result in all_entity_results:
        entity = result['entity']
        data = result['data']

        # Determine if this entity has matches
        has_matches = len(data['us_results']) > 0 and 'error' not in data['us_results'][0]
        match_count = len(data['us_results']) if has_matches else 0

        # Color code based on entity type and matches
        border_color = "#f87171" if has_matches else "#10b981"
        if entity['type'] == 'PARENT':
            entity_label = "🏢 PARENT"
        elif entity.get('relationship') == 'sister':
            entity_label = "🤝 SISTER COMPANY"
        else:
            entity_label = f"🔗 SUBSIDIARY (L{entity['level']})"

        with st.expander(f"{entity_label}: {entity['name']} - {match_count} matches", expanded=(match_count > 0)):
            # Display results using same format as run_analysis
            display_entity_results(entity['name'], data, country_input, fuzzy)

    # Log to database
    db.log_analysis_run(
        analysis_id,
        f"[CONGLOMERATE] {parent_company}",
        parent_company,
        total_matches,
        "CONGLOMERATE_SEARCH"
    )

if __name__ == "__main__":
    main()