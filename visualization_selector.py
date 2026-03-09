"""
Visualization Selector Component

Provides a unified interface for selecting and displaying different
visualization types for large graphs (100+ nodes).
"""

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
import visualizations as viz
import visualizations_advanced as viz_adv
from typing import Optional


def display_visualization_selector(
    graph: nx.MultiDiGraph,
    parent_company: str,
    key_prefix: str = "viz"
):
    """
    Display a visualization selector with multiple options optimized for different graph sizes.

    Args:
        graph: NetworkX graph to visualize
        parent_company: Name of parent company for titles
        key_prefix: Unique prefix for Streamlit widget keys
    """
    num_nodes = graph.number_of_nodes()

    # Show recommendation based on graph size
    if num_nodes > 100:
        st.markdown(
            f"""<div class='alert-box alert-warning'>
            <b>Large Graph Detected ({num_nodes} nodes)</b><br>
            Using Treemap (Country-Grouped) as default for optimal clarity.
            </div>""",
            unsafe_allow_html=True
        )
    elif num_nodes > 50:
        st.markdown(
            f"""<div class='alert-box alert-info'>
            <b>Medium Graph ({num_nodes} nodes)</b><br>
            Using Treemap (Country-Grouped) for clear country-based visualization.
            </div>""",
            unsafe_allow_html=True
        )

    # Visualization type selector
    viz_type = st.selectbox(
        "Select Visualization Type",
        options=[
            "Treemap (Country-Grouped) - DEFAULT",
            "Collapsible Tree (Best for 100+ nodes)",
            "Hierarchical Network (Interactive Physics)",
            "Sunburst Chart (Radial)",
            "Filtered Network (Level Control)"
        ],
        key=f"{key_prefix}_type_selector",
        help="Choose the visualization that best suits your needs"
    )

    st.markdown("---")

    # Display the selected visualization
    if viz_type == "Treemap (Country-Grouped) - DEFAULT":
        display_treemap(graph, parent_company, key_prefix)

    elif viz_type == "Collapsible Tree (Best for 100+ nodes)":
        display_collapsible_tree(graph, parent_company, key_prefix)

    elif viz_type == "Hierarchical Network (Interactive Physics)":
        display_hierarchical_network(graph, parent_company, key_prefix)

    elif viz_type == "Sunburst Chart (Radial)":
        display_sunburst(graph, parent_company, key_prefix)

    elif viz_type == "Filtered Network (Level Control)":
        display_filtered_network(graph, parent_company, key_prefix)


def display_hierarchical_network(graph, parent_company, key_prefix):
    """Display the default hierarchical network with physics"""
    st.markdown(
        "<div class='alert-box alert-info'>Interactive Neo4j-style network - Hierarchical layout showing depth levels. Drag nodes, scroll to zoom.</div>",
        unsafe_allow_html=True
    )

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        show_directors = st.checkbox("Show Directors", value=True, key=f"{key_prefix}_directors")
    with col2:
        show_shareholders = st.checkbox("Show Shareholders", value=True, key=f"{key_prefix}_shareholders")

    # Filter graph
    import graph_builder as gb
    filtered_graph = gb.filter_graph(graph, show_directors, show_shareholders, True)

    # Create and display
    network_html = viz.create_interactive_network(
        filtered_graph,
        title=f"Entity Relationship Network: {parent_company}",
        height="700px"
    )
    components.html(network_html, height=750, scrolling=True)


def display_collapsible_tree(graph, parent_company, key_prefix):
    """Display collapsible tree - best for large graphs"""
    st.markdown(
        """<div class='alert-box alert-success'>
        <b>Collapsible Tree View</b> - Start with collapsed view. Click nodes to expand/collapse branches.
        Use controls to expand to specific levels. Ideal for 100+ nodes.
        </div>""",
        unsafe_allow_html=True
    )

    # Create collapsible tree
    tree_html = viz_adv.create_collapsible_tree(
        graph,
        title=f"Entity Tree: {parent_company}",
        height="800px"
    )
    components.html(tree_html, height=850, scrolling=True)

    # Add tips
    with st.expander("💡 Tips for Using Collapsible Tree"):
        st.markdown("""
        **Controls:**
        - **Click any node** to expand/collapse its children
        - **Expand All**: Show the entire tree
        - **Collapse All**: Return to minimal view
        - **Show Level 1-2**: Expand only to specific depth
        - **Reset View**: Return to initial state

        **Color Legend:**
        - 🔴 Red = Main search entity
        - 🔵 Cyan = Parent company
        - 🟢 Green = Subsidiary
        - 🟡 Yellow = Node with collapsed children

        **Best for:** Graphs with 100+ nodes where you want to focus on specific branches
        """)


