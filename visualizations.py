"""
Visualization Module for Entity Relationship Diagrams and Geographic Maps

This module creates interactive visualizations using:
- PyVis for Neo4j-style interactive network diagrams
- Plotly for network diagrams
- Folium for geographic maps with entity locations
"""

import networkx as nx
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from typing import Dict, List, Optional, Tuple
import logging
from pyvis.network import Network
import tempfile
import os

# Cache for geocoded locations to avoid repeated API calls
GEOCODE_CACHE = {}

# Last geocoding request timestamp for rate limiting
LAST_GEOCODE_TIME = 0

# Initialize geocoder (with user agent required by Nominatim)
geolocator = Nominatim(user_agent="entity_background_check_bot")

# Fallback coordinates for common countries/jurisdictions
# This avoids hitting the API for frequently used locations
COUNTRY_COORDINATES = {
    'United States': (37.0902, -95.7129),
    'USA': (37.0902, -95.7129),
    'United Kingdom': (55.3781, -3.4360),
    'UK': (55.3781, -3.4360),
    'China': (35.8617, 104.1954),
    'India': (20.5937, 78.9629),
    'Singapore': (1.3521, 103.8198),
    'Hong Kong': (22.3193, 114.1694),
    'Japan': (36.2048, 138.2529),
    'Germany': (51.1657, 10.4515),
    'France': (46.2276, 2.2137),
    'Canada': (56.1304, -106.3468),
    'Australia': (-25.2744, 133.7751),
    'Brazil': (-14.2350, -51.9253),
    'Netherlands': (52.1326, 5.2913),
    'Switzerland': (46.8182, 8.2275),
    'Italy': (41.8719, 12.5674),
    'Spain': (40.4637, -3.7492),
    'Mexico': (23.6345, -102.5528),
    'South Korea': (35.9078, 127.7669),
    'Russia': (61.5240, 105.3188),
    'Ireland': (53.4129, -8.2439),
    'Luxembourg': (49.8153, 6.1296),
    'Belgium': (50.5039, 4.4699),
    'Sweden': (60.1282, 18.6435),
    'Norway': (60.4720, 8.4689),
    'Denmark': (56.2639, 9.5018),
    'Finland': (61.9241, 25.7482),
    'Poland': (51.9194, 19.1451),
    'Austria': (47.5162, 14.5501),
    'Czech Republic': (49.8175, 15.4730),
    'Portugal': (39.3999, -8.2245),
    'Greece': (39.0742, 21.8243),
    'Turkey': (38.9637, 35.2433),
    'Israel': (31.0461, 34.8516),
    'United Arab Emirates': (23.4241, 53.8478),
    'UAE': (23.4241, 53.8478),
    'Saudi Arabia': (23.8859, 45.0792),
    'South Africa': (-30.5595, 22.9375),
    'New Zealand': (-40.9006, 174.8860),
    'Argentina': (-38.4161, -63.6167),
    'Chile': (-35.6751, -71.5430),
    'Colombia': (4.5709, -74.2973),
    'Malaysia': (4.2105, 101.9758),
    'Thailand': (15.8700, 100.9925),
    'Vietnam': (14.0583, 108.2772),
    'Philippines': (12.8797, 121.7740),
    'Indonesia': (-0.7893, 113.9213),
    'Taiwan': (23.6978, 120.9605),
    'Cayman Islands': (19.3133, -81.2546),
    'British Virgin Islands': (18.4207, -64.6399),
    'Bermuda': (32.3078, -64.7505),
    'Jersey': (49.2144, -2.1312),
    'Guernsey': (49.4657, -2.5853),
    'Isle of Man': (54.2361, -4.5481),
    'Mauritius': (-20.3484, 57.5522),
    'Seychelles': (-4.6796, 55.4920),
    'Panama': (8.5380, -80.7821),
    'Bahamas': (25.0343, -77.3963)
}


