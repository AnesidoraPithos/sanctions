"""
Beneficial Ownership Service — Phase 4

Queries OCCRP Aleph and Open Ownership Register to trace UBOs.
The Open Ownership integration uses the BODS (Beneficial Ownership Data
Standard) format: a two-step flow (company search → network statements)
followed by recursive chain traversal to find the ultimate beneficial owners
and any intermediary shell companies between them and the target entity.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

ALEPH_SEARCH_URL = "https://aleph.occrp.org/api/2/search"
OPEN_OWNERSHIP_SEARCH_URL = "https://register.openownership.org/api/companies/search"
OPEN_OWNERSHIP_NETWORK_URL = "https://register.openownership.org/api/companies/{company_id}/network"

_MAX_CHAIN_DEPTH = 5


# ---------------------------------------------------------------------------
# BODS helper functions
# ---------------------------------------------------------------------------

def _extract_pct(interests: List[Dict[str, Any]]) -> Optional[float]:
    """Return the first numeric ownership percentage found in a BODS interests list."""
    for interest in interests:
        share = interest.get("share") or {}
        for key in ("exact", "minimum", "exclusiveMinimum"):
            raw = share.get(key)
            if raw is not None:
                try:
                    return float(raw)
                except (TypeError, ValueError):
                    pass
    return None


def _get_person_name(person_stmt: Dict[str, Any]) -> Optional[str]:
    """Return the first fullName from a BODS personStatement."""
    for name_obj in person_stmt.get("names", []):
        full = name_obj.get("fullName") or name_obj.get("fullname")
        if full:
            return full
    return None


def _get_nationality(person_stmt: Dict[str, Any]) -> Optional[str]:
    """Return the first nationality code from a BODS personStatement."""
    for nat in person_stmt.get("nationalities", []):
        code = nat.get("code") or nat.get("name")
        if code:
            return code
    return None


def _trace_ubo(
    entity_id: str,
    entity_map: Dict[str, Dict],
    person_map: Dict[str, Dict],
    ownership_list: List[Dict],
    path: List[str],
    seen: set,
    max_depth: int = _MAX_CHAIN_DEPTH,
) -> List[Dict[str, Any]]:
    """Recursively trace Ultimate Beneficial Owners from a BODS statement set.

    Args:
        entity_id: BODS statementID of the entity whose owners we are tracing.
        entity_map: Map of statementID → entityStatement dicts.
        person_map: Map of statementID → personStatement dicts.
        ownership_list: All ownershipOrControlStatement dicts.
        path: Intermediary entity names accumulated so far (empty at root call).
        seen: Set of already-visited statement IDs (prevents cycles).
        max_depth: Maximum intermediary depth before stopping recursion.

    Returns:
        List of owner dicts ready for the BeneficialOwner response model.
    """
    results: List[Dict[str, Any]] = []

    for stmt in ownership_list:
        subject = stmt.get("subject") or {}
        if subject.get("describedByEntityStatement") != entity_id:
            continue

        party = stmt.get("interestedParty") or {}
        pct = _extract_pct(stmt.get("interests") or [])

        # Case A: owner is a person → UBO found
        person_id = party.get("describedByPersonStatement")
        if person_id:
            if person_id in seen:
                continue
            seen.add(person_id)
            person = person_map.get(person_id, {})
            name = _get_person_name(person)
            results.append(
                {
                    "name": name or person_id,
                    "nationality": _get_nationality(person),
                    "ownership_pct": pct,
                    "entity_type": "person",
                    "via": list(path),
                    "source": "OpenOwnership",
                    "source_url": f"https://register.openownership.org/entities/{person_id}",
                    "verification_date": stmt.get("statementDate"),
                }
            )
            continue

        # Case B: owner is another entity → intermediary, recurse if depth allows
        inter_id = party.get("describedByEntityStatement")
        if inter_id and len(path) < max_depth and inter_id not in seen:
            seen.add(inter_id)
            inter_name = entity_map.get(inter_id, {}).get("name") or inter_id
            results.extend(
                _trace_ubo(
                    inter_id,
                    entity_map,
                    person_map,
                    ownership_list,
                    path + [inter_name],
                    seen,
                    max_depth,
                )
            )

    return results


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
    # Open Ownership Register — BODS
    # ------------------------------------------------------------------

    def search_open_ownership(self, entity_name: str) -> List[Dict[str, Any]]:
        """Query the Open Ownership Register using BODS to trace UBOs.

        Two-step process:
        1. Search for the company by name to get its internal ID.
        2. Fetch the BODS network statements for that company and recursively
           trace the ownership chain to find Ultimate Beneficial Owners and
           any intermediary entities in the chain.

        Args:
            entity_name: Company name to search.

        Returns:
            List of owner dicts with ``entity_type`` and ``via`` chain fields.
        """
        try:
            # Step 1 — find company ID
            search_resp = requests.get(
                OPEN_OWNERSHIP_SEARCH_URL,
                params={"q": entity_name},
                timeout=15,
            )
            if search_resp.status_code != 200:
                logger.warning(
                    "Open Ownership search returned %s for %s",
                    search_resp.status_code,
                    entity_name,
                )
                return []

            search_data = search_resp.json()
            companies: List[Dict] = (
                search_data
                if isinstance(search_data, list)
                else search_data.get("companies", []) or search_data.get("results", [])
            )
            if not companies:
                return []

            # Use the best-matching company (first result)
            company = companies[0]
            company_id: Optional[str] = (
                company.get("_id")
                or company.get("company_number")
                or company.get("id")
            )
            if not company_id:
                logger.warning("No company ID found in Open Ownership search result")
                return []

            # Step 2 — fetch BODS network statements
            network_resp = requests.get(
                OPEN_OWNERSHIP_NETWORK_URL.format(company_id=company_id),
                timeout=15,
            )
            if network_resp.status_code != 200:
                logger.warning(
                    "Open Ownership network endpoint returned %s for company %s",
                    network_resp.status_code,
                    company_id,
                )
                return []

            network_data = network_resp.json()
            statements: List[Dict] = (
                network_data
                if isinstance(network_data, list)
                else network_data.get("data", []) or network_data.get("statements", [])
            )
            if not statements:
                return []

            # Step 3 — index statements by type
            person_map: Dict[str, Dict] = {}
            entity_map: Dict[str, Dict] = {}
            ownership_list: List[Dict] = []

            for stmt in statements:
                stmt_type = stmt.get("statementType", "")
                stmt_id = stmt.get("statementID") or stmt.get("id", "")
                if stmt_type == "personStatement":
                    person_map[stmt_id] = stmt
                elif stmt_type == "entityStatement":
                    entity_map[stmt_id] = stmt
                elif stmt_type == "ownershipOrControlStatement":
                    ownership_list.append(stmt)

            if not ownership_list:
                return []

            # Step 4 — find the root entity statement for the searched company.
            # The root entity is the one whose name best matches entity_name, or
            # the first entityStatement if there is only one.
            root_id: Optional[str] = None
            entity_name_lower = entity_name.lower()
            for eid, estmt in entity_map.items():
                if entity_name_lower in (estmt.get("name") or "").lower():
                    root_id = eid
                    break
            if root_id is None and entity_map:
                root_id = next(iter(entity_map))

            if root_id is None:
                return []

            # Step 5 — recursive UBO traversal starting from root entity
            return _trace_ubo(
                root_id,
                entity_map,
                person_map,
                ownership_list,
                path=[],
                seen={root_id},
            )

        except Exception as exc:
            logger.warning(
                "Open Ownership BODS search failed for %s: %s", entity_name, exc
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