def display_treemap(graph, parent_company, key_prefix):
    """Display treemap visualization with country-first grouping"""
    st.markdown(
        """<div class='alert-box alert-success'>
        <b>Treemap View (Country-Grouped)</b> - Entities grouped by country/jurisdiction.
        Each country is a distinct colored section containing its subsidiaries.
        </div>""",
        unsafe_allow_html=True
    )

    # Debug info
    print(f"[DISPLAY_TREEMAP DEBUG] Graph has {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    print(f"[DISPLAY_TREEMAP DEBUG] Parent company: {parent_company}")

    # Create treemap
    try:
        fig = viz_adv.create_treemap_visualization(
            graph,
            title=f"Entity Treemap: {parent_company}",
            height=750
        )
        print(f"[DISPLAY_TREEMAP DEBUG] Treemap created successfully")
        st.plotly_chart(fig, use_container_width=True)
        print(f"[DISPLAY_TREEMAP DEBUG] Plotly chart displayed")
    except Exception as e:
        print(f"[DISPLAY_TREEMAP ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        st.error(f"Error creating treemap: {str(e)}")

    with st.expander("💡 How to Read This Treemap"):
        st.markdown("""
        **Structure:**
        - **Parent Company** (outer border) contains all country groups
        - **📍 Country Sections** (e.g., "📍 China", "📍 Singapore") are colored by country
        - **Subsidiaries** sit within their respective country sections

        **Size Meaning:**
        - Larger rectangles = More subsidiaries
        - Country section size = Total number of entities in that country

        **Colors:**
        - 🔵 Cyan = Parent company
        - 🔴 Red = Main search entity (the one you searched for)
        - Each country has a unique color (e.g., 🟣 Purple for China, 🟠 Orange for Singapore)

        **Interaction:**
        - **Hover** over any rectangle to see details
        - **Click** to zoom into that section
        - **Click the outer border** to zoom back out

        **Best for:**
        - Understanding geographic distribution at a glance
        - Seeing which countries have the most subsidiaries
        - Identifying clusters of operations in specific regions
        - Comparing relative sizes of country operations
        """)

    # Show quick stats
    countries = set()
    for node, attrs in graph.nodes(data=True):
        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        if jurisdiction != 'Unknown':
            countries.add(jurisdiction)

    if len(countries) > 0:
        st.markdown(f"**🌍 Geographic Coverage:** {len(countries)} countries/jurisdictions represented")
        st.markdown(f"**Countries:** {', '.join(sorted(countries))}")


def display_sunburst(graph, parent_company, key_prefix):
    """Display sunburst/radial chart"""
    st.markdown(
        """<div class='alert-box alert-info'>
        <b>Sunburst Chart</b> - Radial hierarchy with parent at center. Each ring = depth level.
        </div>""",
        unsafe_allow_html=True
    )

    # Create sunburst
    fig = viz_adv.create_sunburst_chart(
        graph,
        title=f"Entity Sunburst: {parent_company}",
        height=750
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("💡 About Sunburst"):
        st.markdown("""
        **How to Read:**
        - Center = Parent company
        - Inner rings = Immediate subsidiaries (Level 1)
        - Outer rings = Deeper subsidiaries (Level 2+)
        - Click segments to zoom in
        - Colors indicate special entities (red=searched, cyan=parent)

        **Best for:** Understanding the radial structure and depth of corporate ownership
        """)


def display_filtered_network(graph, parent_company, key_prefix):
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

    # Create and display
    network_html = viz.create_interactive_network(
        filtered_graph,
        title=f"Filtered Network: {parent_company}",
        height="700px"
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