def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a location string to latitude/longitude coordinates.
    Uses caching and fallback coordinates to avoid API rate limits.

    Args:
        location: Location string (country, jurisdiction)

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    global LAST_GEOCODE_TIME

    # Check cache first
    if location in GEOCODE_CACHE:
        return GEOCODE_CACHE[location]

    # Handle special cases and normalize
    location_normalized = location.strip()
    if not location_normalized or location_normalized.lower() in ['unknown', 'n/a', '']:
        return None

    # Check fallback coordinates first (avoid API calls for common countries)
    if location_normalized in COUNTRY_COORDINATES:
        coords = COUNTRY_COORDINATES[location_normalized]
        GEOCODE_CACHE[location] = coords
        return coords

    try:
        # Enforce rate limit: wait at least 1.5 seconds between requests
        current_time = time.time()
        time_since_last = current_time - LAST_GEOCODE_TIME
        if time_since_last < 1.5:
            time.sleep(1.5 - time_since_last)

        LAST_GEOCODE_TIME = time.time()

        geocode_result = geolocator.geocode(location_normalized, timeout=10)

        if geocode_result:
            coords = (geocode_result.latitude, geocode_result.longitude)
            GEOCODE_CACHE[location] = coords
            return coords
        else:
            GEOCODE_CACHE[location] = None
            return None

    except Exception as e:
        # Handle rate limiting (429) and other errors gracefully
        if '429' in str(e) or 'rate limit' in str(e).lower():
            logging.warning(f"Rate limit hit for {location}, using fallback if available")
        else:
            logging.warning(f"Geocoding failed for {location}: {e}")

        GEOCODE_CACHE[location] = None
        return None


