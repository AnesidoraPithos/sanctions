import streamlit as st
import pandas as pd
import database as db
from usa_agent import USASanctionsAgent
from research_agent import SanctionsResearchAgent
import graph_builder as gb
import visualizations as viz
import visualizations_advanced as viz_adv
import visualization_selector as viz_selector
import streamlit.components.v1 as components
import serialization_utils as serializer
import export_utils as exporter 

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

def escape_markdown_for_display(text):
    """
    Escape problematic characters in markdown text to prevent formatting issues.
    Specifically handles dollar signs that trigger LaTeX math mode in Streamlit.

    Args:
        text (str): Raw markdown text

    Returns:
        str: Escaped text safe for st.markdown() display
    """
    if not text:
        return text

    # Escape dollar signs to prevent LaTeX/math mode rendering
    # Use double backslash in replacement because markdown processes it
    text = text.replace('$', r'\$')

    return text


def display_search_history():
    """Display enhanced search history with restore, delete, and export functionality"""
    st.markdown("### Search History & Restore")

    # Initialize session state for bulk selection
    if 'selected_searches_for_delete' not in st.session_state:
        st.session_state.selected_searches_for_delete = set()

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search_filter = st.text_input("🔍 Filter by entity name", key="history_filter")
    with col2:
        all_tags = db.get_all_tags()
        tag_filter = st.multiselect("🏷️ Filter by tags", all_tags, key="history_tag_filter")
    with col3:
        sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Risk Level", "Entity Name"], key="history_sort")

    # Get filtered searches
    filters = {}
    if search_filter:
        filters['entity_name'] = search_filter
    if tag_filter:
        filters['tags'] = tag_filter

    searches_df = db.get_saved_searches(limit=50, filters=filters)

    if searches_df.empty:
        st.info("No saved searches found. Searches will appear here when auto-save is enabled or you manually save a search.")
        return

    # Apply sorting
    if sort_by == "Date (oldest)":
        searches_df = searches_df.sort_values('timestamp', ascending=True)
    elif sort_by == "Risk Level":
        risk_order = {"VERY HIGH": 0, "HIGH": 1, "MID": 2, "LOW": 3, "SAFE": 4}
        searches_df['risk_order'] = searches_df['risk_level'].map(risk_order)
        searches_df = searches_df.sort_values('risk_order')
    elif sort_by == "Entity Name":
        searches_df = searches_df.sort_values('entity_name')

    # Bulk action buttons
    st.markdown("---")
    col_bulk1, col_bulk2, col_bulk3, col_bulk4, col_bulk5 = st.columns([2, 2, 2, 2, 4])

    with col_bulk1:
        if st.button("🗑️ Delete Selected", use_container_width=True, help="Delete all selected searches"):
            if st.session_state.selected_searches_for_delete:
                # Delete all selected searches efficiently
                success_count, total_count = db.delete_multiple_searches(
                    list(st.session_state.selected_searches_for_delete)
                )

                if success_count == total_count:
                    st.success(f"✓ Deleted {success_count} search(es)")
                else:
                    st.warning(f"⚠️ Deleted {success_count} of {total_count} search(es)")

                st.session_state.selected_searches_for_delete = set()
                st.rerun()
            else:
                st.warning("No searches selected")

    with col_bulk2:
        if st.button("Select All", use_container_width=True, help="Select all visible searches"):
            st.session_state.selected_searches_for_delete = set(searches_df['search_id'].tolist())
            st.rerun()

    with col_bulk3:
        if st.button("Clear Selection", use_container_width=True, help="Clear all selections"):
            st.session_state.selected_searches_for_delete = set()
            st.rerun()

    with col_bulk4:
        if st.button("🗑️ Delete All", use_container_width=True, type="secondary", help="Delete ALL saved searches (cannot be undone!)"):
            if 'confirm_delete_all' not in st.session_state:
                st.session_state.confirm_delete_all = True
                st.warning("⚠️ Click again to confirm deletion of ALL searches!")
                st.rerun()
            else:
                # Confirmed - delete all
                deleted_count = db.delete_all_searches()
                st.success(f"✓ Deleted all {deleted_count} search(es)")
                st.session_state.selected_searches_for_delete = set()
                del st.session_state.confirm_delete_all
                st.rerun()

    # Display count and selection info
    selected_count = len(st.session_state.selected_searches_for_delete)
    st.markdown(f"**Showing {len(searches_df)} saved search{'es' if len(searches_df) != 1 else ''}** | Selected for deletion: **{selected_count}**")
    st.markdown("---")

    for idx, search in searches_df.iterrows():
        # Format tags for display
        tags_list = serializer.format_tags_for_display(search['tags'])
        tags_display = ', '.join([f"🏷️ {tag}" for tag in tags_list]) if tags_list else 'No tags'

        # Risk level badge
        risk_colors = {
            "VERY HIGH": "#ef4444",
            "HIGH": "#f97316",
            "MID": "#eab308",
            "LOW": "#3b82f6",
            "SAFE": "#10b981"
        }
        risk_color = risk_colors.get(search['risk_level'], "#64748b")

        # Create expander for each search
        with st.expander(
            f"🔍 {search['entity_name']} | {search['timestamp']} | "
            f"Risk: {search['risk_level']} | Matches: {search['match_count']}"
        ):
            col_info1, col_info2 = st.columns(2)

            with col_info1:
                st.markdown(f"""
                **Entity:** {search['entity_name']}
                **Date:** {search['timestamp']}
                **Risk Level:** <span style='color: {risk_color}; font-weight: bold;'>{search['risk_level']}</span>
                **Match Count:** {search['match_count']}
                **Subsidiaries:** {search['subsidiary_count']} | **Sisters:** {search['sister_count']}
                """, unsafe_allow_html=True)

            with col_info2:
                st.markdown(f"""
                **Country Filter:** {search['country_filter']}
                **Fuzzy Search:** {'Yes' if search['fuzzy_search'] else 'No'}
                **Conglomerate:** {'Yes' if search['is_conglomerate'] else 'No'}
                **Tags:** {tags_display}
                **Auto-saved:** {'Yes' if search['is_auto_saved'] else 'No'}
                """)

            if search['notes']:
                st.markdown(f"**Notes:** {search['notes']}")

            # Selection checkbox
            st.markdown("---")
            is_selected = st.checkbox(
                f"Select for deletion",
                value=search['search_id'] in st.session_state.selected_searches_for_delete,
                key=f"select_{search['search_id']}"
            )

            # Update selection state
            if is_selected:
                st.session_state.selected_searches_for_delete.add(search['search_id'])
            else:
                st.session_state.selected_searches_for_delete.discard(search['search_id'])

            # Action buttons
            col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

            with col_btn1:
                if st.button("📂 Restore", key=f"restore_{search['search_id']}", use_container_width=True):
                    restore_search(search['search_id'])

            with col_btn2:
                if st.button("📤 Export", key=f"export_{search['search_id']}", use_container_width=True):
                    st.session_state[f"show_export_{search['search_id']}"] = True

            with col_btn3:
                if st.button("✏️ Edit", key=f"edit_{search['search_id']}", use_container_width=True):
                    st.session_state[f"show_edit_{search['search_id']}"] = True

            with col_btn4:
                if st.button("🗑️ Delete", key=f"delete_{search['search_id']}", use_container_width=True):
                    if db.delete_saved_search(search['search_id']):
                        # Remove from selection state if selected
                        st.session_state.selected_searches_for_delete.discard(search['search_id'])
                        st.success("Search deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete search")

            # Export options for this search
            if st.session_state.get(f"show_export_{search['search_id']}", False):
                st.markdown("---")
                st.markdown("**Export Options:**")

                # Load full search data
                saved_search = db.load_search_results(search['search_id'])
                if saved_search:
                    export_data = {
                        'search_id': search['search_id'],
                        'timestamp': saved_search['timestamp'],
                        'entity_name': saved_search['entity_name'],
                        'risk_level': saved_search['risk_level'],
                        'match_count': saved_search['match_count'],
                        'subsidiary_count': saved_search['subsidiary_count'],
                        'sister_count': saved_search['sister_count'],
                        'country_filter': saved_search['country_filter'],
                        'fuzzy_search': saved_search['fuzzy_search'],
                        'notes': saved_search['notes'],
                        'results': serializer.deserialize_search_results(saved_search)
                    }

                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        exporter.create_download_button_json(search['search_id'], export_data, saved_search['entity_name'])
                    with col_e2:
                        exporter.create_download_button_excel(search['search_id'], export_data, saved_search['entity_name'])
                    with col_e3:
                        exporter.create_download_button_pdf(search['search_id'], export_data, saved_search['entity_name'])

            # Edit metadata form
            if st.session_state.get(f"show_edit_{search['search_id']}", False):
                st.markdown("---")
                with st.form(f"edit_form_{search['search_id']}"):
                    new_notes = st.text_area("Notes", value=search['notes'] or '', key=f"notes_{search['search_id']}")
                    current_tags = ', '.join(serializer.format_tags_for_display(search['tags']))
                    new_tags = st.text_input("Tags (comma-separated)", value=current_tags, key=f"tags_{search['search_id']}")

                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        if st.form_submit_button("Save Changes", use_container_width=True):
                            tags_json = serializer.parse_tags(new_tags)
                            if db.update_search_metadata(search['search_id'], notes=new_notes, tags=tags_json):
                                st.success("Metadata updated")
                                st.session_state[f"show_edit_{search['search_id']}"] = False
                                st.rerun()
                    with col_s2:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            st.session_state[f"show_edit_{search['search_id']}"] = False
                            st.rerun()


