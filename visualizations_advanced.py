"""
Advanced Visualization Module for Large Entity Hierarchies

This module provides specialized visualizations for handling 100+ node graphs:
- Collapsible tree diagram
- Treemap visualization
- Radial/sunburst chart
- Filtered hierarchical view with controls
"""

import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple
import json


def create_collapsible_tree(
    G: nx.MultiDiGraph,
    title: str = "Collapsible Entity Tree",
    height: str = "800px"
) -> str:
    """
    Create a collapsible D3.js-style tree that starts collapsed.
    Users can click nodes to expand/collapse branches.

    Args:
        G: NetworkX graph
        title: Title for the visualization
        height: Height of the container

    Returns:
        HTML string with interactive collapsible tree
    """
    print(f"[COLLAPSIBLE_TREE DEBUG] Creating tree for graph with {G.number_of_nodes()} nodes")

    # Convert NetworkX graph to hierarchical JSON structure
    tree_data = graph_to_tree_json(G)
    print(f"[COLLAPSIBLE_TREE DEBUG] Tree data created: {list(tree_data.keys())}")

    # Color mappings
    SEARCHED_ENTITY_COLOR = '#ef4444'
    PARENT_COMPANY_COLOR = '#0ea5e9'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background-color: #0b1121;
                font-family: 'Inter', sans-serif;
                overflow: auto;
            }}
            #tree-container {{
                width: 100%;
                height: {height};
                background-color: #0b1121;
                border: 2px solid #334155;
                border-radius: 8px;
                overflow: auto;
            }}
            .node circle {{
                fill: #10b981;
                stroke: #fff;
                stroke-width: 2px;
                cursor: pointer;
            }}
            .node.parent circle {{
                fill: {PARENT_COMPANY_COLOR};
            }}
            .node.searched circle {{
                fill: {SEARCHED_ENTITY_COLOR};
            }}
            .node text {{
                font: 12px 'Inter', sans-serif;
                fill: #e2e8f0;
                text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            }}
            .link {{
                fill: none;
                stroke: #64748b;
                stroke-width: 2px;
            }}
            .node.collapsed circle {{
                fill: #fbbf24;
            }}
            #controls {{
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(30, 41, 59, 0.95);
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 15px;
                color: #e2e8f0;
                z-index: 1000;
            }}
            button {{
                background: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                margin: 5px 0;
                width: 100%;
                font-size: 13px;
            }}
            button:hover {{
                background: #2563eb;
            }}
            .legend {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: rgba(30, 41, 59, 0.95);
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 15px;
                color: #e2e8f0;
                font-size: 12px;
                max-width: 200px;
            }}
            .legend-item {{
                margin: 5px 0;
            }}
            .legend-color {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }}
        </style>
    </head>
    <body>
        <div id="controls">
            <h3 style="margin-top:0; color: #3b82f6;">Tree Controls</h3>
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
            <button onclick="expandToLevel(1)">Show Level 1</button>
            <button onclick="expandToLevel(2)">Show Levels 1-2</button>
            <button onclick="resetView()">Reset View</button>
        </div>

        <div class="legend">
            <h4 style="margin-top:0; color: #3b82f6;">Legend</h4>
            <div class="legend-item">
                <span class="legend-color" style="background: {SEARCHED_ENTITY_COLOR};"></span>
                <span>Search Entity</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: {PARENT_COMPANY_COLOR};"></span>
                <span>Parent</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #10b981;"></span>
                <span>Subsidiary</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #fbbf24;"></span>
                <span>Collapsed</span>
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #475569;">
                <small>Click nodes to expand/collapse</small>
            </div>
        </div>

        <svg id="tree-container"></svg>

        <script src="https://d3js.org/d3.v7.min.js"></script>
        <script>
            const treeData = {json.dumps(tree_data)};

            const width = window.innerWidth - 40;
            const height = parseInt("{height}") || 800;

            const svg = d3.select("#tree-container")
                .attr("width", width)
                .attr("height", height);

            const g = svg.append("g")
                .attr("transform", "translate(100,50)");

            const tree = d3.tree()
                .size([height - 100, width - 300]);

            let root = d3.hierarchy(treeData);
            root.x0 = height / 2;
            root.y0 = 0;

            // Collapse all children initially except first level
            if (root.children) {{
                root.children.forEach(collapse);
            }}

            update(root);

            function collapse(d) {{
                if (d.children) {{
                    d._children = d.children;
                    d._children.forEach(collapse);
                    d.children = null;
                }}
            }}

            function expand(d) {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }}

            function update(source) {{
                const treeData = tree(root);
                const nodes = treeData.descendants();
                const links = treeData.descendants().slice(1);

                nodes.forEach(d => {{ d.y = d.depth * 200; }});

                // Nodes
                const node = g.selectAll("g.node")
                    .data(nodes, d => d.id || (d.id = ++i));

                const nodeEnter = node.enter().append("g")
                    .attr("class", d => {{
                        let classes = "node";
                        if (d.data.is_searched) classes += " searched";
                        if (d.data.node_type === "parent") classes += " parent";
                        if (d._children) classes += " collapsed";
                        return classes;
                    }})
                    .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                    .on("click", click);

                nodeEnter.append("circle")
                    .attr("r", 6);

                nodeEnter.append("text")
                    .attr("dy", ".35em")
                    .attr("x", d => d.children || d._children ? -13 : 13)
                    .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                    .text(d => d.data.name)
                    .style("fill-opacity", 1e-6);

                const nodeUpdate = nodeEnter.merge(node);

                nodeUpdate.transition()
                    .duration(750)
                    .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

                nodeUpdate.select("text")
                    .style("fill-opacity", 1);

                const nodeExit = node.exit().transition()
                    .duration(750)
                    .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                    .remove();

                nodeExit.select("text")
                    .style("fill-opacity", 1e-6);

                // Links
                const link = g.selectAll("path.link")
                    .data(links, d => d.id);

                const linkEnter = link.enter().insert("path", "g")
                    .attr("class", "link")
                    .attr("d", d => {{
                        const o = {{x: source.x0, y: source.y0}};
                        return diagonal(o, o);
                    }});

                const linkUpdate = linkEnter.merge(link);

                linkUpdate.transition()
                    .duration(750)
                    .attr("d", d => diagonal(d, d.parent));

                link.exit().transition()
                    .duration(750)
                    .attr("d", d => {{
                        const o = {{x: source.x, y: source.y}};
                        return diagonal(o, o);
                    }})
                    .remove();

                nodes.forEach(d => {{
                    d.x0 = d.x;
                    d.y0 = d.y;
                }});
            }}

            function diagonal(s, d) {{
                return `M ${{s.y}} ${{s.x}}
                        C ${{(s.y + d.y) / 2}} ${{s.x}},
                          ${{(s.y + d.y) / 2}} ${{d.x}},
                          ${{d.y}} ${{d.x}}`;
            }}

            function click(event, d) {{
                if (d.children) {{
                    d._children = d.children;
                    d.children = null;
                }} else {{
                    d.children = d._children;
                    d._children = null;
                }}
                update(d);
            }}

            let i = 0;

            function expandAll() {{
                root.descendants().forEach(expand);
                update(root);
            }}

            function collapseAll() {{
                if (root.children) {{
                    root.children.forEach(collapse);
                }}
                update(root);
            }}

            function expandToLevel(level) {{
                root.descendants().forEach(d => {{
                    if (d.depth < level) {{
                        expand(d);
                    }} else {{
                        collapse(d);
                    }}
                }});
                update(root);
            }}

            function resetView() {{
                collapseAll();
            }}
        </script>
    </body>
    </html>
    """

    return html


def create_simple_treemap(
    G: nx.MultiDiGraph,
    title: str = "Entity Treemap (Simple)",
    height: int = 800
) -> go.Figure:
    """
    Create a simple flat treemap without country grouping.
    Fallback for when complex hierarchical treemap doesn't render.
    """
    print(f"[SIMPLE_TREEMAP DEBUG] Creating simple treemap for {G.number_of_nodes()} nodes")

    labels = []
    parents = []
    values = []
    colors = []
    hover_texts = []

    # Simple flat structure - all nodes under root
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    if not root_nodes:
        parent_nodes = [n for n, attrs in G.nodes(data=True) if attrs.get('node_type') == 'parent']
        root_nodes = parent_nodes if parent_nodes else [list(G.nodes())[0]]

    root_node = root_nodes[0]

    # Add root
    labels.append(root_node)
    parents.append("")
    values.append(1)
    colors.append('#0ea5e9')
    hover_texts.append(f"<b>{root_node}</b><br>Parent Company")

    # Add all other nodes as direct children of root
    for node, attrs in G.nodes(data=True):
        if node == root_node:
            continue

        labels.append(node)
        parents.append(root_node)
        values.append(1)

        is_searched = attrs.get('is_searched_entity', False)
        if is_searched:
            colors.append('#ef4444')
        else:
            colors.append('#10b981')

        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        node_type = attrs.get('node_type', 'unknown')
        hover_text = f"<b>{node}</b><br>Type: {node_type}<br>Jurisdiction: {jurisdiction}"
        hover_texts.append(hover_text)

    print(f"[SIMPLE_TREEMAP DEBUG] Created {len(labels)} items")

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(width=2, color='#0b1121')),
        text=labels,
        hovertext=hover_texts,
        hoverinfo='text',
        textposition='middle center',
        textfont=dict(size=10, color='white')
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20, color='white')),
        plot_bgcolor='#0b1121',
        paper_bgcolor='#0b1121',
        height=height,
        margin=dict(t=60, l=10, r=10, b=10)
    )

    return fig


def create_treemap_visualization(
    G: nx.MultiDiGraph,
    title: str = "Entity Treemap",
    height: int = 800
) -> go.Figure:
    """
    Create a treemap showing hierarchical structure as nested rectangles.
    Groups by country first, then shows subsidiaries within each country.
    Size represents number of subsidiaries, color represents country.

    Args:
        G: NetworkX graph
        title: Title for the visualization
        height: Height in pixels

    Returns:
        Plotly Figure with treemap
    """
    # Debug logging
    print(f"[TREEMAP DEBUG] Creating treemap for graph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Build country-first hierarchy
    labels = []
    parents = []
    values = []
    colors = []
    hover_texts = []
    ids = []

    # Extended color palette for countries
    COUNTRY_COLORS = {
        'United States': '#10b981',
        'USA': '#10b981',
        'China': '#a855f7',
        'Singapore': '#f59e0b',
        'Hong Kong': '#ec4899',
        'United Kingdom': '#06b6d4',
        'UK': '#06b6d4',
        'Japan': '#8b5cf6',
        'Germany': '#14b8a6',
        'France': '#f97316',
        'Canada': '#84cc16',
        'Australia': '#6366f1',
        'India': '#22c55e',
        'Netherlands': '#d946ef',
        'Switzerland': '#fb923c',
        'Italy': '#facc15',
        'Spain': '#2dd4bf',
        'South Korea': '#c084fc',
        'Brazil': '#4ade80',
        'Mexico': '#f472b6',
    }

    # Find root node (parent company)
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"[TREEMAP DEBUG] Root nodes (in_degree=0): {root_nodes}")

    if not root_nodes:
        parent_nodes = [n for n, attrs in G.nodes(data=True) if attrs.get('node_type') == 'parent']
        print(f"[TREEMAP DEBUG] Parent nodes by type: {parent_nodes}")
        root_nodes = parent_nodes if parent_nodes else [list(G.nodes())[0]]

    root_node = root_nodes[0]
    root_attrs = G.nodes[root_node]
    print(f"[TREEMAP DEBUG] Selected root node: {root_node}")

    # Add root node
    labels.append(root_node)
    parents.append("")
    values.append(1)  # Will be calculated later
    ids.append(root_node)
    colors.append('#0ea5e9')  # Parent company color (cyan)

    root_jurisdiction = root_attrs.get('jurisdiction', 'Unknown')
    hover_text = f"<b>{root_node}</b><br>"
    hover_text += f"Type: Parent Company<br>"
    hover_text += f"Jurisdiction: {root_jurisdiction}<br>"
    hover_text += f"Total Subsidiaries: {G.number_of_nodes() - 1}"
    hover_texts.append(hover_text)

    # Group subsidiaries by country
    subsidiaries_by_country = {}
    for node, attrs in G.nodes(data=True):
        if node == root_node:
            continue

        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        if jurisdiction not in subsidiaries_by_country:
            subsidiaries_by_country[jurisdiction] = []

        subsidiaries_by_country[jurisdiction].append((node, attrs))

    # Add country group nodes
    for country, entities in subsidiaries_by_country.items():
        country_id = f"country_{country}"
        country_color = COUNTRY_COLORS.get(country, '#64748b')

        # Add country group node
        labels.append(f"📍 {country}")
        parents.append(root_node)
        values.append(len(entities))
        ids.append(country_id)
        colors.append(country_color)

        country_hover = f"<b>{country}</b><br>"
        country_hover += f"Entities: {len(entities)}"
        hover_texts.append(country_hover)

        # Add entities within this country
        for entity_name, attrs in entities:
            node_type = attrs.get('node_type', 'unknown')
            num_children = len(list(G.successors(entity_name)))
            is_searched = attrs.get('is_searched_entity', False)

            # Entity color - use country color but slightly different shade
            if is_searched:
                entity_color = '#ef4444'  # Red for searched entity
            else:
                entity_color = country_color

            labels.append(entity_name)
            parents.append(country_id)
            values.append(max(num_children, 1))  # At least 1 for leaf nodes
            ids.append(entity_name)
            colors.append(entity_color)

            # Hover text
            entity_hover = f"<b>{entity_name}</b><br>"
            entity_hover += f"Type: {node_type.title()}<br>"
            entity_hover += f"Jurisdiction: {country}<br>"
            if 'ownership_pct' in attrs and attrs['ownership_pct']:
                entity_hover += f"Ownership: {attrs['ownership_pct']:.1f}%<br>"
            entity_hover += f"Direct Subsidiaries: {num_children}"
            if is_searched:
                entity_hover += "<br>🔍 MAIN SEARCH ENTITY"
            hover_texts.append(entity_hover)

    print(f"[TREEMAP DEBUG] Total items in treemap: {len(labels)}")
    print(f"[TREEMAP DEBUG] Countries found: {len(subsidiaries_by_country)}")
    print(f"[TREEMAP DEBUG] First 5 labels: {labels[:5]}")
    print(f"[TREEMAP DEBUG] First 5 parents: {parents[:5]}")
    print(f"[TREEMAP DEBUG] First 5 values: {values[:5]}")

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        ids=ids,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='#0b1121')
        ),
        text=labels,
        hovertext=hover_texts,
        hoverinfo='text',
        textposition='middle center',
        textfont=dict(size=11, color='white', family='Inter'),
        branchvalues="total"  # Important: use total value for branches
    ))

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        plot_bgcolor='#0b1121',
        paper_bgcolor='#0b1121',
        height=height,
        width=None,  # Let Streamlit handle width
        margin=dict(t=60, l=10, r=10, b=10),
        autosize=True
    )

    print(f"[TREEMAP DEBUG] Figure created with {len(fig.data)} data traces")
    print(f"[TREEMAP DEBUG] Treemap has {len(labels)} labels in total")

    return fig


def create_sunburst_chart(
    G: nx.MultiDiGraph,
    title: str = "Entity Sunburst",
    height: int = 800
) -> go.Figure:
    """
    Create a sunburst/radial chart with parent at center.
    Each ring represents a depth level.

    Args:
        G: NetworkX graph
        title: Title for the visualization
        height: Height in pixels

    Returns:
        Plotly Figure with sunburst chart
    """
    # Build sunburst data
    labels = []
    parents = []
    values = []
    colors = []
    hover_texts = []

    SEARCHED_ENTITY_COLOR = '#ef4444'
    PARENT_COMPANY_COLOR = '#0ea5e9'

    for node, attrs in G.nodes(data=True):
        labels.append(node)

        # Find parent
        predecessors = list(G.predecessors(node))
        if predecessors:
            parents.append(predecessors[0])
        else:
            parents.append("")  # Root

        # Value (uniform for now, could be ownership %)
        values.append(1)

        # Color
        is_searched = attrs.get('is_searched_entity', False)
        node_type = attrs.get('node_type', 'unknown')

        if is_searched:
            color = SEARCHED_ENTITY_COLOR
        elif node_type == 'parent':
            color = PARENT_COMPANY_COLOR
        else:
            color = '#10b981'  # Default green

        colors.append(color)

        # Hover text
        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        level = attrs.get('level', 0)
        hover_text = f"<b>{node}</b><br>"
        hover_text += f"Type: {node_type.title()}<br>"
        hover_text += f"Level: {level}<br>"
        hover_text += f"Jurisdiction: {jurisdiction}"
        hover_texts.append(hover_text)

    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(width=2, color='#0b1121')
        ),
        hovertext=hover_texts,
        hoverinfo='text',
        textfont=dict(size=12, color='white')
    ))

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        plot_bgcolor='#0b1121',
        paper_bgcolor='#0b1121',
        height=height,
        margin=dict(t=60, l=10, r=10, b=10)
    )

    return fig


def graph_to_tree_json(G: nx.MultiDiGraph) -> Dict:
    """
    Convert NetworkX graph to hierarchical JSON structure for D3.js tree.

    Args:
        G: NetworkX graph

    Returns:
        Hierarchical dictionary representing the tree
    """
    # Find root node (node with no predecessors)
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]

    if not root_nodes:
        # If no clear root, use parent node
        parent_nodes = [n for n, attrs in G.nodes(data=True)
                       if attrs.get('node_type') == 'parent']
        root_nodes = parent_nodes if parent_nodes else [list(G.nodes())[0]]

    def build_tree(node):
        """Recursively build tree structure"""
        attrs = G.nodes[node]

        tree_node = {
            'name': node,
            'node_type': attrs.get('node_type', 'unknown'),
            'jurisdiction': attrs.get('jurisdiction', 'Unknown'),
            'level': attrs.get('level', 0),
            'is_searched': attrs.get('is_searched_entity', False)
        }

        # Get children
        children = list(G.successors(node))
        if children:
            tree_node['children'] = [build_tree(child) for child in children]

        return tree_node

    # Build tree from root
    tree = build_tree(root_nodes[0])

    return tree


def create_filtered_network_view(
    G: nx.MultiDiGraph,
    max_level: int = 2,
    countries: Optional[List[str]] = None,
    title: str = "Filtered Network View"
) -> nx.MultiDiGraph:
    """
    Create a filtered version of the graph showing only specified levels and countries.
    Use this with the existing Neo4j visualization for a cleaner view.

    Args:
        G: Original graph
        max_level: Maximum depth level to show
        countries: List of countries to include (None = all)
        title: Title for the view

    Returns:
        Filtered NetworkX graph
    """
    filtered_G = nx.MultiDiGraph()

    # Filter nodes
    for node, attrs in G.nodes(data=True):
        level = attrs.get('level', 0)
        jurisdiction = attrs.get('jurisdiction', 'Unknown')

        # Check level filter
        if level > max_level:
            continue

        # Check country filter
        if countries and jurisdiction not in countries and attrs.get('node_type') != 'parent':
            continue

        # Add node to filtered graph
        filtered_G.add_node(node, **attrs)

    # Add edges where both nodes exist in filtered graph
    for u, v, key, attrs in G.edges(data=True, keys=True):
        if u in filtered_G.nodes() and v in filtered_G.nodes():
            filtered_G.add_edge(u, v, key=key, **attrs)

    return filtered_G
