"""
Graph Builder Module for Entity Relationship Visualization

This module builds NetworkX graphs from entity data including:
- Parent-subsidiary-sister relationships
- Directors and officers
- Major shareholders
- Related party transactions
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple


def build_entity_graph(
    company_name: str,
    subsidiaries: Optional[List[Dict]] = None,
    sisters: Optional[List[Dict]] = None,
    directors: Optional[List[Dict]] = None,
    shareholders: Optional[List[Dict]] = None,
    transactions: Optional[List[Dict]] = None,
    parent_info: Optional[Dict] = None
) -> nx.MultiDiGraph:
    """
    Build a NetworkX MultiDiGraph from entity relationship data.

    Args:
        company_name: Name of the parent/main company
        subsidiaries: List of subsidiary entities
        sisters: List of sister entities
        directors: List of director/officer dictionaries
        shareholders: List of shareholder dictionaries
        transactions: List of transaction dictionaries
        parent_info: Optional dictionary with parent company details (jurisdiction, status, etc.)

    Returns:
        NetworkX MultiDiGraph with nodes and edges representing relationships
    """
    G = nx.MultiDiGraph()

    # Initialize empty lists if None
    subsidiaries = subsidiaries or []
    sisters = sisters or []
    directors = directors or []
    shareholders = shareholders or []
    transactions = transactions or []

    # Add entity nodes (parent, subsidiaries, sisters)
    add_entity_nodes(G, company_name, subsidiaries, sisters, parent_info)

    # Add person nodes (directors, shareholders)
    add_person_nodes(G, directors, shareholders)

    # Add edges (relationships)
    add_edges(G, company_name, subsidiaries, sisters, directors, shareholders, transactions)

    return G


def add_entity_nodes(
    G: nx.MultiDiGraph,
    parent_name: str,
    subsidiaries: List[Dict],
    sisters: List[Dict],
    parent_info: Optional[Dict] = None
) -> None:
    """
    Add entity nodes (parent, subsidiaries, sisters) to the graph.

    Args:
        G: NetworkX graph to modify
        parent_name: Name of parent company
        subsidiaries: List of subsidiary dictionaries
        sisters: List of sister company dictionaries
        parent_info: Optional dictionary with parent company details
    """
    # Add parent node
    parent_jurisdiction = parent_info.get('jurisdiction', 'Unknown') if parent_info else 'Unknown'
    parent_status = parent_info.get('status', 'Active') if parent_info else 'Active'

    G.add_node(
        parent_name,
        node_type='parent',
        entity_type='company',
        jurisdiction=parent_jurisdiction,
        status=parent_status,
        size=40,  # Largest node
        color='#3b82f6'  # Blue
    )

    # Add subsidiary nodes
    for sub in subsidiaries:
        sub_name = sub.get('name', '')
        if sub_name and sub_name not in G.nodes():
            G.add_node(
                sub_name,
                node_type='subsidiary',
                entity_type='company',
                jurisdiction=sub.get('jurisdiction', 'Unknown'),
                status=sub.get('status', 'Unknown'),
                ownership_pct=sub.get('ownership_percentage', 0),
                size=25,  # Medium node
                color='#10b981'  # Green
            )

    # Add sister company nodes
    for sister in sisters:
        sister_name = sister.get('name', '')
        if sister_name and sister_name not in G.nodes():
            G.add_node(
                sister_name,
                node_type='sister',
                entity_type='company',
                jurisdiction=sister.get('jurisdiction', 'Unknown'),
                status=sister.get('status', 'Unknown'),
                ownership_pct=sister.get('ownership_percentage', 0),
                size=25,  # Medium node
                color='#a855f7'  # Purple
            )


def add_person_nodes(
    G: nx.MultiDiGraph,
    directors: List[Dict],
    shareholders: List[Dict]
) -> None:
    """
    Add person nodes (directors, shareholders) to the graph.

    Args:
        G: NetworkX graph to modify
        directors: List of director/officer dictionaries
        shareholders: List of shareholder dictionaries
    """
    # Add director nodes
    for director in directors:
        person_name = director.get('name', '')
        if person_name and person_name not in G.nodes():
            G.add_node(
                person_name,
                node_type='director',
                entity_type='person',
                title=director.get('title', ''),
                nationality=director.get('nationality', 'Unknown'),
                sanctions_hit=director.get('sanctions_hit', 0),
                size=15,  # Small node
                color='#f59e0b'  # Orange
            )

    # Add shareholder nodes (can be people or entities)
    for shareholder in shareholders:
        shareholder_name = shareholder.get('name', '')
        if shareholder_name and shareholder_name not in G.nodes():
            shareholder_type = shareholder.get('type', 'Unknown')

            G.add_node(
                shareholder_name,
                node_type='shareholder',
                entity_type='person' if shareholder_type == 'Individual' else 'company',
                shareholder_type=shareholder_type,
                jurisdiction=shareholder.get('jurisdiction', 'Unknown'),
                ownership_pct=shareholder.get('ownership_percentage', 0),
                voting_rights=shareholder.get('voting_rights', 0),
                sanctions_hit=shareholder.get('sanctions_hit', 0),
                size=20,  # Small-medium node
                color='#eab308'  # Yellow
            )


def add_edges(
    G: nx.MultiDiGraph,
    parent_name: str,
    subsidiaries: List[Dict],
    sisters: List[Dict],
    directors: List[Dict],
    shareholders: List[Dict],
    transactions: List[Dict]
) -> None:
    """
    Add edges (relationships) between nodes in the graph.

    Args:
        G: NetworkX graph to modify
        parent_name: Name of parent company
        subsidiaries: List of subsidiary dictionaries
        sisters: List of sister company dictionaries
        directors: List of director/officer dictionaries
        shareholders: List of shareholder dictionaries
        transactions: List of transaction dictionaries
    """
    # Add parent -> subsidiary edges
    for sub in subsidiaries:
        sub_name = sub.get('name', '')
        if sub_name:
            ownership_pct = sub.get('ownership_percentage', 0)
            G.add_edge(
                parent_name,
                sub_name,
                relationship='owns',
                ownership_pct=ownership_pct,
                edge_color='#3b82f6',
                edge_width=2
            )

    # Add sister relationships (bi-directional)
    for sister in sisters:
        sister_name = sister.get('name', '')
        if sister_name:
            G.add_edge(
                parent_name,
                sister_name,
                relationship='sibling_of',
                edge_color='#a855f7',
                edge_width=1.5
            )
            G.add_edge(
                sister_name,
                parent_name,
                relationship='sibling_of',
                edge_color='#a855f7',
                edge_width=1.5
            )

    # Add director relationships
    for director in directors:
        person_name = director.get('name', '')
        company = director.get('company_name', parent_name)
        if person_name and company in G.nodes():
            G.add_edge(
                person_name,
                company,
                relationship='director_of',
                title=director.get('title', ''),
                edge_color='#f59e0b',
                edge_width=1
            )

    # Add shareholder relationships
    for shareholder in shareholders:
        shareholder_name = shareholder.get('name', '')
        company = shareholder.get('company_name', parent_name)
        if shareholder_name and company in G.nodes():
            ownership_pct = shareholder.get('ownership_percentage', 0)
            G.add_edge(
                shareholder_name,
                company,
                relationship='shareholder_of',
                ownership_pct=ownership_pct,
                voting_rights=shareholder.get('voting_rights', 0),
                edge_color='#eab308',
                edge_width=1.5
            )

    # Add transaction relationships
    for txn in transactions:
        counterparty = txn.get('counterparty', '')
        company = txn.get('company_name', parent_name)

        # Only add transaction edges if counterparty is in the graph
        if counterparty and counterparty in G.nodes() and company in G.nodes():
            amount = txn.get('amount', 0)
            G.add_edge(
                company,
                counterparty,
                relationship='transacted_with',
                transaction_type=txn.get('transaction_type', ''),
                amount=amount,
                currency=txn.get('currency', 'USD'),
                transaction_date=txn.get('transaction_date', ''),
                edge_color='#ef4444',
                edge_width=1
            )


def filter_graph(
    G: nx.MultiDiGraph,
    show_directors: bool = True,
    show_shareholders: bool = True,
    show_transactions: bool = True,
    country_filter: Optional[str] = None
) -> nx.MultiDiGraph:
    """
    Filter graph based on node types and attributes.

    Args:
        G: Original graph
        show_directors: Include director nodes
        show_shareholders: Include shareholder nodes
        show_transactions: Include transaction edges
        country_filter: If specified, only show entities from this country

    Returns:
        Filtered graph
    """
    # Create a copy to avoid modifying original
    filtered_G = G.copy()

    # Remove nodes based on filters
    nodes_to_remove = []

    for node, attrs in G.nodes(data=True):
        node_type = attrs.get('node_type', '')

        # Filter by node type
        if not show_directors and node_type == 'director':
            nodes_to_remove.append(node)
        elif not show_shareholders and node_type == 'shareholder':
            nodes_to_remove.append(node)

        # Filter by country
        if country_filter and country_filter != 'All':
            jurisdiction = attrs.get('jurisdiction', 'Unknown')
            # Keep parent and entities matching filter
            if node_type not in ['parent'] and jurisdiction != country_filter:
                if node_type in ['subsidiary', 'sister']:
                    nodes_to_remove.append(node)

    # Remove filtered nodes
    filtered_G.remove_nodes_from(nodes_to_remove)

    # Remove transaction edges if needed
    if not show_transactions:
        edges_to_remove = []
        for u, v, key, attrs in filtered_G.edges(data=True, keys=True):
            if attrs.get('relationship') == 'transacted_with':
                edges_to_remove.append((u, v, key))
        filtered_G.remove_edges_from(edges_to_remove)

    return filtered_G


def get_graph_statistics(G: nx.MultiDiGraph) -> Dict:
    """
    Calculate statistics about the graph.

    Args:
        G: NetworkX graph

    Returns:
        Dictionary of statistics
    """
    stats = {
        'total_nodes': G.number_of_nodes(),
        'total_edges': G.number_of_edges(),
        'companies': 0,
        'people': 0,
        'countries': set(),
        'most_connected': None,
        'most_connected_degree': 0
    }

    # Count node types and collect countries
    for node, attrs in G.nodes(data=True):
        entity_type = attrs.get('entity_type', '')
        if entity_type == 'company':
            stats['companies'] += 1
        elif entity_type == 'person':
            stats['people'] += 1

        jurisdiction = attrs.get('jurisdiction', '')
        if jurisdiction and jurisdiction != 'Unknown':
            stats['countries'].add(jurisdiction)

    stats['num_countries'] = len(stats['countries'])
    stats['countries'] = list(stats['countries'])

    # Find most connected node
    if G.number_of_nodes() > 0:
        degrees = dict(G.degree())
        most_connected = max(degrees.items(), key=lambda x: x[1])
        stats['most_connected'] = most_connected[0]
        stats['most_connected_degree'] = most_connected[1]

    return stats


def find_paths(G: nx.MultiDiGraph, source: str, target: str, max_paths: int = 5) -> List[List[str]]:
    """
    Find all simple paths between two nodes.

    Args:
        G: NetworkX graph
        source: Source node name
        target: Target node name
        max_paths: Maximum number of paths to return

    Returns:
        List of paths (each path is a list of node names)
    """
    try:
        # Convert to undirected for path finding (since we want any connection)
        G_undirected = G.to_undirected()

        paths = []
        for path in nx.all_simple_paths(G_undirected, source, target, cutoff=5):
            paths.append(path)
            if len(paths) >= max_paths:
                break

        return paths
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def get_neighbors_table(G: nx.MultiDiGraph, node: str) -> List[Dict]:
    """
    Get all neighbors of a node with edge attributes.

    Args:
        G: NetworkX graph
        node: Node name

    Returns:
        List of dictionaries with neighbor information
    """
    neighbors = []

    # Outgoing edges (this node -> others)
    for target in G.successors(node):
        for key, edge_attrs in G[node][target].items():
            neighbor_info = {
                'from': node,
                'to': target,
                'relationship': edge_attrs.get('relationship', ''),
                'direction': 'outgoing'
            }

            # Add relationship-specific attributes
            if 'ownership_pct' in edge_attrs and edge_attrs['ownership_pct'] is not None:
                neighbor_info['details'] = f"{edge_attrs['ownership_pct']:.1f}%"
            elif 'amount' in edge_attrs and edge_attrs['amount'] is not None:
                neighbor_info['details'] = f"{edge_attrs.get('currency', 'USD')} {edge_attrs['amount']:,.0f}"
            elif 'title' in edge_attrs and edge_attrs['title']:
                neighbor_info['details'] = edge_attrs['title']
            else:
                neighbor_info['details'] = ''

            neighbors.append(neighbor_info)

    # Incoming edges (others -> this node)
    for source in G.predecessors(node):
        for key, edge_attrs in G[source][node].items():
            neighbor_info = {
                'from': source,
                'to': node,
                'relationship': edge_attrs.get('relationship', ''),
                'direction': 'incoming'
            }

            # Add relationship-specific attributes
            if 'ownership_pct' in edge_attrs and edge_attrs['ownership_pct'] is not None:
                neighbor_info['details'] = f"{edge_attrs['ownership_pct']:.1f}%"
            elif 'amount' in edge_attrs and edge_attrs['amount'] is not None:
                neighbor_info['details'] = f"{edge_attrs.get('currency', 'USD')} {edge_attrs['amount']:,.0f}"
            elif 'title' in edge_attrs and edge_attrs['title']:
                neighbor_info['details'] = edge_attrs['title']
            else:
                neighbor_info['details'] = ''

            neighbors.append(neighbor_info)

    return neighbors
