"""
Beneficial Ownership Service — Phase 4

Queries OCCRP Aleph and Open Ownership Register to trace UBOs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

ALEPH_SEARCH_URL = "https://aleph.occrp.org/api/2/search"
OPEN_OWNERSHIP_URL = "https://register.openownership.org/api/companies/search"


class BeneficialOwnershipService:
    """Trace beneficial ownership from public registries."""

    # ------------------------------------------------------------------
    # OCCRP Aleph
    # ------------------------------------------------------------------

    def search_occrp_aleph(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search OCCRP Aleph for beneficial owners.

        Args:
            entity_name: Company name to search.

        Returns:
            List of partial owner dicts.
        """
        try:
            params = {
                "q": entity_name,
                "filter:schema": "Company",
                "limit": 20,
            }
            resp = requests.get(ALEPH_SEARCH_URL, params=params, timeout=15)
            if resp.status_code != 200:
                logger.warning("Aleph returned %s for %s", resp.status_code, entity_name)
                return []

            data = resp.json()
            results: List[Dict[str, Any]] = []
            for hit in data.get("results", []):
                props = hit.get("properties", {})
                name = hit.get("caption") or (props.get("name") or [None])[0]
                if not name:
                    continue
                country_list = props.get("country") or props.get("jurisdiction") or []
                nationality = country_list[0] if country_list else None
                results.append(
                    {
                        "name": name,
                        "nationality": nationality,
                        "ownership_pct": None,
                        "source": "OCCRP Aleph",
                        "source_url": f"https://aleph.occrp.org/entities/{hit.get('id', '')}",
                        "verification_date": None,
                    }
                )
            return results

        except Exception as exc:
            logger.warning("OCCRP Aleph search failed for %s: %s", entity_name, exc)
            return []

    # ------------------------------------------------------------------
    # Open Ownership Register
    # ------------------------------------------------------------------

    def search_open_ownership(self, entity_name: str) -> List[Dict[str, Any]]:
        """Search Open Ownership Register for beneficial owners.

        Args:
            entity_name: Company name to search.

        Returns:
            List of partial owner dicts.
        """
        try:
            params = {"q": entity_name}
            resp = requests.get(OPEN_OWNERSHIP_URL, params=params, timeout=15)
            if resp.status_code != 200:
                logger.warning(
                    "Open Ownership returned %s for %s", resp.status_code, entity_name
                )
                return []

            data = resp.json()
            results: List[Dict[str, Any]] = []
            companies = data if isinstance(data, list) else data.get("companies", []) or data.get("results", [])
            for company in companies[:10]:
                owners = company.get("ultimate_beneficial_owners") or []
                for owner in owners:
                    name = owner.get("name") or owner.get("full_name") or ""
                    if not name:
                        continue
                    pct: Optional[float] = None
                    raw_pct = owner.get("ownership_percentage") or owner.get("percentage_of_shares")
                    if raw_pct is not None:
                        try:
                            pct = float(raw_pct)
                        except (TypeError, ValueError):
                            pct = None

                    nationality = owner.get("nationality") or owner.get("country_of_residence")
                    results.append(
                        {
                            "name": name,
                            "nationality": nationality,
                            "ownership_pct": pct,
                            "source": "OpenOwnership",
                            "source_url": f"https://register.openownership.org/entities/{owner.get('id', '')}",
                            "verification_date": owner.get("declared_date"),
                        }
                    )
            return results

        except Exception as exc:
            logger.warning(
                "Open Ownership search failed for %s: %s", entity_name, exc
            )
            return []

    # ------------------------------------------------------------------
    # Combined
    # ------------------------------------------------------------------

    def get_beneficial_owners(self, entity_name: str) -> List[Dict[str, Any]]:
        """Combine and deduplicate beneficial owners from all sources.

        Args:
            entity_name: Entity to trace.

        Returns:
            Deduplicated list of owner dicts.
        """
        aleph = self.search_occrp_aleph(entity_name)
        open_own = self.search_open_ownership(entity_name)

        combined = aleph + open_own
        seen: set[str] = set()
        deduped: List[Dict[str, Any]] = []
        for item in combined:
            key = item.get("name", "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                deduped.append(item)

        return deduped
