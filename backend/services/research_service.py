"""
Research Service

Refactored from agents/research_agent.py for FastAPI backend.
Provides OSINT media intelligence and LLM-powered intelligence reports.
"""

import os
import sys
from typing import List, Dict, Any, Optional
import importlib.util

# Path setup is done in services/__init__.py
# This ensures project_root is in sys.path before imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# NOW import the existing SanctionsResearchAgent (after path is set up)
from agents.research_agent import SanctionsResearchAgent

# Import backend config explicitly to avoid confusion with root config.py
config_path = os.path.join(backend_dir, 'config.py')
spec = importlib.util.spec_from_file_location("backend_config", config_path)
backend_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_config)
settings = backend_config.settings


class ResearchService:
    """
    Service layer for OSINT research and intelligence reporting

    Wraps the existing SanctionsResearchAgent for use in FastAPI backend.
    """

    def __init__(self):
        """Initialize research service"""
        # Use existing research agent implementation
        self.agent = SanctionsResearchAgent()

        # Configure LLM based on settings
        if settings.LLM_PROVIDER == "openai":
            # Use OpenAI API
            from openai import OpenAI
            self.agent.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.agent.model_id = settings.LLM_MODEL
        else:
            # Use Ollama (default)
            from openai import OpenAI
            self.agent.client = OpenAI(
                base_url=settings.OLLAMA_BASE_URL + '/v1',
                api_key='ollama'
            )
            self.agent.model_id = settings.LLM_MODEL

    def get_media_intelligence(self, entity_name: str) -> Dict[str, Any]:
        """
        Get media intelligence for entity

        Searches for:
        1. Official sanctions news (government sources)
        2. General media coverage (broader sources)

        Args:
            entity_name: Name of entity to research

        Returns:
            Dictionary with official and general media hits
        """
        # Get official sanctions news
        official_hits = self.agent.get_sanction_news(entity_name)

        # Get general media coverage
        general_hits = self.agent.get_general_media(entity_name)

        return {
            "official_sources": official_hits,
            "general_media": general_hits,
            "total_hits": len(official_hits) + len(general_hits)
        }

    def generate_intelligence_report(self, entity_name: str) -> str:
        """
        Generate LLM-powered intelligence report

        Uses OSINT sources and LLM to create comprehensive
        due diligence report covering:
        - Executive summary with threat level
        - Regulatory & legal status
        - Political activity
        - Recent developments
        - Business relationships

        Args:
            entity_name: Name of entity to analyze

        Returns:
            Markdown-formatted intelligence report
        """
        return self.agent.generate_intelligence_report(entity_name)

    def format_media_data(
        self,
        media_intelligence: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Format media intelligence for API response

        Args:
            media_intelligence: Raw media intelligence data

        Returns:
            Formatted media hits list
        """
        formatted = []

        # Format official sources
        for hit in media_intelligence.get("official_sources", []):
            formatted.append({
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "snippet": hit.get("snippet", ""),
                "source": "Official Government Source",
                "source_type": hit.get("source_type", "official"),
                "relevance": hit.get("relevance", "")
            })

        # Format general media
        for hit in media_intelligence.get("general_media", []):
            formatted.append({
                "title": hit.get("title", ""),
                "url": hit.get("url", ""),
                "snippet": hit.get("snippet", ""),
                "source": "General Media",
                "source_type": hit.get("source_type", "general"),
                "relevance": hit.get("relevance", "")
            })

        return formatted


# Global service instance
_research_service: Optional[ResearchService] = None


def get_research_service() -> ResearchService:
    """
    Get or create research service instance

    Returns:
        ResearchService instance
    """
    global _research_service

    if _research_service is None:
        _research_service = ResearchService()

    return _research_service
