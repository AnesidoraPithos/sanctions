"""
Advanced OSINT Service — Phase 4

LittleSis API lookups and targeted DuckDuckGo dork queries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

LITTLESIS_API_URL = "https://littlesis.org/api/entities"

DORK_TEMPLATES = [
    '"{name}" site:opensecrets.org',
    '"{name}" "beneficial owner"',
    '"{name}" "ultimate beneficial owner"',
]


class AdvancedOsintService:
    """Advanced OSINT: LittleSis + targeted dork queries."""

    # ------------------------------------------------------------------
    # LittleSis
    # ------------------------------------------------------------------

    def search_littlesis(self, entity_name: str) -> List[Dict[str, Any]]:
        """Query LittleSis API for entity relationships.

        Args:
            entity_name: Name to look up.

        Returns:
            List of entity dicts from LittleSis.
        """
        try:
            params = {"q": entity_name, "num": 10}
            headers: Dict[str, str] = {}
            try:
                from config import settings
                if settings.LITTLESIS_API_KEY:
                    headers["Authorization"] = f"Token {settings.LITTLESIS_API_KEY}"
            except Exception:
                pass

            resp = requests.get(
                LITTLESIS_API_URL, params=params, headers=headers, timeout=15
            )
            if resp.status_code != 200:
                logger.warning(
                    "LittleSis returned %s for %s", resp.status_code, entity_name
                )
                return []

            data = resp.json()
            entities = data.get("data") or data.get("entities") or (data if isinstance(data, list) else [])
            results: List[Dict[str, Any]] = []
            for entity in entities[:10]:
                attrs = entity.get("attributes") or entity
                results.append(
                    {
                        "id": entity.get("id"),
                        "name": attrs.get("name") or attrs.get("primary_ext") or "",
                        "type": attrs.get("primary_ext") or attrs.get("type") or "",
                        "summary": attrs.get("summary") or "",
                        "url": attrs.get("url") or f"https://littlesis.org/person/{entity.get('id', '')}",
                    }
                )
            return results

        except Exception as exc:
            logger.warning("LittleSis search failed for %s: %s", entity_name, exc)
            return []

    # ------------------------------------------------------------------
    # Dork queries
    # ------------------------------------------------------------------

    def run_targeted_dorks(self, entity_name: str) -> List[Dict[str, Any]]:
        """Run targeted DuckDuckGo dork queries for beneficial ownership signals.

        Args:
            entity_name: Entity to research.

        Returns:
            List of search result dicts.
        """
        results: List[Dict[str, Any]] = []
        try:
            from services.research_service import get_research_service  # type: ignore
            research_service = get_research_service()

            for template in DORK_TEMPLATES:
                query = template.format(name=entity_name)
                try:
                    # Reuse the existing DuckDuckGo search utility
                    hits = research_service._search_duckduckgo(query, max_results=3)  # type: ignore
                    for hit in hits:
                        results.append(
                            {
                                "query": query,
                                "title": hit.get("title", ""),
                                "url": hit.get("url", ""),
                                "snippet": hit.get("snippet", ""),
                            }
                        )
                except Exception as dork_exc:
                    logger.debug("Dork query failed (%s): %s", query, dork_exc)

        except Exception as exc:
            logger.warning("Targeted dorks failed for %s: %s", entity_name, exc)

        return results

    # ------------------------------------------------------------------
    # Combined
    # ------------------------------------------------------------------

    def get_advanced_osint(self, entity_name: str) -> Dict[str, Any]:
        """Return combined LittleSis + dork results.

        Args:
            entity_name: Entity to investigate.

        Returns:
            Dict with littlesis_results and dork_results.
        """
        littlesis_results = self.search_littlesis(entity_name)
        dork_results = self.run_targeted_dorks(entity_name)
        return {
            "littlesis_results": littlesis_results,
            "dork_results": dork_results,
        }