def restore_search(search_id):
    """
    Restore a saved search into the current session.
    This loads all search results from the database without re-running API calls.
    """
    # Load search from database
    saved_search = db.load_search_results(search_id)

    if not saved_search:
        st.error("Failed to load search")
        return

    # Deserialize results
    results = serializer.deserialize_search_results(saved_search)

    # Store in session state
    st.session_state.showing_restored_search = True
    st.session_state.restored_search_id = search_id
    st.session_state.restored_entity_name = saved_search['entity_name']
    st.session_state.restored_results = results
    st.session_state.restored_params = {
        'country': saved_search['country_filter'],
        'fuzzy': bool(saved_search['fuzzy_search']),
        'conglomerate': bool(saved_search['is_conglomerate']),
        'reverse_search': bool(saved_search['is_reverse_search'])
    }

    # Store conglomerate data if available
    if results.get('conglomerate_data'):
        st.session_state.related_companies_found = results['conglomerate_data']

    st.success(f"✓ Restored search for: {saved_search['entity_name']}")
    st.rerun()

def main():
    db.init_db()

    # Initialize session state for search persistence
    if 'current_search_id' not in st.session_state:
        st.session_state.current_search_id = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    # Initialize session state for save/restore functionality
    if 'auto_save_enabled' not in st.session_state:
        st.session_state.auto_save_enabled = True
    if 'showing_restored_search' not in st.session_state:
        st.session_state.showing_restored_search = False
    if 'restored_search_id' not in st.session_state:
        st.session_state.restored_search_id = None
    if 'restored_results' not in st.session_state:
        st.session_state.restored_results = None
    if 'show_save_dialog' not in st.session_state:
        st.session_state.show_save_dialog = False

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

    # --- SETTINGS PANEL ---
    with st.expander("⚙️ SETTINGS"):
        st.markdown("### Search Settings")

        col_set1, col_set2 = st.columns(2)

        with col_set1:
            auto_save = st.checkbox(
                "Auto-save all searches",
                value=st.session_state.auto_save_enabled,
                help="Automatically save every search for future reference and restore"
            )
            st.session_state.auto_save_enabled = auto_save

            if auto_save:
                st.markdown("<div class='alert-box alert-success'>✓ All searches will be automatically saved</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='alert-box alert-warning'>⚠ Manual save required for each search</div>", unsafe_allow_html=True)

        with col_set2:
            # Show storage stats
            saved_count = len(db.get_saved_searches(limit=1000))
            st.metric("Saved Searches", saved_count)

            if st.button("View Search History"):
                st.session_state.show_history = True

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

            # Initialize reverse_search (will be set later)
            reverse_search = False

            # Show depth selector and sister companies option when conglomerate search is enabled
            if conglomerate:
                depth = st.selectbox("SEARCH DEPTH", [1, 2, 3], index=0,
                                   help="1 = Direct subsidiaries only, 2 = Subsidiaries + their children, 3 = Three levels deep")

                # Option to select which subsidiaries to search at depth 2/3
                if depth >= 2:
                    st.info(f"""
**📊 Depth {depth} Search:**
- You'll be able to select which subsidiaries to search at level {depth}
- Progress tracking will show which subsidiary is currently being processed
- Each subsidiary search takes 5-10 seconds
                    """)

                # Ownership threshold filter
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                ownership_filter = st.selectbox(
                    "OWNERSHIP THRESHOLD",
                    ["All subsidiaries", "Wholly-owned (100%)", "Majority (>50%)", "Custom threshold"],
                    index=0,
                    help="Filter subsidiaries by ownership percentage"
                )

                if ownership_filter == "Custom threshold":
                    ownership_threshold = st.slider(
                        "Minimum ownership %",
                        min_value=0,
                        max_value=100,
                        value=51,
                        step=1,
                        help="Only include subsidiaries with at least this ownership percentage"
                    )
                elif ownership_filter == "Wholly-owned (100%)":
                    ownership_threshold = 100
                elif ownership_filter == "Majority (>50%)":
                    ownership_threshold = 51
                else:
                    ownership_threshold = 0  # All subsidiaries

                # Sister companies not applicable when searching parent company
                include_sisters = False
                reverse_search = False
            else:
                depth = 1  # Default when disabled
                ownership_threshold = 0

                # Reverse search: Find parent and sister companies
                reverse_search = st.checkbox("SEARCH FOR PARENT & SISTERS", value=False,
                                            help="Enable if searching for a subsidiary company. Will find its parent company and sister companies (other subsidiaries of the same parent)")

                # Show visual confirmation when enabled
                if reverse_search:
                    st.info("🔄 **Reverse Search Mode**: Will search for parent company and sister companies")

                # Sister companies only available when NOT in conglomerate mode and reverse search is disabled
                # (entity could be a subsidiary with sister companies)
                if not reverse_search:
                    include_sisters = st.checkbox("INCLUDE SISTER COMPANIES", value=False,
                                            help="Search for other companies owned by the same parent company (sister companies)")
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
        st.session_state.include_sisters = include_sisters if (not conglomerate and not reverse_search) else False
        st.session_state.ownership_threshold = ownership_threshold if conglomerate else 0
        st.session_state.reverse_search = reverse_search if not conglomerate else False

        # Reset depth search state on new search
        st.session_state.depth_search_stage = 'initial'
        st.session_state.selected_depth_subsidiaries = []
        st.session_state.requested_depth = depth if conglomerate else 1

        # Clear previous related companies results
        if 'related_companies_found' in st.session_state:
            del st.session_state.related_companies_found

        # If conglomerate search OR reverse search, show subsidiary selection interface first
        if conglomerate or reverse_search:
            st.session_state.show_subsidiary_selection = True
            st.session_state.analysis_complete = False
            # Debug logging
            if reverse_search:
                print(f"[DEBUG] Reverse search enabled for: {name_input}")
        else:
            st.session_state.analysis_complete = True

    # Check if we're displaying a restored search
    if st.session_state.get('showing_restored_search', False):
        st.markdown("---")
        st.markdown("<div class='alert-box alert-info'>📂 Displaying Restored Search - No API calls were made</div>", unsafe_allow_html=True)

        # Display restored results
        restored_results = st.session_state.restored_results
        restored_params = st.session_state.restored_params
        entity_name = st.session_state.restored_entity_name

        # Create a fake "data" object that matches the structure expected by run_analysis
        # Since run_analysis expects fetch_analysis_data format
        # We'll call display_entity_results directly with the restored data

        data = {
            'final_query_name': entity_name,
            'us_results': restored_results.get('us_results', []),
            'media_hits': restored_results.get('media_hits', []),
            'report': restored_results.get('report', ''),
            'pdf_bytes': restored_results.get('pdf_bytes')
        }

        # Determine if this is a conglomerate search based on stored data
        conglom_data = restored_results.get('conglomerate_data')
        if conglom_data:
            # Check if this is a reverse search
            is_reverse_search = conglom_data.get('is_reverse_search', False)

            if is_reverse_search:
                # In reverse search, subsidiaries[0] contains the parent info
                # Sisters contains the actual sister companies
                # The searched entity should be treated as a subsidiary along with sisters
                subsidiaries_data = conglom_data.get('subsidiaries', [])
                parent_name = subsidiaries_data[0]['name'] if subsidiaries_data else entity_name

                # All companies (searched entity + sisters) should be subsidiaries of parent
                all_subsidiaries = []

                # Add the searched entity as a subsidiary
                all_subsidiaries.append({
                    'name': entity_name,
                    'jurisdiction': 'Unknown',
                    'status': 'Active',
                    'level': 1,
                    'is_searched_entity': True
                })

                # Add all sister companies as subsidiaries too
                for sister in conglom_data.get('sisters', []):
                    all_subsidiaries.append(sister)

                conglomerate_context = {
                    'parent': parent_name,
                    'subsidiaries': all_subsidiaries,
                    'sisters': []  # Empty since they're all subsidiaries now
                }
            else:
                # Normal conglomerate search
                conglomerate_context = {
                    'parent': entity_name,
                    'subsidiaries': conglom_data.get('subsidiaries', []),
                    'sisters': conglom_data.get('sisters', [])
                }

            display_entity_results(
                entity_name,
                data,
                restored_params.get('country', 'GLOBAL'),
                restored_params.get('fuzzy', True),
                conglomerate_context=conglomerate_context
            )
        else:
            # Single entity search
            display_entity_results(
                entity_name,
                data,
                restored_params.get('country', 'GLOBAL'),
                restored_params.get('fuzzy', True)
            )

        # Add button to clear restored search
        if st.button("🔄 Start New Search", use_container_width=False):
            st.session_state.showing_restored_search = False
            st.session_state.restored_search_id = None
            st.session_state.restored_results = None
            st.session_state.restored_entity_name = None
            if 'related_companies_found' in st.session_state:
                del st.session_state.related_companies_found
            st.rerun()

    # Display subsidiary selection interface if needed
    elif st.session_state.get('show_subsidiary_selection', False):
        display_subsidiary_selection(
            st.session_state.search_name,
            st.session_state.search_depth
        )

    # Display results if analysis has been run
    elif st.session_state.analysis_complete:
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
    Supports both normal conglomerate search (parent → subsidiaries) and reverse search (subsidiary → parent → sisters).
    """
    st.markdown("---")

    # Check if this is a reverse search
    reverse_search = st.session_state.get('reverse_search', False)

    # Debug logging
    print(f"[DEBUG] display_subsidiary_selection called")
    print(f"[DEBUG] reverse_search = {reverse_search}")
    print(f"[DEBUG] parent_company = {parent_company}")

    if reverse_search:
        st.subheader("02 // PARENT & SISTER COMPANIES")
    else:
        st.subheader("02 // SUBSIDIARY SELECTION")

    # Initialize depth search session state
    if 'depth_search_stage' not in st.session_state:
        st.session_state.depth_search_stage = 'initial'
    if 'selected_depth_subsidiaries' not in st.session_state:
        st.session_state.selected_depth_subsidiaries = []
    if 'requested_depth' not in st.session_state:
        st.session_state.requested_depth = depth

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

        # Check if this is a reverse search (subsidiary → parent → sisters)
        reverse_search_enabled = st.session_state.get('reverse_search', False)

        # Debug logging
        print(f"[DEBUG] Inside search block")
        print(f"[DEBUG] reverse_search_enabled = {reverse_search_enabled}")
        print(f"[DEBUG] parent_company = {parent_company}")

        # Determine actual search depth based on stage
        # If depth >= 2 and this is initial search, start with depth 1 only
        if depth >= 2 and st.session_state.depth_search_stage == 'initial':
            actual_depth = 1
            st.session_state.requested_depth = depth
            st.session_state.depth_search_stage = 'selecting'
            progress_callback(f"📊 Starting depth 1 search (depth {depth} will be performed on selected subsidiaries)", "INFO")
        else:
            actual_depth = depth

        # Get selected subsidiaries for depth search if applicable
        depth_search_subs = st.session_state.get('selected_depth_subsidiaries', None) if actual_depth >= 2 else None

        # Perform search with progress callback
        research_agent = SanctionsResearchAgent()

        # Check if this is a reverse search (subsidiary → parent → sisters)
        if reverse_search_enabled:
            print(f"[DEBUG] About to call find_parent_and_sisters for: {parent_company}")
            with st.spinner(f"Searching for parent and sister companies of {parent_company}..."):
                print(f"[DEBUG] Inside spinner, calling find_parent_and_sisters...")
                reverse_results = research_agent.find_parent_and_sisters(
                    parent_company,
                    progress_callback
                )
                print(f"[DEBUG] find_parent_and_sisters returned: {reverse_results.keys() if reverse_results else 'None'}")

                # Transform reverse search results to match expected format
                parent_info = reverse_results.get('parent')
                sisters = reverse_results.get('sisters', [])

                # Add parent as a "subsidiary" for display purposes (will be shown differently)
                subsidiaries = []
                if parent_info:
                    subsidiaries.append({
                        'name': parent_info['name'],
                        'jurisdiction': parent_info.get('jurisdiction', 'Unknown'),
                        'status': parent_info.get('status', 'Unknown'),
                        'relationship': 'parent',
                        'level': 0,
                        'source': parent_info.get('source', 'unknown')
                    })

                results = {
                    'subsidiaries': subsidiaries,
                    'sisters': sisters,
                    'method': reverse_results.get('method', 'unknown'),
                    'source_url': None,
                    'filing_date': None,
                    'is_reverse_search': True
                }
                st.session_state.related_companies_found = results
        else:
            with st.spinner(f"Searching for related companies of {parent_company}..."):
                include_sisters = st.session_state.get('include_sisters', False)
                ownership_threshold = st.session_state.get('ownership_threshold', 0)
                results = research_agent.find_subsidiaries(
                    parent_company,
                    actual_depth,
                    include_sisters,
                    progress_callback,
                    ownership_threshold,
                    depth_search_subsidiaries=depth_search_subs
                )
                st.session_state.related_companies_found = results

        # Show final completion message
        progress_callback("✨ Search complete!", "SUCCESS")

    results = st.session_state.related_companies_found
    subsidiaries = results.get('subsidiaries', [])
    sisters = results.get('sisters', [])
    method = results.get('method', 'unknown')
    is_reverse_search = results.get('is_reverse_search', False)

    # Method labels for display
    method_labels = {
        'opencorporates_api': 'OpenCorporates API',
        'api': 'OpenCorporates API',
        'sec_edgar': 'SEC EDGAR (10-K Filings)',
        'sec_edgar_10k': 'SEC EDGAR (10-K - US Company)',
        'sec_edgar_20f': 'SEC EDGAR (20-F - Foreign Issuer)',
        'sec_edgar+duckduckgo': 'SEC EDGAR + DuckDuckGo',
        'sec_edgar_10k+duckduckgo': 'SEC EDGAR (10-K) + DuckDuckGo',
        'sec_edgar_20f+duckduckgo': 'SEC EDGAR (20-F) + DuckDuckGo',
        'wikipedia+duckduckgo': 'Wikipedia + DuckDuckGo',
        'duckduckgo': 'DuckDuckGo Search'
    }

    # Handle reverse search display differently
    if is_reverse_search:
        # For reverse search: subsidiaries[0] is the parent, sisters are actual sisters
        parent_company_info = subsidiaries[0] if subsidiaries else None

        if parent_company_info:
            # Display parent company info prominently
            st.markdown(f"""
            <div class='alert-box alert-success'>
                <strong>🏢 Parent Company Found:</strong> {parent_company_info['name']}<br>
                <span style='font-size: 0.85em;'>📍 Jurisdiction: {parent_company_info.get('jurisdiction', 'Unknown')} | Status: {parent_company_info.get('status', 'Unknown')}</span>
            </div>
            """, unsafe_allow_html=True)

        if not sisters:
            st.warning(f"Found parent company but no sister companies for {parent_company}.")
            st.info("Proceeding with parent company and searched subsidiary only.")
            # Add both parent and searched subsidiary
            st.session_state.selected_subsidiaries = [parent_company_info] if parent_company_info else []
            st.session_state.show_subsidiary_selection = False
            st.session_state.analysis_complete = True
            st.rerun()
            return

        # For reverse search, include parent + sisters in all_companies
        # (parent is in subsidiaries list with level 0)
        all_companies = subsidiaries + sisters

        # Display parent info
        if subsidiaries:
            parent_name = subsidiaries[0]['name']
            parent_country = subsidiaries[0].get('jurisdiction', 'Unknown')
            st.markdown(f"""
            <div class='alert-box alert-success'>
                🏢 <strong>Parent Company Found:</strong> {parent_name}<br>
                📍 {parent_country} | Source: {method_labels.get(method, 'Unknown')}
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='alert-box alert-info'>
            Found {len(sisters)} sister companies of {parent_company}
        </div>
        """, unsafe_allow_html=True)
    else:
        # Normal conglomerate search: combine subsidiaries and sisters
        all_companies = subsidiaries + sisters

        if not all_companies:
            st.warning(f"No subsidiaries or sister companies found for {parent_company}. Proceeding with parent company search only.")
            st.session_state.selected_subsidiaries = []
            st.session_state.show_subsidiary_selection = False
            st.session_state.analysis_complete = True
            st.rerun()
            return

    # Display count with method info (for normal search)
    # Display count with method info (skip for reverse search as already displayed above)
    if not is_reverse_search:
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
                            'wikipedia': '📖 Wikipedia',
                            'duckduckgo': '🔍 DuckDuckGo'
                        }
                        source_colors = {
                            'sec_edgar': '#10b981',
                            'opencorporates_api': '#3b82f6',
                            'wikipedia': '#a855f7',
                            'duckduckgo': '#94a3b8'
                        }
                        source_label = source_labels.get(source, '❓ Unknown')
                        source_color = source_colors.get(source, '#64748b')

                        # Format ownership percentage if available
                        ownership_pct = sub.get('ownership_percentage')
                        ownership_display = ""
                        if ownership_pct is not None:
                            ownership_display = f" | Ownership: {ownership_pct}%"

                        # Format reference URL if available
                        reference_url = sub.get('reference_url')
                        reference_link = ""
                        if reference_url:
                            reference_link = f"<br><span style='font-size: 0.75em;'>🔗 <a href='{reference_url}' target='_blank' style='color: #60a5fa;'>View Source</a></span>"

                        st.markdown(f"""
                        <div style='padding: 8px; background: #172033; border-left: 3px solid {status_color}; margin-bottom: 5px;'>
                            <strong style='color: #e2e8f0;'>{sub['name']}</strong>
                            <span style='background: {source_color}; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{source_label}</span><br>
                            <span style='color: #94a3b8; font-size: 0.85em;'>
                                📍 {sub['jurisdiction']} | Level: {sub.get('level', 1)} | Status: {sub['status']}{ownership_display}
                            </span>{reference_link}
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
                        'wikipedia': '📖 Wikipedia',
                        'duckduckgo': '🔍 DuckDuckGo'
                    }
                    source_colors = {
                        'sec_edgar': '#10b981',
                        'opencorporates_api': '#3b82f6',
                        'wikipedia': '#a855f7',
                        'duckduckgo': '#94a3b8'
                    }
                    source_label = source_labels.get(source, '❓ Unknown')
                    source_color = source_colors.get(source, '#64748b')

                    # Format ownership percentage if available
                    ownership_pct = sister.get('ownership_percentage')
                    ownership_display = ""
                    if ownership_pct is not None:
                        ownership_display = f" | Ownership: {ownership_pct}%"

                    # Format reference URL if available
                    reference_url = sister.get('reference_url')
                    reference_link = ""
                    if reference_url:
                        reference_link = f"<br><span style='font-size: 0.75em;'>🔗 <a href='{reference_url}' target='_blank' style='color: #60a5fa;'>View Source</a></span>"

                    st.markdown(f"""
                    <div style='padding: 8px; background: #172033; border-left: 3px solid {status_color}; margin-bottom: 5px;'>
                        <strong style='color: #e2e8f0;'>{sister['name']}</strong>
                        <span style='background: {source_color}; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{source_label}</span><br>
                        <span style='color: #94a3b8; font-size: 0.85em;'>
                            📍 {sister['jurisdiction']} | Relationship: Sister Company | Status: {sister['status']}{ownership_display}
                        </span>{reference_link}
                    </div>
                    """, unsafe_allow_html=True)

    # Display Financial Intelligence (Directors, Shareholders, Transactions) if available
    directors = results.get('directors', [])
    shareholders = results.get('shareholders', [])
    transactions = results.get('transactions', [])

    # Debug: Show what was found
    total_fin_items = len(directors) + len(shareholders) + len(transactions)

    # Always show the Financial Intelligence section (even if no data)
    st.markdown("---")
    st.markdown(f"### 📊 Financial Intelligence (SEC Filing Data) {f'({total_fin_items} items found)' if total_fin_items > 0 else ''}")

    if directors or shareholders or transactions:
        # Display directors
        if directors:
            with st.expander(f"👥 Directors & Officers ({len(directors)})", expanded=False):
                st.markdown(f"<div class='alert-box alert-info'>Extracted from SEC filings for {parent_company}</div>", unsafe_allow_html=True)
                for director in directors:
                    nationality = director.get('nationality', 'Unknown')
                    other_positions = director.get('other_positions', '')

                    other_positions_html = ""
                    if other_positions and other_positions != 'Unknown':
                        other_positions_html = f"<br><span style='font-size: 0.75em; color: #94a3b8;'>Other Positions: {other_positions}</span>"

                    st.markdown(f"""
                    <div style='padding: 10px; background: #172033; border-left: 3px solid #3b82f6; margin-bottom: 8px;'>
                        <strong style='color: #e2e8f0; font-size: 1.05em;'>{director['name']}</strong><br>
                        <span style='color: #3b82f6; font-size: 0.9em;'>📋 {director['title']}</span><br>
                        <span style='color: #94a3b8; font-size: 0.85em;'>
                            🌍 Nationality: {nationality}
                        </span>{other_positions_html}
                    </div>
                    """, unsafe_allow_html=True)

        # Display major shareholders
        if shareholders:
            with st.expander(f"💼 Major Shareholders ({len(shareholders)})", expanded=False):
                st.markdown(f"<div class='alert-box alert-info'>Major shareholders (5%+ ownership) from SEC filings for {parent_company}</div>", unsafe_allow_html=True)
                for shareholder in shareholders:
                    ownership_pct = shareholder.get('ownership_percentage')
                    shareholder_type = shareholder.get('type', 'Unknown')
                    jurisdiction = shareholder.get('jurisdiction', 'Unknown')

                    ownership_display = f"{ownership_pct}%" if ownership_pct else "Unknown %"
                    type_badge_color = '#10b981' if shareholder_type == 'Corporate' else '#3b82f6' if shareholder_type == 'Institutional' else '#f59e0b'

                    st.markdown(f"""
                    <div style='padding: 10px; background: #172033; border-left: 3px solid {type_badge_color}; margin-bottom: 8px;'>
                        <strong style='color: #e2e8f0; font-size: 1.05em;'>{shareholder['name']}</strong>
                        <span style='background: {type_badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{shareholder_type}</span><br>
                        <span style='color: #10b981; font-size: 1.1em; font-weight: bold;'>Ownership: {ownership_display}</span><br>
                        <span style='color: #94a3b8; font-size: 0.85em;'>
                            🌍 Jurisdiction: {jurisdiction}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

        # Display related party transactions
        if transactions:
            with st.expander(f"💸 Related Party Transactions ({len(transactions)})", expanded=False):
                st.markdown(f"<div class='alert-box alert-warning'>Financial transactions between {parent_company} and related parties</div>", unsafe_allow_html=True)
                for txn in transactions:
                    txn_type = txn.get('transaction_type', 'Unknown')
                    counterparty = txn.get('counterparty', 'Unknown')
                    relationship = txn.get('relationship', 'Unknown')
                    amount = txn.get('amount')
                    currency = txn.get('currency', 'USD')
                    txn_date = txn.get('transaction_date', 'Unknown')
                    purpose = txn.get('purpose', '')

                    # Format amount
                    if amount:
                        amount_display = f"{currency} {amount:,.0f}"
                    else:
                        amount_display = "Amount not disclosed"

                    # Type badge color
                    type_badge_color = '#10b981' if 'Loan' in txn_type else '#3b82f6' if 'Sale' in txn_type else '#f59e0b'

                    purpose_html = ""
                    if purpose and purpose != 'Unknown':
                        purpose_html = f"<br><span style='font-size: 0.75em; color: #94a3b8;'>Purpose: {purpose}</span>"

                    st.markdown(f"""
                    <div style='padding: 10px; background: #172033; border-left: 3px solid {type_badge_color}; margin-bottom: 8px;'>
                        <strong style='color: #e2e8f0; font-size: 1.05em;'>{counterparty}</strong>
                        <span style='background: {type_badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 3px; font-size: 0.7em; margin-left: 8px;'>{txn_type}</span><br>
                        <span style='color: #10b981; font-size: 1.1em; font-weight: bold;'>{amount_display}</span><br>
                        <span style='color: #94a3b8; font-size: 0.85em;'>
                            🔗 Relationship: {relationship} | 📅 Date: {txn_date}
                        </span>{purpose_html}
                    </div>
                    """, unsafe_allow_html=True)

        # Add link to source filing if available
        fin_intel_url = results.get('fin_intel_url')
        if fin_intel_url:
            st.markdown(f"""
            <div style='margin-top: 10px; text-align: right;'>
                <a href="{fin_intel_url}" target="_blank" style="color: #3b82f6; text-decoration: underline; font-size: 0.85em;">
                    📋 View Full SEC Filing (Items 6 & 7 / Proxy Statement)
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        # No financial intelligence data available
        st.markdown("""
        <div class='alert-box alert-info'>
            <strong>ℹ INFO:</strong> No financial intelligence data available for this entity.
            Financial intelligence includes directors, officers, major shareholders (5%+ ownership), and related party transactions from SEC filings (10-K, 20-F, DEF 14A).
            <br><br>
            <strong>Possible reasons:</strong>
            <ul>
                <li>Entity is not publicly traded or doesn't file with SEC</li>
                <li>Entity is foreign and doesn't have U.S. SEC filings</li>
                <li>SEC filing data extraction is still in progress</li>
                <li>Data was filtered out due to quality validation (placeholder names removed)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # === RELATIONSHIP DIAGRAM SECTION ===
    # Build graph from collected data
    if subsidiaries or sisters or directors or shareholders or transactions:
        st.markdown("---")
        st.markdown("### 🔗 Relationship Diagram")

        # Build graph
        with st.spinner("Building relationship network..."):
            # Collect all directors and shareholders from all entities
            all_directors = list(directors) if directors else []
            all_shareholders = list(shareholders) if shareholders else []
            all_transactions = list(transactions) if transactions else []

            # Fetch directors and shareholders for each subsidiary
            all_entity_names = [parent_company]
            if subsidiaries:
                all_entity_names.extend([sub.get('name') for sub in subsidiaries if sub.get('name')])
            if sisters:
                all_entity_names.extend([sis.get('name') for sis in sisters if sis.get('name')])

            for entity_name in all_entity_names:
                if entity_name != parent_company:  # Already have parent data
                    # Fetch from database
                    entity_directors = db.get_directors(company_name=entity_name)
                    entity_shareholders = db.get_shareholders(company_name=entity_name)
                    entity_transactions = db.get_transactions(company_name=entity_name)

                    if entity_directors:
                        all_directors.extend(entity_directors)
                    if entity_shareholders:
                        all_shareholders.extend(entity_shareholders)
                    if entity_transactions:
                        all_transactions.extend(entity_transactions)

            # Check if this is a reverse search
            if is_reverse_search and subsidiaries:
                # For reverse search: subsidiaries[0] is the parent, need to restructure
                actual_parent_name = subsidiaries[0].get('name', parent_company)

                # Create subsidiaries list: searched entity + all sisters
                restructured_subsidiaries = []

                # Add the searched entity (Lazada) as a subsidiary
                restructured_subsidiaries.append({
                    'name': parent_company,
                    'jurisdiction': 'Unknown',
                    'status': 'Active',
                    'level': 1,
                    'is_searched_entity': True
                })

                # Add all sisters as subsidiaries
                for sister in sisters:
                    restructured_subsidiaries.append(sister)

                # Build graph with correct structure
                parent_info = {'jurisdiction': 'Unknown', 'status': 'Active'}
                graph = gb.build_entity_graph(
                    company_name=actual_parent_name,  # Alibaba
                    subsidiaries=restructured_subsidiaries,  # Lazada + sisters
                    sisters=[],  # Empty - all are subsidiaries now
                    directors=all_directors,
                    shareholders=all_shareholders,
                    transactions=all_transactions,
                    parent_info=parent_info
                )
            else:
                # Normal conglomerate search
                parent_info = {'jurisdiction': 'Unknown', 'status': 'Active'}
                graph = gb.build_entity_graph(
                    company_name=parent_company,
                    subsidiaries=subsidiaries,
                    sisters=sisters,
                    directors=all_directors,
                    shareholders=all_shareholders,
                    transactions=all_transactions,
                    parent_info=parent_info
                )

        # Get graph statistics
        stats = gb.get_graph_statistics(graph)

        # Display quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Entities", stats['total_nodes'])
        with col2:
            st.metric("Relationships", stats['total_edges'])
        with col3:
            st.metric("Countries", stats['num_countries'])
        with col4:
            if stats['most_connected']:
                st.metric("Most Connected", stats['most_connected'][:15] + "..." if len(stats['most_connected']) > 15 else stats['most_connected'])

        # Sub-tabs for different visualizations
        viz_tab1, viz_tab2 = st.tabs(["🔗 Network View", "🌍 Geographic View"])

        with viz_tab1:
            # Use the new visualization selector for multiple visualization options
            viz_selector.display_visualization_selector(
                graph=graph,
                parent_company=parent_company,
                key_prefix="subsidiary_preview"
            )

        with viz_tab2:
            st.markdown("<div class='alert-box alert-info'>Geographic distribution of entities showing jurisdictions and cross-border relationships</div>", unsafe_allow_html=True)

            # Filter controls for geographic view
            col1, col2 = st.columns(2)
            with col1:
                show_directors_geo = st.checkbox("Show Directors", value=True, key="show_directors_sub_geo")
            with col2:
                show_shareholders_geo = st.checkbox("Show Shareholders", value=True, key="show_shareholders_sub_geo")

            # Filter graph for geographic view
            filtered_graph_geo = gb.filter_graph(graph, show_directors_geo, show_shareholders_geo, True)

            # Create and display geographic map
            geo_map = viz.create_geographic_map(filtered_graph_geo, title=f"Geographic Distribution: {parent_company}")
            components.html(geo_map._repr_html_(), height=650)

        # Graph Explorer
        with st.expander("📊 EXPLORE GRAPH DATABASE"):
            st.markdown("### Graph Statistics")

            # Display detailed statistics
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                **Network Composition:**
                - Total Nodes: {stats['total_nodes']}
                - Companies: {stats['companies']}
                - People: {stats['people']}
                - Total Relationships: {stats['total_edges']}
                """)
            with col2:
                st.markdown(f"""
                **Geographic Distribution:**
                - Countries Represented: {stats['num_countries']}
                - Countries: {', '.join(stats['countries'][:5])}{'...' if len(stats['countries']) > 5 else ''}
                """)

            st.markdown("---")
            st.markdown("### Relationship Explorer")

            # Entity selector
            node_list = list(graph.nodes())
            if node_list:
                selected_entity = st.selectbox("Select Entity to Explore", node_list, key="entity_explorer_sub")

                if selected_entity:
                    # Get neighbors
                    neighbors = gb.get_neighbors_table(graph, selected_entity)

                    if neighbors:
                        st.markdown(f"**Showing {len(neighbors)} relationships for {selected_entity}:**")

                        # Convert to DataFrame for display
                        df_neighbors = pd.DataFrame(neighbors)
                        st.dataframe(df_neighbors, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"No relationships found for {selected_entity}")

            st.markdown("---")
            st.markdown("### Path Finder")

            # Path finder
            col1, col2 = st.columns(2)
            with col1:
                source_entity = st.selectbox("From Entity", node_list, key="path_source_sub")
            with col2:
                target_entity = st.selectbox("To Entity", node_list, key="path_target_sub")

            if st.button("Find Paths", key="find_paths_sub"):
                if source_entity and target_entity and source_entity != target_entity:
                    paths = gb.find_paths(filtered_graph, source_entity, target_entity, max_paths=5)

                    if paths:
                        st.success(f"Found {len(paths)} path(s) between {source_entity} and {target_entity}:")
                        for i, path in enumerate(paths, 1):
                            path_str = " → ".join(path)
                            st.markdown(f"**Path {i}:** {path_str}")
                    else:
                        st.warning(f"No paths found between {source_entity} and {target_entity}")
                else:
                    st.warning("Please select two different entities")

    # Depth Search Selection Interface (if depth >= 2 and in selection stage)
    if (st.session_state.get('depth_search_stage') == 'selecting' and
        st.session_state.requested_depth >= 2 and
        len(subsidiaries) > 0):

        st.markdown("---")
        st.markdown(f"### 📊 Select Subsidiaries for Depth {st.session_state.requested_depth} Search")

        st.info(f"""
**Depth {st.session_state.requested_depth} Search:**
- Found **{len(subsidiaries)} level 1 subsidiaries**
- Select which ones to search at depth {st.session_state.requested_depth}
- Each subsidiary search takes 5-10 seconds
- Progress tracking will show which subsidiary is being processed
        """)

        # SELECT ALL / CLEAR ALL buttons
        col1, col2, col3 = st.columns([2, 2, 8])
        with col1:
            if st.button("✓ SELECT ALL", key="select_all_depth"):
                st.session_state.selected_depth_subsidiaries = [sub['name'] for sub in subsidiaries]
                st.rerun()
        with col2:
            if st.button("✗ CLEAR ALL", key="clear_all_depth"):
                st.session_state.selected_depth_subsidiaries = []
                st.rerun()

        # Display subsidiaries with checkboxes for depth search
        st.markdown("#### Select Level 1 Subsidiaries:")

        # Use columns for checkbox display
        for sub in subsidiaries:
            sub_name = sub['name']
            is_selected = sub_name in st.session_state.selected_depth_subsidiaries

            col1, col2 = st.columns([1, 20])
            with col1:
                if st.checkbox("", value=is_selected, key=f"depth_select_{sub_name}"):
                    if sub_name not in st.session_state.selected_depth_subsidiaries:
                        st.session_state.selected_depth_subsidiaries.append(sub_name)
                        st.rerun()
                else:
                    if sub_name in st.session_state.selected_depth_subsidiaries:
                        st.session_state.selected_depth_subsidiaries.remove(sub_name)
                        st.rerun()

            with col2:
                # Get source badge
                source = sub.get('source', method)
                source_badges = {
                    'opencorporates_api': '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 500;">🏢 API</span>',
                    'sec_edgar': '<span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 500;">📋 SEC EDGAR</span>',
                    'duckduckgo': '<span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 500;">🔍 DuckDuckGo</span>',
                    'wikipedia': '<span style="background: #a855f7; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 500;">📖 Wikipedia</span>',
                }
                source_badge = source_badges.get(source, '<span style="background: #6b7280; color: white; padding: 2px 8px; border-radius: 3px; font-size: 0.75em; font-weight: 500;">🔍 Web</span>')

                st.markdown(f"""
                <div style='padding: 8px; border-left: 3px solid #3b82f6; margin: 5px 0; background: #1e293b;'>
                    <strong>{sub_name}</strong> {source_badge}<br>
                    <span style='font-size: 0.85em; color: #9ca3af;'>
                        📍 {sub.get('jurisdiction', 'Unknown')} |
                        Level: {sub.get('level', 1)} |
                        Status: {sub.get('status', 'Unknown')}
                    </span>
                </div>
                """, unsafe_allow_html=True)

        # Show selection count and CONTINUE button
        selected_count = len(st.session_state.selected_depth_subsidiaries)
        st.markdown(f"**Selected: {selected_count} subsidiaries**")

        if selected_count > 0:
            estimated_time = selected_count * 7  # 7 seconds per subsidiary average
            estimated_min = max(1, estimated_time // 60)

            st.markdown("---")
            col1, col2, col3 = st.columns([4, 2, 6])
            with col1:
                if st.button(f"🔍 CONTINUE DEPTH {st.session_state.requested_depth} SEARCH", use_container_width=True, type="primary"):
                    st.session_state.depth_search_stage = 'searching'
                    # Clear the related_companies_found to trigger new search with depth
                    if 'related_companies_found' in st.session_state:
                        del st.session_state.related_companies_found
                    st.rerun()
            with col2:
                st.markdown(f"<div style='padding: 10px; text-align: center; color: #9ca3af;'>~{estimated_min} min</div>", unsafe_allow_html=True)
            with col3:
                if st.button("⏭️ SKIP DEPTH SEARCH", use_container_width=True):
                    st.session_state.depth_search_stage = 'complete'
                    st.rerun()
        else:
            st.warning("Please select at least one subsidiary to continue depth search, or click SKIP to proceed without depth search.")
            if st.button("⏭️ SKIP DEPTH SEARCH", use_container_width=True):
                st.session_state.depth_search_stage = 'complete'
                st.rerun()

    # Proceed button (only show if not in depth selection stage)
    if not (st.session_state.get('depth_search_stage') == 'selecting' and st.session_state.requested_depth >= 2):
        st.markdown("---")
        col1, col2, col3 = st.columns([3, 3, 6])
        with col1:
            if st.button("PROCEED WITH SEARCH", use_container_width=True, type="primary"):
                selected_companies = [all_companies[i] for i in st.session_state.selected_sub_indices]
                st.session_state.selected_subsidiaries = selected_companies

                # Store conglomerate structure for relationship diagrams
                if is_reverse_search:
                    # For reverse search: subsidiaries[0] contains parent info
                    parent_name = subsidiaries[0]['name'] if subsidiaries else parent_company
                    st.session_state.conglomerate_structure = {
                        'parent': parent_name,
                        'all_subsidiaries': [],
                        'all_sisters': sisters,
                        'is_reverse': True
                    }
                else:
                    # For normal search: parent_company is the parent
                    st.session_state.conglomerate_structure = {
                        'parent': parent_company,
                        'all_subsidiaries': subsidiaries,
                        'all_sisters': sisters,
                        'is_reverse': False
                    }

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

    # --- EXTRACT AI THREAT ASSESSMENT FROM REPORT ---
    def extract_ai_threat_level(report_text):
        """Extract threat level from AI intelligence report (Executive Summary)"""
        import re
        if not report_text:
            return None

        # Search first 1000 chars (Executive Summary section)
        summary = report_text[:1000].lower()

        # Look for threat/risk level patterns
        patterns = [
            r'threat level[:\s]+(high|medium|low)',
            r'risk level[:\s]+(high|medium|low)',
            r'overall risk[:\s]+(high|medium|low)',
            r'assessed as[:\s]+(high|medium|low)\s+(risk|threat)',
            r'represents a[:\s]+(high|medium|low)\s+risk',
            r'poses a[:\s]+(high|medium|low)\s+risk',
        ]

        for pattern in patterns:
            match = re.search(pattern, summary)
            if match:
                level = match.group(1).upper()
                return 'HIGH' if level == 'HIGH' else 'MEDIUM' if level == 'MEDIUM' else 'LOW'

        return None

    ai_threat = extract_ai_threat_level(report)

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
        # No database matches - check AI assessment
        if ai_threat == 'HIGH':
            risk_level = "MID"  # No DB match but AI flags high risk
            risk_class = "mid"
            log("AI ASSESSMENT: HIGH RISK (No database match)", "WARN")
        elif ai_threat == 'MEDIUM':
            risk_level = "MID"  # No DB match but AI flags medium risk
            risk_class = "mid"
            log("AI ASSESSMENT: MEDIUM RISK (No database match)", "WARN")
        elif ai_threat == 'LOW':
            risk_level = "LOW"  # No DB match, AI says low risk
            risk_class = "low"
            log("AI ASSESSMENT: LOW RISK (No database match)", "INFO")
        else:
            risk_level = "SAFE"  # No DB match, no clear AI threat identified
            risk_class = "safe"
    elif has_low_match:
        # Weak match, likely false positive
        # But elevate if AI assessment indicates higher risk
        if ai_threat == 'HIGH' or ai_threat == 'MEDIUM':
            risk_level = "MID"
            risk_class = "mid"
            log(f"AI ASSESSMENT: {ai_threat} RISK + Low fuzzy match → Elevated to MID", "WARN")
        else:
            risk_level = "LOW"
            risk_class = "low"
    elif has_medium_match:
        # Moderate match, requires investigation
        # Elevate if AI assessment indicates higher risk
        if ai_threat == 'HIGH':
            risk_level = "MID"
            risk_class = "mid"
            log(f"AI ASSESSMENT: HIGH RISK + Medium fuzzy match → Elevated to MID", "WARN")
        else:
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
    if not match_exists:
        # No database matches - use AI-driven descriptions
        if ai_threat in ['HIGH', 'MEDIUM']:
            threat_descriptions = {
                "MID": f"No database match, but AI intelligence analysis identifies medium-to-high risk indicators ({media_count} media source{'s' if media_count != 1 else ''} found). Review Info Summary tab for details. Manual investigation recommended.",
                "LOW": f"No database match. AI analysis suggests low risk profile ({media_count} media source{'s' if media_count != 1 else ''} found). Standard due diligence recommended.",
                "SAFE": "No matches found in sanctions databases. Entity appears clear of federal restrictions."
            }
        else:
            threat_descriptions = {
                "LOW": f"No database match. Limited intelligence available ({media_count} media source{'s' if media_count != 1 else ''} found). Manual verification recommended.",
                "SAFE": "No matches found in sanctions databases. Entity appears clear of federal restrictions."
            }
    else:
        # Database matches exist - use database-driven descriptions
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
    tab1, tab2, tab3, tab4 = st.tabs(["[1] ENTITY LIST", "[2] INFO SUMMARY", "[3] NEWS REPORT", "[4] RELATIONSHIP DIAGRAM"])

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
            # Escape dollar signs and other problematic markdown characters
            st.markdown(escape_markdown_for_display(report))
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

    # TAB 4: RELATIONSHIP DIAGRAM
    with tab4:
        # Disclaimer banner
        st.markdown("""
        <div class="alert-box alert-info">
            <strong>ℹ INFO:</strong> This relationship diagram is built from available data including corporate filings,
            ownership structures, and related party information. Entity network coverage may vary based on data availability.
        </div>
        """, unsafe_allow_html=True)

        # Fetch financial intelligence data for the entity
        directors_single = db.get_directors(company_name=final_query_name)
        shareholders_single = db.get_shareholders(company_name=final_query_name)
        transactions_single = db.get_transactions(company_name=final_query_name)

        # Check if we have any relationship data
        if not directors_single and not shareholders_single and not transactions_single:
            st.info("No relationship data available for this entity. Relationship diagrams require corporate structure data from SEC filings or other sources.")
        else:
            # Build graph from available data
            with st.spinner("Building relationship network..."):
                parent_info_single = {'jurisdiction': 'Unknown', 'status': 'Active'}
                graph_single = gb.build_entity_graph(
                    company_name=final_query_name,
                    subsidiaries=[],
                    sisters=[],
                    directors=directors_single,
                    shareholders=shareholders_single,
                    transactions=transactions_single,
                    parent_info=parent_info_single
                )

            # Get graph statistics
            stats_single = gb.get_graph_statistics(graph_single)

            # Display quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entities", stats_single['total_nodes'])
            with col2:
                st.metric("Relationships", stats_single['total_edges'])
            with col3:
                st.metric("Countries", stats_single['num_countries'])
            with col4:
                if stats_single['most_connected']:
                    st.metric("Most Connected", stats_single['most_connected'][:15] + "..." if len(stats_single['most_connected']) > 15 else stats_single['most_connected'])

            # Sub-tabs for different visualizations
            viz_tab1_single, viz_tab2_single = st.tabs(["🔗 Network View", "🌍 Geographic View"])

            with viz_tab1_single:
                # Use the new visualization selector for multiple visualization options
                viz_selector.display_visualization_selector(
                    graph=graph_single,
                    parent_company=final_query_name,
                    key_prefix="single_entity"
                )

            with viz_tab2_single:
                st.markdown("<div class='alert-box alert-info'>Geographic distribution of entities showing jurisdictions and cross-border relationships</div>", unsafe_allow_html=True)

                # Filter controls for geographic view
                col1, col2 = st.columns(2)
                with col1:
                    show_directors_single_geo = st.checkbox("Show Directors", value=True, key="show_directors_single_geo")
                with col2:
                    show_shareholders_single_geo = st.checkbox("Show Shareholders", value=True, key="show_shareholders_single_geo")

                # Filter graph for geographic view
                filtered_graph_single_geo = gb.filter_graph(graph_single, show_directors_single_geo, show_shareholders_single_geo, True)

                # Create and display geographic map
                geo_map_single = viz.create_geographic_map(filtered_graph_single_geo, title=f"Geographic Distribution: {final_query_name}")
                components.html(geo_map_single._repr_html_(), height=650)

            # Graph Explorer
            with st.expander("📊 EXPLORE GRAPH DATABASE"):
                st.markdown("### Graph Statistics")

                # Display detailed statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    **Network Composition:**
                    - Total Nodes: {stats_single['total_nodes']}
                    - Companies: {stats_single['companies']}
                    - People: {stats_single['people']}
                    - Total Relationships: {stats_single['total_edges']}
                    """)
                with col2:
                    st.markdown(f"""
                    **Geographic Distribution:**
                    - Countries Represented: {stats_single['num_countries']}
                    - Countries: {', '.join(stats_single['countries'][:5])}{'...' if len(stats_single['countries']) > 5 else ''}
                    """)

                st.markdown("---")
                st.markdown("### Relationship Explorer")

                # Entity selector
                node_list_single = list(graph_single.nodes())
                if node_list_single:
                    selected_entity_single = st.selectbox("Select Entity to Explore", node_list_single, key="entity_explorer_single")

                    if selected_entity_single:
                        # Get neighbors
                        neighbors_single = gb.get_neighbors_table(graph_single, selected_entity_single)

                        if neighbors_single:
                            st.markdown(f"**Showing {len(neighbors_single)} relationships for {selected_entity_single}:**")

                            # Convert to DataFrame for display
                            df_neighbors_single = pd.DataFrame(neighbors_single)
                            st.dataframe(df_neighbors_single, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No relationships found for {selected_entity_single}")

                st.markdown("---")
                st.markdown("### Path Finder")

                # Path finder
                col1, col2 = st.columns(2)
                with col1:
                    source_entity_single = st.selectbox("From Entity", node_list_single, key="path_source_single")
                with col2:
                    target_entity_single = st.selectbox("To Entity", node_list_single, key="path_target_single")

                if st.button("Find Paths", key="find_paths_single"):
                    if source_entity_single and target_entity_single and source_entity_single != target_entity_single:
                        paths_single = gb.find_paths(filtered_graph_single, source_entity_single, target_entity_single, max_paths=5)

                        if paths_single:
                            st.success(f"Found {len(paths_single)} path(s) between {source_entity_single} and {target_entity_single}:")
                            for i, path in enumerate(paths_single, 1):
                                path_str = " → ".join(path)
                                st.markdown(f"**Path {i}:** {path_str}")
                        else:
                            st.warning(f"No paths found between {source_entity_single} and {target_entity_single}")
                    else:
                        st.warning("Please select two different entities")

    # --- SAVE & EXPORT SECTION ---
    st.markdown("---")
    st.markdown("### 💾 SAVE & EXPORT")

    # Prepare search data for saving
    search_data_to_save = {
        'entity_name': final_query_name,
        'translated_name': final_query_name if final_query_name != name_input else None,
        'search_params': {
            'country': country_input,
            'fuzzy': fuzzy,
            'conglomerate': st.session_state.get('search_conglomerate', False),
            'reverse_search': st.session_state.get('reverse_search', False),
            'search_depth': st.session_state.get('search_depth', 1),
            'ownership_threshold': st.session_state.get('ownership_threshold', 0.0)
        },
        'results': {
            'us_results': us_results,
            'media_hits': media_hits,
            'report': report,
            'pdf_bytes': pdf_bytes,
            'conglomerate_data': st.session_state.get('related_companies_found')
        }
    }

    # Auto-save functionality
    if st.session_state.auto_save_enabled and not st.session_state.get(f'auto_saved_{analysis_id}', False):
        # Generate search ID
        search_id = serializer.generate_search_id()

        # Serialize parameters and results
        serialized_params = serializer.serialize_search_params(search_data_to_save['search_params'])
        serialized_results = serializer.serialize_search_results(search_data_to_save['results'])
        summary_metrics = serializer.calculate_summary_metrics(search_data_to_save['results'])

        # Save to database
        success = db.save_search_results(
            search_id=search_id,
            entity_name=final_query_name,
            translated_name=search_data_to_save['translated_name'],
            search_params=serialized_params,
            results_data=serialized_results,
            summary_metrics=summary_metrics,
            user_metadata={'notes': '', 'tags': '[]', 'is_auto_saved': 1}
        )

        if success:
            st.session_state[f'auto_saved_{analysis_id}'] = True
            st.session_state.current_search_id = search_id
            st.toast(f"✓ Search auto-saved (ID: {search_id[:12]}...)")

    # Manual save and export buttons
    col_save1, col_save2, col_save3, col_save4 = st.columns(4)

    with col_save1:
        if st.button("💾 SAVE SEARCH", use_container_width=True, help="Save this search with notes and tags"):
            st.session_state.show_save_dialog = True

    with col_save2:
        if st.session_state.get('current_search_id'):
            # Show export options if search is saved
            if st.button("📤 EXPORT", use_container_width=True, help="Export search as JSON, Excel, or PDF"):
                st.session_state.show_export_dialog = True

    with col_save3:
        # Auto-save status indicator
        if st.session_state.auto_save_enabled:
            st.markdown("<div class='alert-box alert-success' style='padding: 8px; text-align: center;'>✓ AUTO-SAVED</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='alert-box alert-info' style='padding: 8px; text-align: center;'>MANUAL MODE</div>", unsafe_allow_html=True)

    # Save dialog
    if st.session_state.get('show_save_dialog', False):
        with st.form("save_search_form"):
            st.markdown("#### Save Search")
            notes = st.text_area("Notes (optional)", placeholder="Add notes about this search...")
            tags = st.text_input("Tags (comma-separated)", placeholder="high-priority, q1-2026, compliance")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("💾 Save", use_container_width=True)
            with col_cancel:
                cancelled = st.form_submit_button("Cancel", use_container_width=True)

            if submitted:
                # Generate search ID
                search_id = serializer.generate_search_id()

                # Serialize parameters and results
                serialized_params = serializer.serialize_search_params(search_data_to_save['search_params'])
                serialized_results = serializer.serialize_search_results(search_data_to_save['results'])
                summary_metrics = serializer.calculate_summary_metrics(search_data_to_save['results'])

                # Parse tags
                tags_json = serializer.parse_tags(tags)

                # Save to database
                success = db.save_search_results(
                    search_id=search_id,
                    entity_name=final_query_name,
                    translated_name=search_data_to_save['translated_name'],
                    search_params=serialized_params,
                    results_data=serialized_results,
                    summary_metrics=summary_metrics,
                    user_metadata={'notes': notes, 'tags': tags_json, 'is_auto_saved': 0}
                )

                if success:
                    st.success(f"✓ Search saved! ID: {search_id}")
                    st.session_state.current_search_id = search_id
                    st.session_state.show_save_dialog = False
                    st.rerun()
                else:
                    st.error("Failed to save search")

            if cancelled:
                st.session_state.show_save_dialog = False
                st.rerun()

    # Export dialog
    if st.session_state.get('show_export_dialog', False) and st.session_state.get('current_search_id'):
        st.markdown("#### Export Options")

        # Load full search data for export
        search_id = st.session_state.current_search_id
        saved_search = db.load_search_results(search_id)

        if saved_search:
            # Reconstruct search data for export
            export_data = {
                'search_id': search_id,
                'timestamp': saved_search['timestamp'],
                'entity_name': saved_search['entity_name'],
                'risk_level': saved_search['risk_level'],
                'match_count': saved_search['match_count'],
                'subsidiary_count': saved_search['subsidiary_count'],
                'sister_count': saved_search['sister_count'],
                'country_filter': saved_search['country_filter'],
                'fuzzy_search': saved_search['fuzzy_search'],
                'notes': saved_search['notes'],
                'results': serializer.deserialize_search_results(saved_search)
            }

            col_exp1, col_exp2, col_exp3 = st.columns(3)

            with col_exp1:
                exporter.create_download_button_json(search_id, export_data, saved_search['entity_name'])

            with col_exp2:
                exporter.create_download_button_excel(search_id, export_data, saved_search['entity_name'])

            with col_exp3:
                exporter.create_download_button_pdf(search_id, export_data, saved_search['entity_name'])

            if st.button("Close Export", use_container_width=True):
                st.session_state.show_export_dialog = False
                st.rerun()

    # --- FOOTER ---
    st.markdown("---")

    with st.expander("📜 SAVED SEARCH HISTORY"):
        display_search_history()

def display_entity_results(entity_name, data, country_input, fuzzy, conglomerate_context=None):
    """
    Display results for a single entity (reusable for both single and conglomerate searches).
    This is extracted from run_analysis() for code reuse.

    Args:
        entity_name: Name of the entity being displayed
        data: Analysis data for the entity
        country_input: Country filter
        fuzzy: Fuzzy search flag
        conglomerate_context: Optional dict with {'parent': str, 'subsidiaries': list, 'sisters': list}
                            for relationship diagram in conglomerate mode
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
    tab1, tab2, tab3, tab4 = st.tabs(["[1] ENTITY LIST", "[2] INFO SUMMARY", "[3] NEWS REPORT", "[4] RELATIONSHIP DIAGRAM"])

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
        # Escape dollar signs and other problematic markdown characters
        st.markdown(escape_markdown_for_display(report))

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

    # TAB 4: RELATIONSHIP DIAGRAM (for display_entity_results)
    with tab4:
        st.markdown("""
        <div class="alert-box alert-info">
            <strong>ℹ INFO:</strong> This relationship diagram shows connections from available corporate data.
            Coverage varies based on data availability in SEC filings and other sources.
        </div>
        """, unsafe_allow_html=True)

        # Fetch financial intelligence data
        directors_display = db.get_directors(company_name=final_query_name)
        shareholders_display = db.get_shareholders(company_name=final_query_name)
        transactions_display = db.get_transactions(company_name=final_query_name)

        # Determine if we have relationship data to display
        graph_display = None

        # If conglomerate context is provided, use it for the diagram
        if conglomerate_context:
            # Build graph with full conglomerate structure
            with st.spinner("Building relationship network..."):
                parent_info_display = {'jurisdiction': 'Unknown', 'status': 'Active'}
                graph_display = gb.build_entity_graph(
                    company_name=conglomerate_context['parent'],
                    subsidiaries=conglomerate_context.get('subsidiaries', []),
                    sisters=conglomerate_context.get('sisters', []),
                    directors=directors_display,
                    shareholders=shareholders_display,
                    transactions=transactions_display,
                    parent_info=parent_info_display
                )

        # Check if we have any relationship data for single entity mode
        elif not directors_display and not shareholders_display and not transactions_display:
            st.info("No relationship data available for this entity. Relationship diagrams require corporate structure data from SEC filings or other sources.")
        else:
            # Build graph from available data (single entity mode)
            with st.spinner("Building relationship network..."):
                parent_info_display = {'jurisdiction': 'Unknown', 'status': 'Active'}
                graph_display = gb.build_entity_graph(
                    company_name=final_query_name,
                    subsidiaries=[],
                    sisters=[],
                    directors=directors_display,
                    shareholders=shareholders_display,
                    transactions=transactions_display,
                    parent_info=parent_info_display
                )

        # If graph was built, display visualizations
        if graph_display:
            # Get graph statistics
            stats_display = gb.get_graph_statistics(graph_display)

            # Display quick stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entities", stats_display['total_nodes'])
            with col2:
                st.metric("Relationships", stats_display['total_edges'])
            with col3:
                st.metric("Countries", stats_display['num_countries'])
            with col4:
                if stats_display['most_connected']:
                    st.metric("Most Connected", stats_display['most_connected'][:15] + "..." if len(stats_display['most_connected']) > 15 else stats_display['most_connected'])

            # Sub-tabs for different visualizations
            viz_tab1_display, viz_tab2_display = st.tabs(["🔗 Network View", "🌍 Geographic View"])

            with viz_tab1_display:
                st.markdown("<div class='alert-box alert-info'>Interactive Neo4j-style network - Drag nodes, scroll to zoom, click to explore relationships</div>", unsafe_allow_html=True)

                # Filter controls
                col1, col2 = st.columns(2)
                with col1:
                    show_directors_display = st.checkbox("Show Directors", value=True, key=f"show_directors_display_{final_query_name}")
                with col2:
                    show_shareholders_display = st.checkbox("Show Shareholders", value=True, key=f"show_shareholders_display_{final_query_name}")

                # Filter graph
                filtered_graph_display = gb.filter_graph(graph_display, show_directors_display, show_shareholders_display, True)

                # Create and display interactive network diagram
                network_html_display = viz.create_interactive_network(
                    filtered_graph_display,
                    title=f"Entity Relationship Network: {final_query_name}",
                    height="700px"
                )
                components.html(network_html_display, height=750, scrolling=True)

            with viz_tab2_display:
                # Create and display geographic map
                geo_map_display = viz.create_geographic_map(filtered_graph_display, title=f"Geographic Distribution: {final_query_name}")
                components.html(geo_map_display._repr_html_(), height=650)

            # Graph Explorer (simplified for individual entity view)
            with st.expander("📊 EXPLORE GRAPH DATABASE"):
                st.markdown("### Relationship Explorer")

                # Entity selector
                node_list_display = list(filtered_graph_display.nodes())
                if node_list_display:
                    selected_entity_display = st.selectbox("Select Entity to Explore", node_list_display, key=f"entity_explorer_display_{final_query_name}")

                    if selected_entity_display:
                        # Get neighbors
                        neighbors_display = gb.get_neighbors_table(filtered_graph_display, selected_entity_display)

                        if neighbors_display:
                            st.markdown(f"**Showing {len(neighbors_display)} relationships for {selected_entity_display}:**")

                            # Convert to DataFrame for display
                            df_neighbors_display = pd.DataFrame(neighbors_display)
                            st.dataframe(df_neighbors_display, use_container_width=True, hide_index=True)
                        else:
                            st.info(f"No relationships found for {selected_entity_display}")

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

    # === CONGLOMERATE RELATIONSHIP DIAGRAM ===
    st.markdown("---")
    st.markdown("### 🔗 Conglomerate Relationship Network")

    # Fetch financial intelligence data for the parent company
    directors = db.get_directors(company_name=parent_company)
    shareholders = db.get_shareholders(company_name=parent_company)
    transactions = db.get_transactions(company_name=parent_company)

    # Build graph from conglomerate data
    with st.spinner("Building conglomerate relationship network..."):
        # Convert entities_to_search to subsidiaries/sisters format
        subsidiaries_list = []
        sisters_list = []

        # Check if this is a reverse search
        conglom_structure = st.session_state.get('conglomerate_structure', {})
        is_reverse = conglom_structure.get('is_reverse', False)

        # For reverse search, the real parent is stored in conglomerate_structure
        if is_reverse:
            # Get the actual parent company (e.g., Alibaba)
            actual_parent = conglom_structure.get('parent', parent_company)

            # In reverse search, all entities (Lazada + its sisters) are subsidiaries of the parent
            # They should all connect to the parent node, not to each other
            for entity in entities_to_search:
                if entity['type'] == 'PARENT':
                    # This is actually the searched subsidiary (Lazada), add as subsidiary
                    subsidiaries_list.append({
                        'name': entity['name'],
                        'jurisdiction': entity.get('jurisdiction', 'Unknown'),
                        'status': 'Active',
                        'level': entity.get('level', 1),
                        'is_searched_entity': True
                    })
                else:
                    # These are sister companies - also subsidiaries of the parent
                    subsidiaries_list.append({
                        'name': entity['name'],
                        'jurisdiction': entity.get('jurisdiction', 'Unknown'),
                        'status': 'Active',
                        'level': entity.get('level', 1)
                    })

            # Use the actual parent for the graph
            graph_parent_name = actual_parent
        else:
            # Normal forward search: parent_company is the actual parent
            for entity in entities_to_search:
                if entity['type'] == 'PARENT':
                    continue
                elif entity.get('relationship') == 'sister':
                    sisters_list.append({
                        'name': entity['name'],
                        'jurisdiction': entity.get('jurisdiction', 'Unknown'),
                        'status': 'Active',
                        'level': entity.get('level', 1)
                    })
                else:  # SUBSIDIARY
                    subsidiaries_list.append({
                        'name': entity['name'],
                        'jurisdiction': entity.get('jurisdiction', 'Unknown'),
                        'status': 'Active',
                        'level': entity.get('level', 1)
                    })

            graph_parent_name = parent_company

        parent_info = {'jurisdiction': 'Unknown', 'status': 'Active'}
        graph = gb.build_entity_graph(
            company_name=graph_parent_name,
            subsidiaries=subsidiaries_list,
            sisters=sisters_list,
            directors=directors,
            shareholders=shareholders,
            transactions=transactions,
            parent_info=parent_info
        )

    # Get graph statistics
    stats = gb.get_graph_statistics(graph)

    # Display quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Entities", stats['total_nodes'])
    with col2:
        st.metric("Relationships", stats['total_edges'])
    with col3:
        st.metric("Countries", stats['num_countries'])
    with col4:
        if stats['most_connected']:
            st.metric("Most Connected", stats['most_connected'][:15] + "..." if len(stats['most_connected']) > 15 else stats['most_connected'])

    # Sub-tabs for different visualizations
    viz_tab1, viz_tab2 = st.tabs(["🔗 Network View", "🌍 Geographic View"])

    with viz_tab1:
        # Use the new visualization selector for multiple visualization options
        viz_selector.display_visualization_selector(
            graph=graph,
            parent_company=parent_company,
            key_prefix="conglomerate_main"
        )

    with viz_tab2:
        st.markdown("<div class='alert-box alert-info'>Geographic distribution showing entity locations and cross-border relationships</div>", unsafe_allow_html=True)

        # Filter controls for geographic view
        col1, col2, col3 = st.columns(3)
        with col1:
            show_directors_cong_geo = st.checkbox("Show Directors", value=True, key="show_directors_cong_geo")
        with col2:
            show_shareholders_cong_geo = st.checkbox("Show Shareholders", value=True, key="show_shareholders_cong_geo")
        with col3:
            # Country filter
            all_countries = ['All'] + stats['countries']
            country_filter_geo = st.selectbox("Filter by Country", all_countries, key="country_filter_cong_geo")

        # Filter graph for geographic view
        filtered_graph_cong_geo = gb.filter_graph(
            graph,
            show_directors_cong_geo,
            show_shareholders_cong_geo,
            True,
            country_filter_geo if country_filter_geo != 'All' else None
        )

        # Create and display geographic map
        geo_map_cong = viz.create_geographic_map(filtered_graph_cong_geo, title=f"Geographic Distribution: {parent_company} Conglomerate")
        components.html(geo_map_cong._repr_html_(), height=650)

    # Graph Explorer
    with st.expander("📊 EXPLORE GRAPH DATABASE"):
        st.markdown("### Graph Statistics")

        # Display detailed statistics
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Network Composition:**
            - Total Nodes: {stats['total_nodes']}
            - Companies: {stats['companies']}
            - People: {stats['people']}
            - Total Relationships: {stats['total_edges']}
            """)
        with col2:
            st.markdown(f"""
            **Geographic Distribution:**
            - Countries Represented: {stats['num_countries']}
            - Countries: {', '.join(stats['countries'][:5])}{'...' if len(stats['countries']) > 5 else ''}
            """)

        st.markdown("---")
        st.markdown("### Relationship Explorer")

        # Entity selector
        node_list_cong = list(graph.nodes())
        if node_list_cong:
            selected_entity_cong = st.selectbox("Select Entity to Explore", node_list_cong, key="entity_explorer_cong")

            if selected_entity_cong:
                # Get neighbors
                neighbors_cong = gb.get_neighbors_table(graph, selected_entity_cong)

                if neighbors_cong:
                    st.markdown(f"**Showing {len(neighbors_cong)} relationships for {selected_entity_cong}:**")

                    # Convert to DataFrame for display
                    df_neighbors_cong = pd.DataFrame(neighbors_cong)
                    st.dataframe(df_neighbors_cong, use_container_width=True, hide_index=True)
                else:
                    st.info(f"No relationships found for {selected_entity_cong}")

        st.markdown("---")
        st.markdown("### Path Finder")

        # Path finder
        col1, col2 = st.columns(2)
        with col1:
            source_entity_cong = st.selectbox("From Entity", node_list_cong, key="path_source_cong")
        with col2:
            target_entity_cong = st.selectbox("To Entity", node_list_cong, key="path_target_cong")

        if st.button("Find Paths", key="find_paths_cong"):
            if source_entity_cong and target_entity_cong and source_entity_cong != target_entity_cong:
                paths_cong = gb.find_paths(filtered_graph_cong, source_entity_cong, target_entity_cong, max_paths=5)

                if paths_cong:
                    st.success(f"Found {len(paths_cong)} path(s) between {source_entity_cong} and {target_entity_cong}:")
                    for i, path in enumerate(paths_cong, 1):
                        path_str = " → ".join(path)
                        st.markdown(f"**Path {i}:** {path_str}")
                else:
                    st.warning(f"No paths found between {source_entity_cong} and {target_entity_cong}")
            else:
                st.warning("Please select two different entities")

    st.markdown("---")
    st.markdown("### 📋 Individual Entity Analysis")
    st.markdown("<div class='alert-box alert-info'>Detailed sanctions screening results for each entity in the conglomerate</div>", unsafe_allow_html=True)

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
            # Pass conglomerate context so relationship diagram shows parent-sister structure
            conglomerate_ctx = {
                'parent': parent_company,
                'subsidiaries': subsidiaries_list,
                'sisters': sisters_list
            }
            display_entity_results(entity['name'], data, country_input, fuzzy, conglomerate_context=conglomerate_ctx)

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