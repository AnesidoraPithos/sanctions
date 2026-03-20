"""
Network Service

Handles network graph generation for entity relationships.
Converts NetworkX graphs to JSON format for frontend visualization (Cytoscape.js).
"""

import logging
import os
import sys
from typing import Dict, Any, List, Optional

# Path setup is done in services/__init__.py
# This ensures project_root is in sys.path before imports

# NOW import existing modules (after path is set up)
from visualizations.graph_builder import build_entity_graph, get_graph_statistics

logger = logging.getLogger(__name__)


class NetworkService:
    """
    Service for generating network graph data

    Converts entity relationship data into JSON format for Cytoscape.js visualization
    """

    def __init__(self):
        """Initialize network service"""
        logger.info("NetworkService initialized")

    def build_network_graph(
        self,
        company_name: str,
        subsidiaries: Optional[List[Dict]] = None,
        sisters: Optional[List[Dict]] = None,
        directors: Optional[List[Dict]] = None,
        shareholders: Optional[List[Dict]] = None,
        transactions: Optional[List[Dict]] = None,
        parent_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Build network graph data structure for frontend visualization

        Args:
            company_name: Name of the parent company
            subsidiaries: List of subsidiary entities
            sisters: List of sister entities
            directors: List of director/officer dictionaries
            shareholders: List of shareholder dictionaries
            transactions: List of transaction dictionaries
            parent_info: Optional parent company details

        Returns:
            dict: {
                'nodes': List of node dicts for Cytoscape.js,
                'edges': List of edge dicts for Cytoscape.js,
                'statistics': Graph statistics dict
            }
        """
        logger.info(f"Building network graph for '{company_name}'")

        try:
            # Step 1: Build NetworkX graph using existing graph_builder
            nx_graph = build_entity_graph(
                company_name=company_name,
                subsidiaries=subsidiaries,
                sisters=sisters,
                directors=directors,
                shareholders=shareholders,
                transactions=transactions,
                parent_info=parent_info
            )

            logger.info(
                f"NetworkX graph built: "
                f"{nx_graph.number_of_nodes()} nodes, "
                f"{nx_graph.number_of_edges()} edges"
            )

            # Step 2: Convert NetworkX graph to Cytoscape.js JSON format
            nodes = self._convert_nodes_to_json(nx_graph)
            edges = self._convert_edges_to_json(nx_graph)

            # Step 3: Calculate graph statistics
            statistics = get_graph_statistics(nx_graph)

            logger.info(
                f"Network graph JSON generated: "
                f"{len(nodes)} nodes, {len(edges)} edges, "
                f"{statistics['companies']} companies, {statistics['people']} people"
            )

            return {
                'nodes': nodes,
                'edges': edges,
                'statistics': statistics
            }

        except Exception as e:
            logger.error(f"Network graph generation failed: {str(e)}", exc_info=True)
            return {
                'nodes': [],
                'edges': [],
                'statistics': {
                    'total_nodes': 0,
                    'total_edges': 0,
                    'companies': 0,
                    'people': 0,
                    'countries': [],
                    'error': str(e)
                }
            }

    def _convert_nodes_to_json(self, nx_graph) -> List[Dict[str, Any]]:
        """
        Convert NetworkX nodes to Cytoscape.js node format

        Cytoscape.js node format:
        {
            'data': {
                'id': 'node_id',
                'label': 'Node Label',
                'node_type': 'parent|subsidiary|sister|director|shareholder',
                'entity_type': 'company|person',
                ... other attributes ...
            }
        }

        Args:
            nx_graph: NetworkX MultiDiGraph

        Returns:
            List of node dicts in Cytoscape.js format
        """
        nodes = []

        for node_id, attrs in nx_graph.nodes(data=True):
            # Create Cytoscape.js node format
            cy_node = {
                'data': {
                    'id': node_id,
                    'label': node_id,
                    **attrs  # Spread all NetworkX node attributes
                }
            }
            nodes.append(cy_node)

        return nodes

    def _convert_edges_to_json(self, nx_graph) -> List[Dict[str, Any]]:
        """
        Convert NetworkX edges to Cytoscape.js edge format

        Cytoscape.js edge format:
        {
            'data': {
                'id': 'edge_id',
                'source': 'source_node_id',
                'target': 'target_node_id',
                'relationship': 'owns|director_of|shareholder_of|transacted_with|sibling_of',
                ... other attributes ...
            }
        }

        Args:
            nx_graph: NetworkX MultiDiGraph

        Returns:
            List of edge dicts in Cytoscape.js format
        """
        edges = []

        for idx, (source, target, attrs) in enumerate(nx_graph.edges(data=True)):
            # Create unique edge ID
            edge_id = f"{source}_{target}_{idx}"

            # Create Cytoscape.js edge format
            cy_edge = {
                'data': {
                    'id': edge_id,
                    'source': source,
                    'target': target,
                    **attrs  # Spread all NetworkX edge attributes
                }
            }
            edges.append(cy_edge)

        return edges

    def get_subgraph(
        self,
        full_graph_data: Dict[str, Any],
        node_ids: List[str],
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Extract a subgraph containing specified nodes and their neighbors

        Useful for filtering large graphs to show only relevant entities

        Args:
            full_graph_data: Full graph data dict (nodes, edges, statistics)
            node_ids: List of node IDs to include in subgraph
            depth: How many hops away from node_ids to include (default 1)

        Returns:
            dict: Subgraph data (nodes, edges, statistics)
        """
        logger.info(f"Extracting subgraph for {len(node_ids)} nodes with depth={depth}")

        # Get all nodes and edges
        all_nodes = {node['data']['id']: node for node in full_graph_data['nodes']}
        all_edges = full_graph_data['edges']

        # Start with requested nodes
        included_node_ids = set(node_ids)

        # Add neighbors up to specified depth
        for _ in range(depth):
            neighbors = set()
            for edge in all_edges:
                source = edge['data']['source']
                target = edge['data']['target']

                if source in included_node_ids:
                    neighbors.add(target)
                if target in included_node_ids:
                    neighbors.add(source)

            included_node_ids.update(neighbors)

        # Filter nodes
        filtered_nodes = [
            node for node in full_graph_data['nodes']
            if node['data']['id'] in included_node_ids
        ]

        # Filter edges (only include edges where both source and target are included)
        filtered_edges = [
            edge for edge in all_edges
            if edge['data']['source'] in included_node_ids
            and edge['data']['target'] in included_node_ids
        ]

        logger.info(
            f"Subgraph extracted: {len(filtered_nodes)} nodes, {len(filtered_edges)} edges"
        )

        return {
            'nodes': filtered_nodes,
            'edges': filtered_edges,
            'statistics': {
                'total_nodes': len(filtered_nodes),
                'total_edges': len(filtered_edges)
            }
        }


# Singleton instance
_network_service = None


def get_network_service() -> NetworkService:
    """Get or create singleton network service instance"""
    global _network_service
    if _network_service is None:
        _network_service = NetworkService()
    return _network_service
