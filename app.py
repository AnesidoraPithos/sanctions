import streamlit as st
import pandas as pd
import database as db
from usa_agent import USASanctionsAgent
from research_agent import SanctionsResearchAgent 

# --- CONFIGURATION ---
st.set_page_config(
    page_title="SENTINEL | INTEL OPS",
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
    
    # --- HEADER ---
    c_head1, c_head2 = st.columns([12, 2])
    with c_head1:
        st.markdown("<h1>SENTINEL <span style='color:#3b82f6; opacity: 0.5'>//</span> ENTITY INTELLIGENCE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-family: JetBrains Mono; color: #64748b; font-size: 0.8em; margin-top: 5px; margin-left: 20px;'>:: SYSTEM READY :: OFFICIAL USE ONLY :: V 1.0.0</p>", unsafe_allow_html=True)
    with c_head2:
        # Minimal status indicator instead of emoji
        st.markdown("<div style='text-align: right; font-family: JetBrains Mono; color: #10b981; font-size: 0.8em; border: 1px solid #10b981; padding: 4px;'>ONLINE</div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- CONTROL PANEL ---
    st.subheader("01 // TARGET PARAMETERS")
    
    # Use a container with a custom border look
    with st.container():
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        with c1:
            name_input = st.text_input("SUBJECT IDENTIFIER", placeholder="INPUT ENTITY NAME")
        with c2:
            country_input = st.selectbox("JURISDICTION", ["GLOBAL", "CN", "RU", "IR", "NK", "US"])
        with c3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # Spacer alignment
            fuzzy = st.toggle("FUZZY LOGIC", value=True)
        with c4:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            run_btn = st.button("EXECUTE QUERY", use_container_width=True)

    if run_btn and name_input:
        run_analysis(name_input, country_input, fuzzy)

def run_analysis(name_input, country_input, fuzzy):
    # Initialize
    analysis_id = pd.Timestamp.now().strftime('%Y%m%d-%H%M%S')
    us_agent = USASanctionsAgent()
    research_agent = SanctionsResearchAgent()
    
    final_query_name = name_input
    
    st.markdown("---")
    st.subheader("02 // PROCESS LOG")
    
    # Custom Log Container
    log_container = st.empty()
    
    def log(message, status="INFO"):
        colors = {"INFO": "#94a3b8", "WARN": "#fb923c", "CRIT": "#f87171", "OK": "#34d399"}
        log_container.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.8em; color: {colors[status]};'>[{pd.Timestamp.now().strftime('%H:%M:%S')}] :: {message}</div>", unsafe_allow_html=True)

    final_query_name = name_input
    
    # --- PHASE 1: LINGUISTIC PROCESSING ---
    if not name_input.isascii():
        with st.status("🔄 DECRYPTING // TRANSLATING...", expanded=True) as status:
            # CALL THE AGENT
            translated = research_agent.translate_name(name_input)
            
            # UPDATE THE QUERY VARIABLE
            final_query_name = translated 
            
            status.write(f"SCRIPT DETECTED. TRANSLATED: **{final_query_name}**")
            status.update(label="PRE-PROCESSING COMPLETE", state="complete", expanded=False)

    # --- PHASE 2: DATABASE SCAN ---
    with st.spinner(f"🔍 SCANNING FEDERAL DATABASES FOR '{final_query_name}'..."):
        # CRITICAL: Ensure we use 'final_query_name', NOT 'name_input'
        us_params = {
            "name": final_query_name, 
            "countries": "" if country_input == "GLOBAL" else country_input, 
            "fuzzy_name": "true" if fuzzy else "false", 
            "size": 100
        }
        us_results = us_agent.search(us_params)
    
    match_exists = us_results and 'error' not in us_results[0]
    match_count = len(us_results) if match_exists else 0
    
    if match_exists:
        log(f"DATABASE HIT: {match_count} RECORDS IDENTIFIED.", "CRIT")
    else:
        log("DATABASE SCAN COMPLETE. NO DIRECT MATCHES.", "OK")

    # --- PHASE 3: OSINT ---
    log("INITIALIZING OPEN SOURCE INTELLIGENCE SWEEP...", "INFO")
    media_hits = research_agent.get_sanction_news(final_query_name)
    media_count = len(media_hits)
    log(f"INTELLIGENCE GATHERED: {media_count} RELEVANT SIGNALS.", "INFO" if media_count > 0 else "WARN")

    # --- THREAT CALCULATION ---
    max_score = 0
    if match_exists:
        scores = [float(r.get('Score', 0)) for r in us_results if r.get('Score')]
        max_score = max(scores) if scores else 0

    if match_count == 0:
        risk_level = "SAFE"
        risk_class = "safe"
    elif max_score < 100:
        risk_level = "LOW"
        risk_class = "low"
    elif max_score >= 100 and media_count < 2:
        risk_level = "MID"
        risk_class = "mid"
    else:
        risk_level = "HIGH"
        risk_class = "high"

    # Log to DB
    db.log_analysis_run(analysis_id, name_input, final_query_name, match_count, risk_level)

    # --- REPORT DASHBOARD ---
    st.markdown("---")
    st.subheader(f"03 // INTELLIGENCE DOSSIER [{analysis_id}]")
    
    # STATUS BAR
    c_stat1, c_stat2, c_stat3 = st.columns([2, 4, 2])
    with c_stat1:
        st.markdown(f'<div class="risk-badge {risk_class}">THREAT: {risk_level}</div>', unsafe_allow_html=True)
    with c_stat2:
        st.markdown(f"<div style='font-family: JetBrains Mono; font-size: 0.9em; color: #94a3b8; padding-top: 5px;'>SUBJECT: {final_query_name.upper()}</div>", unsafe_allow_html=True)
    with c_stat3:
        st.markdown(f"<div style='text-align: right; font-family: JetBrains Mono; font-size: 0.9em; color: #64748b; padding-top: 5px;'>CONFIDENCE: {'HIGH' if match_count > 0 else 'STANDARD'}</div>", unsafe_allow_html=True)

    # TABS
    tab1, tab2, tab3 = st.tabs(["[1] FEDERAL REGISTRY", "[2] TACTICAL SUMMARY", "[3] SIGNALS INTEL"])
    
    # TAB 1: DB RECORDS
    with tab1:
        if match_exists:
            for row in us_results:
                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span>SOURCE: {row.get('List')}</span>
                        <span>SCORE: {row.get('Score')}</span>
                    </div>
                    <h4>{row.get('Name')}</h4>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #cbd5e1;">TYPE: {row.get('Type')} // LOC: {row.get('Address')}</div>
                    <div style="margin-top: 10px; background: rgba(0,0,0,0.2); padding: 8px; font-style: italic; color: #94a3b8;">
                        NOTES: {row.get('Remark')}
                    </div>
                    <div style="margin-top: 10px; text-align: right;">
                        <a href="{row.get('Link')}" target="_blank">>> VIEW SOURCE DOCUMENT</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-box alert-success">
                [SYSTEM] NO MATCHES FOUND IN CONSOLIDATED SCREENING LIST.<br>
                Subject appears clear of federal sanctions at this time.
            </div>
            """, unsafe_allow_html=True)

    # TAB 2: AI REPORT
    with tab2:
        with st.spinner("COMPILING TACTICAL REPORT..."):
            report = research_agent.generate_intelligence_report(final_query_name)
            
            c_rep, c_dl = st.columns([5, 1])
            with c_rep:
                st.markdown(report)
            with c_dl:
                pdf_bytes = research_agent.export_report_to_pdf(final_query_name, report)
                st.download_button("DOWNLOAD PDF", pdf_bytes, f"{final_query_name}_INTEL.pdf", "application/pdf", use_container_width=True)

    # TAB 3: MEDIA
    with tab3:
        if media_count > 0:
            for hit in media_hits:
                st.markdown(f"""
                <div class="intel-card">
                    <div class="intel-card-header">
                        <span>SIGNAL DETECTED</span>
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
    with st.expander("OPERATIONS ARCHIVE"):
        if st.button("REFRESH LOGS"):
            st.dataframe(db.get_analysis_history(20), use_container_width=True, hide_index=True)
        else:
            st.dataframe(db.get_analysis_history(5), use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()