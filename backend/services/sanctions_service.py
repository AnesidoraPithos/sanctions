"""
Sanctions Screening Service

Refactored from agents/usa_agent.py to work with FastAPI backend.
Provides sanctions screening via USA Trade API and local database.
"""

import os
import sys
from typing import List, Dict, Any, Optional
import importlib.util

# Path setup is done in services/__init__.py
# This ensures project_root is in sys.path before imports

# NOW import the existing USASanctionsAgent (after path is set up)
from agents.usa_agent import USASanctionsAgent

# Import backend config explicitly to avoid confusion with root config.py
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(backend_dir, 'config.py')
spec = importlib.util.spec_from_file_location("backend_config", config_path)
backend_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_config)
settings = backend_config.settings


class SanctionsService:
    """
    Service layer for sanctions screening

    Wraps the existing USASanctionsAgent for use in FastAPI backend.
    """

    def __init__(self):
        """Initialize sanctions service"""
        # Use existing agent implementation
        self.agent = USASanctionsAgent()

    def search_sanctions(
        self,
        entity_name: str,
        country: Optional[str] = None,
        fuzzy_threshold: int = 80
    ) -> List[Dict[str, Any]]:
        """
        Search for sanctions matches

        Args:
            entity_name: Name of entity to search
            country: Optional country filter
            fuzzy_threshold: Fuzzy matching threshold (0-100)

        Returns:
            List of sanctions hits with scoring information
        """
        # Build search parameters for USA Trade API
        search_params = {
            "name": entity_name,
            "fuzzy_name": "true"
        }

        if country:
            search_params["countries"] = country

        # Call existing agent logic
        results = self.agent.search(search_params, query_name=entity_name, score_threshold=fuzzy_threshold)

        # Filter by fuzzy threshold
        filtered_results = [
            result for result in results
            if result.get('combined_score', 0) >= fuzzy_threshold
        ]

        return filtered_results

    def format_sanctions_data(self, sanctions_hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format sanctions hits for API response

        Args:
            sanctions_hits: Raw sanctions hits from search

        Returns:
            Formatted sanctions data matching SanctionsHit model
        """
        formatted = []
        for hit in sanctions_hits:
            formatted.append({
                "name": hit.get("Name", ""),
                "list": hit.get("List", ""),
                "type": hit.get("Type"),
                "address": hit.get("Address"),
                "remark": hit.get("Remark"),
                "link": hit.get("Link"),
                "api_score": hit.get("api_score"),
                "local_score": hit.get("local_score"),
                "combined_score": hit.get("combined_score", 0),
                "match_quality": hit.get("match_quality", "LOW"),
                "similarity_breakdown": hit.get("similarity_breakdown")
            })
        return formatted

    def calculate_risk_level(self, sanctions_hits: List[Dict[str, Any]]) -> str:
        """
        Calculate risk level based on sanctions hits

        Args:
            sanctions_hits: List of sanctions matches

        Returns:
            Risk level: SAFE, LOW, MID, HIGH, VERY_HIGH
        """
        if not sanctions_hits:
            return "SAFE"

        # Count high-quality matches
        high_matches = sum(
            1 for hit in sanctions_hits
            if hit.get('match_quality') in ['EXACT', 'HIGH']
        )

        medium_matches = sum(
            1 for hit in sanctions_hits
            if hit.get('match_quality') == 'MEDIUM'
        )

        # Get best combined score
        best_score = max(
            (hit.get('combined_score', 0) for hit in sanctions_hits),
            default=0
        )

        # Risk level logic
        if high_matches >= 3 or best_score >= 95:
            return "VERY_HIGH"
        elif high_matches >= 1 or best_score >= 85:
            return "HIGH"
        elif medium_matches >= 3 or best_score >= 75:
            return "MID"
        elif len(sanctions_hits) >= 1:
            return "LOW"
        else:
            return "SAFE"

    def format_sanctions_data(
        self,
        sanctions_hits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format sanctions data for API response

        Args:
            sanctions_hits: Raw sanctions hits

        Returns:
            Formatted sanctions data
        """
        formatted = []

        for hit in sanctions_hits:
            formatted.append({
                "name": hit.get("Name") or "Unknown",
                "list": hit.get("List") or "USA",
                "type": hit.get("Type") or "Entity",
                "address": hit.get("Address") or "N/A",
                "remark": hit.get("Remark") or "",
                "link": hit.get("Link"),
                "api_score": hit.get("api_score"),
                "local_score": hit.get("local_score"),
                "combined_score": hit.get("combined_score", 0),
                "match_quality": hit.get("match_quality", "UNKNOWN"),
                "similarity_breakdown": hit.get("similarity_breakdown", {})
            })

        return formatted


# Global service instance
_sanctions_service: Optional[SanctionsService] = None


def get_sanctions_service() -> SanctionsService:
    """
    Get or create sanctions service instance

    Returns:
        SanctionsService instance
    """
    global _sanctions_service

    if _sanctions_service is None:
        _sanctions_service = SanctionsService()

    return _sanctions_service