def create_interactive_network(
    G: nx.MultiDiGraph,
    title: str = "Entity Relationship Network",
    height: str = "700px"
) -> str:
    """
    Create a Neo4j-style interactive network diagram using PyVis.

    This creates a physics-based, draggable, interactive network visualization
    similar to Neo4j's graph database interface with country-based clustering.

    Args:
        G: NetworkX graph to visualize
        title: Title for the diagram
        height: Height of the visualization (e.g., "700px")

    Returns:
        HTML string containing the interactive network
    """
    # Define special colors
    SEARCHED_ENTITY_COLOR = '#ef4444'  # Bright red for main search entity
    PARENT_COMPANY_COLOR = '#0ea5e9'   # Bright cyan for parent companies

    # Country color palette (distinct, accessible colors)
    COUNTRY_COLORS = [
        '#10b981',  # Green
        '#a855f7',  # Purple
        '#f59e0b',  # Orange
        '#eab308',  # Yellow
        '#ec4899',  # Pink
        '#06b6d4',  # Cyan
        '#8b5cf6',  # Violet
        '#14b8a6',  # Teal
        '#f97316',  # Deep Orange
        '#84cc16',  # Lime
        '#6366f1',  # Indigo
        '#22c55e',  # Light Green
        '#d946ef',  # Fuchsia
        '#fb923c',  # Light Orange
        '#facc15',  # Amber
        '#2dd4bf',  # Light Teal
        '#c084fc',  # Light Purple
        '#4ade80',  # Emerald
        '#f472b6',  # Light Pink
        '#fbbf24'   # Gold
    ]

    # Collect all unique countries/jurisdictions from the graph
    countries = set()
    for node, attrs in G.nodes(data=True):
        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        if jurisdiction and jurisdiction != 'Unknown':
            countries.add(jurisdiction)

    # Create country-to-color mapping
    country_to_color = {}
    for idx, country in enumerate(sorted(countries)):
        country_to_color[country] = COUNTRY_COLORS[idx % len(COUNTRY_COLORS)]

    # Add a default color for unknown jurisdictions
    country_to_color['Unknown'] = '#64748b'  # Gray

    # Create hierarchical layout positions based on node depth/level
    # Group nodes by their level in the hierarchy
    import math
    import random

    nodes_by_level = {}
    max_level = 0

    for node, attrs in G.nodes(data=True):
        # Get level from node attributes (default to 0 for parent, 1 for others)
        level = attrs.get('level', 0)
        node_type = attrs.get('node_type', 'unknown')

        # Parent nodes should be at level 0
        if node_type == 'parent':
            level = 0
        # Directors and shareholders at a separate level
        elif node_type in ['director', 'shareholder']:
            level = max_level + 1  # Place at bottom

        if level not in nodes_by_level:
            nodes_by_level[level] = []

        nodes_by_level[level].append(node)
        max_level = max(max_level, level)

    # Calculate positions for hierarchical layout
    node_positions = {}
    vertical_spacing = 300  # Vertical distance between levels
    horizontal_spacing = 200  # Horizontal spacing between nodes at same level

    for level, nodes in nodes_by_level.items():
        num_nodes = len(nodes)
        # Calculate total width needed for this level
        total_width = (num_nodes - 1) * horizontal_spacing if num_nodes > 1 else 0

        # Center this level horizontally
        start_x = -total_width / 2

        # Y position based on level (top to bottom)
        y = -level * vertical_spacing

        # Position each node at this level
        for idx, node in enumerate(sorted(nodes)):  # Sort for consistency
            x = start_x + (idx * horizontal_spacing)
            node_positions[node] = (x, y)

    # Create PyVis network
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0b1121",  # Match dark theme
        font_color="#e2e8f0",
        directed=True
    )

    # Configure physics for hierarchical layout with dynamics
    # Use hierarchical repulsion to maintain vertical structure
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "hierarchicalRepulsion": {
                "centralGravity": 0.0,
                "springLength": 150,
                "springConstant": 0.01,
                "nodeDistance": 180,
                "damping": 0.09,
                "avoidOverlap": 1
            },
            "maxVelocity": 50,
            "minVelocity": 0.1,
            "solver": "hierarchicalRepulsion",
            "timestep": 0.35,
            "stabilization": {
                "enabled": true,
                "iterations": 250,
                "updateInterval": 25,
                "onlyDynamicEdges": false,
                "fit": true
            }
        },
        "layout": {
            "hierarchical": {
                "enabled": false,
                "levelSeparation": 300,
                "nodeSpacing": 200,
                "treeSpacing": 250,
                "blockShifting": true,
                "edgeMinimization": true,
                "parentCentralization": true,
                "direction": "UD",
                "sortMethod": "directed"
            }
        },
        "interaction": {
            "hover": true,
            "dragNodes": true,
            "dragView": true,
            "zoomView": true,
            "navigationButtons": true,
            "keyboard": {
                "enabled": true
            },
            "tooltipDelay": 200
        },
        "nodes": {
            "font": {
                "size": 14,
                "color": "#ffffff",
                "face": "Inter"
            },
            "borderWidth": 2,
            "shadow": {
                "enabled": true,
                "color": "rgba(0,0,0,0.5)",
                "size": 10
            }
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "smooth": {
                "enabled": true,
                "type": "cubicBezier",
                "forceDirection": "vertical",
                "roundness": 0.4
            },
            "shadow": {
                "enabled": false
            }
        }
    }
    """)

    # Add nodes with styling based on country and special node types
    for node, attrs in G.nodes(data=True):
        node_type = attrs.get('node_type', 'unknown')
        jurisdiction = attrs.get('jurisdiction', 'Unknown')
        size = attrs.get('size', 20)

        # Determine node color based on priority:
        # 1. Main search entity (highest priority)
        # 2. Parent company
        # 3. Country-based color
        is_searched_entity = attrs.get('is_searched_entity', False)

        if is_searched_entity:
            color = SEARCHED_ENTITY_COLOR
            size = size * 1.2  # Make searched entity slightly larger
        elif node_type == 'parent':
            color = PARENT_COMPANY_COLOR
        else:
            color = country_to_color.get(jurisdiction, '#64748b')

        # Create hover title with details
        title_text = f"<b>{node}</b><br>"
        title_text += f"Type: {node_type.title()}<br>"

        if jurisdiction:
            title_text += f"Jurisdiction: {jurisdiction}<br>"
        if 'ownership_pct' in attrs and attrs['ownership_pct']:
            title_text += f"Ownership: {attrs['ownership_pct']:.1f}%<br>"
        if 'title' in attrs and attrs['title']:
            title_text += f"Title: {attrs['title']}<br>"
        if 'nationality' in attrs and attrs['nationality']:
            title_text += f"Nationality: {attrs['nationality']}<br>"
        if 'sanctions_hit' in attrs and attrs['sanctions_hit']:
            title_text += f"⚠️ SANCTIONS ALERT<br>"

        if is_searched_entity:
            title_text += f"<br>🔍 MAIN SEARCH ENTITY<br>"

        # Get hierarchical position for this node
        base_x, base_y = node_positions.get(node, (0, 0))

        # Add small random offset to prevent exact overlap of nodes at same level
        offset_x = random.uniform(-30, 30)
        offset_y = random.uniform(-20, 20)

        # Get level for display in tooltip
        level = attrs.get('level', 0)
        if node_type == 'parent':
            level = 0
        if level > 0:
            title_text += f"Depth Level: {level}<br>"

        # Add node with PyVis using hierarchical positioning
        net.add_node(
            node,
            label=node,
            color=color,
            size=size,
            title=title_text,
            borderWidth=2,
            borderWidthSelected=4,
            level=level,  # Set level for hierarchical layout
            x=base_x + offset_x,  # Initial x position
            y=base_y + offset_y,  # Initial y position
            physics=True  # Allow physics to refine position while maintaining structure
        )

    # Add edges with styling
    for u, v, key, attrs in G.edges(data=True, keys=True):
        relationship = attrs.get('relationship', '')
        edge_color = attrs.get('edge_color', '#64748b')
        edge_width = attrs.get('edge_width', 1)

        # Create edge title
        edge_title = f"{u} → {v}<br>{relationship}"
        if 'ownership_pct' in attrs and attrs['ownership_pct'] is not None:
            edge_title += f"<br>Ownership: {attrs['ownership_pct']:.1f}%"
        elif 'amount' in attrs and attrs['amount'] is not None:
            edge_title += f"<br>Amount: {attrs.get('currency', 'USD')} {attrs['amount']:,.0f}"

        net.add_edge(
            u,
            v,
            title=edge_title,
            color=edge_color,
            width=edge_width * 2,  # Make edges more visible
            arrows="to"
        )

    # Generate HTML
    html = net.generate_html()

    # Create legend HTML with country colors and hierarchy info
    legend_items = []

    # Add hierarchy information
    legend_items.append('<div style="margin-bottom: 12px; font-weight: bold; color: #3b82f6;">📊 Hierarchical View</div>')
    legend_items.append('<div style="margin-bottom: 8px; font-size: 11px; color: #94a3b8;">Top to Bottom: Parent → Subsidiaries by Depth</div>')

    # Add separator
    legend_items.append('<hr style="border-color: #475569; margin: 10px 0;">')

    # Add special entity types first
    legend_items.append('<div style="margin-bottom: 8px; font-weight: bold;">Special Entities:</div>')
    legend_items.append(f'<div style="margin-bottom: 8px;"><span style="display: inline-block; width: 12px; height: 12px; background-color: {SEARCHED_ENTITY_COLOR}; border-radius: 50%; margin-right: 8px;"></span><b>Main Search Entity</b></div>')
    legend_items.append(f'<div style="margin-bottom: 8px;"><span style="display: inline-block; width: 12px; height: 12px; background-color: {PARENT_COMPANY_COLOR}; border-radius: 50%; margin-right: 8px;"></span><b>Parent Company</b></div>')

    # Add separator
    legend_items.append('<hr style="border-color: #475569; margin: 10px 0;">')

    # Add country colors
    legend_items.append('<div style="margin-bottom: 8px; font-weight: bold;">Countries/Jurisdictions:</div>')
    for country in sorted(countries):
        color = country_to_color[country]
        legend_items.append(f'<div style="margin-bottom: 6px; font-size: 12px;"><span style="display: inline-block; width: 10px; height: 10px; background-color: {color}; border-radius: 50%; margin-right: 6px;"></span>{country}</div>')

    # Add level information
    if max_level > 0:
        legend_items.append('<hr style="border-color: #475569; margin: 10px 0;">')
        legend_items.append('<div style="margin-bottom: 8px; font-weight: bold;">Depth Levels:</div>')
        for level in range(0, max_level + 1):
            if level in nodes_by_level:
                count = len(nodes_by_level[level])
                level_name = "Parent" if level == 0 else f"Level {level}"
                legend_items.append(f'<div style="margin-bottom: 4px; font-size: 11px;">▸ {level_name}: {count} node(s)</div>')

    legend_html = '\n'.join(legend_items)

    # Add custom CSS for dark theme and styling, plus legend
    html = html.replace(
        '</head>',
        f'''
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #0b1121;
            }}
            #mynetwork {{
                border: 2px solid #334155;
                border-radius: 8px;
            }}
            .vis-network {{
                outline: none;
            }}
            .vis-tooltip {{
                background-color: #1e293b !important;
                border: 1px solid #475569 !important;
                color: #e2e8f0 !important;
                font-family: 'Inter', sans-serif !important;
                padding: 10px !important;
                border-radius: 6px !important;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            }}
            .vis-navigation {{
                background-color: rgba(30, 41, 59, 0.9) !important;
                border: 1px solid #475569 !important;
            }}
            .vis-button {{
                background-color: #334155 !important;
                color: #e2e8f0 !important;
            }}
            .vis-button:hover {{
                background-color: #475569 !important;
            }}
            #country-legend {{
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: rgba(30, 41, 59, 0.95);
                border: 2px solid #475569;
                border-radius: 8px;
                padding: 15px;
                color: #e2e8f0;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                max-height: 80vh;
                overflow-y: auto;
                z-index: 1000;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                min-width: 200px;
            }}
            #country-legend::-webkit-scrollbar {{
                width: 8px;
            }}
            #country-legend::-webkit-scrollbar-track {{
                background: #1e293b;
                border-radius: 4px;
            }}
            #country-legend::-webkit-scrollbar-thumb {{
                background: #475569;
                border-radius: 4px;
            }}
            #country-legend::-webkit-scrollbar-thumb:hover {{
                background: #64748b;
            }}
        </style>
        </head>
        '''
    )

    # Add legend to the HTML body
    html = html.replace(
        '<body>',
        f'''<body>
        <div id="country-legend">
            <h3 style="margin-top: 0; margin-bottom: 12px; color: #3b82f6;">Legend</h3>
            {legend_html}
        </div>
        '''
    )

    return html


def create_network_diagram(
    G: nx.MultiDiGraph,
    layout: str = 'force',
    title: str = "Entity Relationship Network"
) -> go.Figure:
    """
    Create an interactive network diagram using Plotly.

    Args:
        G: NetworkX graph to visualize
        layout: Layout algorithm ('force', 'hierarchical', 'circular')
        title: Title for the diagram

    Returns:
        Plotly Figure object
    """
    # Calculate layout positions
    if layout == 'hierarchical':
        # Use graphviz_layout if available, otherwise fall back to spring
        try:
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot')
        except:
            pos = nx.spring_layout(G, k=2, iterations=50)
    elif layout == 'circular':
        pos = nx.circular_layout(G)
    else:  # force-directed (default)
        pos = nx.spring_layout(G, k=2, iterations=50)

    # Create edge traces
    edge_traces = []

    for u, v, key, attrs in G.edges(data=True, keys=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]

        edge_color = attrs.get('edge_color', '#64748b')
        edge_width = attrs.get('edge_width', 1)
        relationship = attrs.get('relationship', '')

        # Create edge trace
        edge_trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=edge_width, color=edge_color),
            hoverinfo='text',
            text=f"{u} → {v}<br>{relationship}",
            showlegend=False
        )
        edge_traces.append(edge_trace)

    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_hover = []

    for node, attrs in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        # Node attributes
        node_type = attrs.get('node_type', 'unknown')
        entity_type = attrs.get('entity_type', 'unknown')
        color = attrs.get('color', '#64748b')
        size = attrs.get('size', 20)

        node_color.append(color)
        node_size.append(size)
        node_text.append(node)

        # Create hover text with details
        hover_text = f"<b>{node}</b><br>"
        hover_text += f"Type: {node_type.title()}<br>"

        if 'jurisdiction' in attrs:
            hover_text += f"Jurisdiction: {attrs['jurisdiction']}<br>"
        if 'ownership_pct' in attrs and attrs['ownership_pct']:
            hover_text += f"Ownership: {attrs['ownership_pct']:.1f}%<br>"
        if 'title' in attrs and attrs['title']:
            hover_text += f"Title: {attrs['title']}<br>"
        if 'nationality' in attrs and attrs['nationality']:
            hover_text += f"Nationality: {attrs['nationality']}<br>"
        if 'sanctions_hit' in attrs and attrs['sanctions_hit']:
            hover_text += f"⚠️ SANCTIONS ALERT<br>"

        node_hover.append(hover_text)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=10, color='white'),
        hoverinfo='text',
        hovertext=node_hover,
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color='white')
        ),
        showlegend=False
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])

    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='white')
        ),
        showlegend=False,
        hovermode='closest',
        plot_bgcolor='#0b1121',
        paper_bgcolor='#0b1121',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=700,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Add legend manually
    legend_items = [
        {'color': '#3b82f6', 'label': 'Parent Company'},
        {'color': '#10b981', 'label': 'Subsidiary'},
        {'color': '#a855f7', 'label': 'Sister Company'},
        {'color': '#f59e0b', 'label': 'Director'},
        {'color': '#eab308', 'label': 'Shareholder'}
    ]

    # Add legend annotations
    legend_y = 0.95
    for item in legend_items:
        fig.add_annotation(
            xref='paper', yref='paper',
            x=0.02, y=legend_y,
            text=f"<span style='color:{item['color']}'>●</span> {item['label']}",
            showarrow=False,
            font=dict(size=12, color='white'),
            align='left',
            xanchor='left'
        )
        legend_y -= 0.05

    return fig


def create_geographic_map(
    G: nx.MultiDiGraph,
    title: str = "Entity Geographic Distribution"
) -> folium.Map:
    """
    Create an interactive geographic map showing entity locations.

    Args:
        G: NetworkX graph with entity data
        title: Title for the map

    Returns:
        Folium Map object
    """
    # Collect entities with jurisdictions
    entities_by_location = {}

    for node, attrs in G.nodes(data=True):
        jurisdiction = attrs.get('jurisdiction', 'Unknown')

        if jurisdiction and jurisdiction != 'Unknown':
            if jurisdiction not in entities_by_location:
                entities_by_location[jurisdiction] = []

            entities_by_location[jurisdiction].append({
                'name': node,
                'type': attrs.get('node_type', 'unknown'),
                'entity_type': attrs.get('entity_type', 'unknown'),
                'attrs': attrs
            })

    # Create base map centered on world view
    world_map = folium.Map(
        location=[20, 0],  # Center of world
        zoom_start=2,
        tiles='CartoDB dark_matter'
    )

    # Add title
    title_html = f'''
    <div style="position: fixed;
                top: 10px;
                left: 50px;
                width: 400px;
                height: 50px;
                background-color: rgba(11, 17, 33, 0.9);
                border: 2px solid #3b82f6;
                z-index: 9999;
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 10px;
                border-radius: 5px;">
        {title}
    </div>
    '''
    world_map.get_root().html.add_child(folium.Element(title_html))

    # Geocode locations and add markers
    for location, entities in entities_by_location.items():
        coords = geocode_location(location)

        if coords:
            lat, lon = coords

            # Determine marker color based on entity type
            entity_types = [e['type'] for e in entities]

            if 'parent' in entity_types:
                color = 'blue'
                icon = 'building'
            elif 'subsidiary' in entity_types:
                color = 'green'
                icon = 'building'
            elif 'sister' in entity_types:
                color = 'purple'
                icon = 'building'
            elif 'director' in entity_types:
                color = 'orange'
                icon = 'user'
            elif 'shareholder' in entity_types:
                color = 'yellow'
                icon = 'star'
            else:
                color = 'gray'
                icon = 'info-sign'

            # Create popup content
            popup_html = f"<h4>{location}</h4><hr>"
            popup_html += f"<b>{len(entities)} entities</b><br><br>"

            for entity in entities[:10]:  # Limit to 10 entities per popup
                entity_name = entity['name']
                entity_type = entity['type'].title()
                popup_html += f"<b>{entity_name}</b><br>"
                popup_html += f"<i>{entity_type}</i><br>"

                # Add ownership if available
                if 'ownership_pct' in entity['attrs'] and entity['attrs']['ownership_pct']:
                    popup_html += f"Ownership: {entity['attrs']['ownership_pct']:.1f}%<br>"

                popup_html += "<br>"

            if len(entities) > 10:
                popup_html += f"<i>... and {len(entities) - 10} more</i>"

            # Add marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{location} ({len(entities)} entities)",
                icon=folium.Icon(color=color, icon=icon, prefix='fa')
            ).add_to(world_map)

    # Add connections between entities (for transactions or ownership)
    for u, v, attrs in G.edges(data=True):
        relationship = attrs.get('relationship', '')

        # Only draw lines for ownership and transactions
        if relationship in ['owns', 'transacted_with']:
            u_jurisdiction = G.nodes[u].get('jurisdiction', 'Unknown')
            v_jurisdiction = G.nodes[v].get('jurisdiction', 'Unknown')

            if u_jurisdiction != 'Unknown' and v_jurisdiction != 'Unknown' and u_jurisdiction != v_jurisdiction:
                u_coords = geocode_location(u_jurisdiction)
                v_coords = geocode_location(v_jurisdiction)

                if u_coords and v_coords:
                    line_color = '#3b82f6' if relationship == 'owns' else '#ef4444'
                    line_weight = 2 if relationship == 'owns' else 1

                    folium.PolyLine(
                        locations=[u_coords, v_coords],
                        color=line_color,
                        weight=line_weight,
                        opacity=0.6,
                        popup=f"{u} → {v}<br>{relationship}"
                    ).add_to(world_map)

    # Add legend
    legend_html = '''
    <div style="position: fixed;
                bottom: 50px;
                left: 50px;
                width: 180px;
                background-color: rgba(11, 17, 33, 0.9);
                border: 2px solid #3b82f6;
                z-index: 9999;
                font-size: 12px;
                color: white;
                padding: 10px;
                border-radius: 5px;">
        <h4 style="margin-top: 0;">Legend</h4>
        <p><span style="color: #3b82f6;">●</span> Parent Company</p>
        <p><span style="color: #10b981;">●</span> Subsidiary</p>
        <p><span style="color: #a855f7;">●</span> Sister Company</p>
        <p><span style="color: #f59e0b;">●</span> Director</p>
        <p><span style="color: #eab308;">●</span> Shareholder</p>
    </div>
    '''
    world_map.get_root().html.add_child(folium.Element(legend_html))

    return world_map


def create_3d_network_diagram(
    G: nx.MultiDiGraph,
    title: str = "3D Entity Relationship Network"
) -> go.Figure:
    """
    Create a 3D network diagram using Plotly (optional advanced feature).

    Args:
        G: NetworkX graph to visualize
        title: Title for the diagram

    Returns:
        Plotly Figure object with 3D scatter plot
    """
    # Calculate 3D spring layout
    pos = nx.spring_layout(G, dim=3, k=2, iterations=50)

    # Create edge traces
    edge_traces = []

    for u, v, attrs in G.edges(data=True):
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]

        edge_color = attrs.get('edge_color', '#64748b')
        relationship = attrs.get('relationship', '')

        edge_trace = go.Scatter3d(
            x=[x0, x1, None],
            y=[y0, y1, None],
            z=[z0, z1, None],
            mode='lines',
            line=dict(width=2, color=edge_color),
            hoverinfo='text',
            text=f"{u} → {v}<br>{relationship}",
            showlegend=False
        )
        edge_traces.append(edge_trace)

    # Create node trace
    node_x = []
    node_y = []
    node_z = []
    node_text = []
    node_color = []
    node_size = []
    node_hover = []

    for node, attrs in G.nodes(data=True):
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)

        node_type = attrs.get('node_type', 'unknown')
        color = attrs.get('color', '#64748b')
        size = attrs.get('size', 20)

        node_color.append(color)
        node_size.append(size / 2)  # Scale down for 3D
        node_text.append(node)

        hover_text = f"<b>{node}</b><br>Type: {node_type.title()}"
        node_hover.append(hover_text)

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=8, color='white'),
        hoverinfo='text',
        hovertext=node_hover,
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=1, color='white')
        ),
        showlegend=False
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])

    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=20, color='white')),
        showlegend=False,
        plot_bgcolor='#0b1121',
        paper_bgcolor='#0b1121',
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            zaxis=dict(showgrid=False, zeroline=False, showticklabels=False, showbackground=False),
            bgcolor='#0b1121'
        ),
        height=700,
        margin=dict(l=0, r=0, t=60, b=0)
    )

    return fig
