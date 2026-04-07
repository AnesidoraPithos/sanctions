"""
Visualization Selector Component

Provides a unified interface for selecting and displaying different
visualization types for large graphs (100+ nodes).
"""

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import visualizations as viz
import visualizations_advanced as viz_adv  # Only used for create_filtered_network_view
from typing import Optional


def display_visualization_selector(
    graph: nx.MultiDiGraph,
    parent_company: str,
    key_prefix: str = "viz",
    highlighted_nodes: list = None
):
    """
    Display a visualization selector with multiple options optimized for different graph sizes.

    Args:
        graph: NetworkX graph to visualize
        parent_company: Name of parent company for titles
        key_prefix: Unique prefix for Streamlit widget keys
        highlighted_nodes: List of node names to highlight (e.g., selected subsidiaries)
    """
    num_nodes = graph.number_of_nodes()

    # Show recommendation based on graph size
    if num_nodes > 100:
        st.markdown(
            f"""<div class='alert-box alert-warning'>
            <b>Large Graph Detected ({num_nodes} nodes)</b><br>
            Use level control to show specific depth levels for better clarity.
            </div>""",
            unsafe_allow_html=True
        )
    elif num_nodes > 50:
        st.markdown(
            f"""<div class='alert-box alert-info'>
            <b>Medium Graph ({num_nodes} nodes)</b><br>
            Adjust depth levels and country filters to focus on specific branches.
            </div>""",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # Display only filtered network visualization
    display_filtered_network(graph, parent_company, key_prefix, highlighted_nodes)


# REMOVED VISUALIZATIONS - Treemap, Hierarchical Network, Collapsible Tree, Sunburst
# Keeping only Filtered Network (Level Control)


def display_filtered_network(graph, parent_company, key_prefix, highlighted_nodes=None):
    """Display network with level and country filters"""
    st.markdown(
        """<div class='alert-box alert-info'>
        <b>Filtered Network View</b> - Show only specific levels and countries for a cleaner view.
        </div>""",
        unsafe_allow_html=True
    )

    # Filter controls
    col1, col2, col3 = st.columns(3)

    with col1:
        max_level = st.slider(
            "Maximum Depth Level",
            min_value=0,
            max_value=10,
            value=2,
            key=f"{key_prefix}_max_level",
            help="Show only entities up to this depth level"
        )

    with col2:
        # Get unique countries from graph
        countries = set()
        for node, attrs in graph.nodes(data=True):
            jurisdiction = attrs.get('jurisdiction', 'Unknown')
            if jurisdiction != 'Unknown':
                countries.add(jurisdiction)

        selected_countries = st.multiselect(
            "Filter by Countries",
            options=sorted(countries),
            default=None,
            key=f"{key_prefix}_countries",
            help="Leave empty to show all countries"
        )

    with col3:
        show_directors = st.checkbox("Show Directors", value=False, key=f"{key_prefix}_filt_directors")
        show_shareholders = st.checkbox("Show Shareholders", value=False, key=f"{key_prefix}_filt_shareholders")

    # Apply filters
    import graph_builder as gb
    filtered_graph = viz_adv.create_filtered_network_view(
        graph,
        max_level=max_level,
        countries=selected_countries if selected_countries else None
    )
    filtered_graph = gb.filter_graph(filtered_graph, show_directors, show_shareholders, True)

    # Show statistics
    st.markdown(f"**Filtered Graph:** {filtered_graph.number_of_nodes()} nodes, {filtered_graph.number_of_edges()} edges")

    # Show highlighted nodes info
    if highlighted_nodes:
        st.markdown(f"**⭐ Selected Entities:** {len(highlighted_nodes)} highlighted in gold")

    # Create and display
    network_html = viz.create_interactive_network(
        filtered_graph,
        title=f"Filtered Network: {parent_company}",
        height="700px",
        highlighted_nodes=highlighted_nodes
    )
    components.html(network_html, height=750, scrolling=True)

    with st.expander("💡 About Filtered View"):
        st.markdown("""
        **Use This When:**
        - You have a very large graph (100+ nodes)
        - You want to focus on specific depth levels
        - You want to see entities from certain countries only
        - You need a cleaner, less cluttered view

        **Tips:**
        - Start with Level 0-2 to see the core structure
        - Add countries one at a time to understand regional operations
        - Disable directors/shareholders to focus on corporate structure
        """)
