"""
Beneficial Ownership Service — Phase 4

Builds a BODS (Beneficial Ownership Data Standard) formatting engine that
transforms ownership data already collected by Companies House, SEC EDGAR,
and OpenCorporates into a strict BODS-compliant JSON structure with three
core arrays: entities, persons, and ownershipOrControlStatements.

The Open Ownership Register was retired in late 2024; no external OO API
calls are made. OCCRP Aleph search is retained as a supplementary source.
"""

from __future__ import annotations

import logging
import uuid as _uuid_mod
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

ALEPH_SEARCH_URL = "https://aleph.occrp.org/api/2/search"

_MAX_CHAIN_DEPTH = 5

# Namespace for deterministic UUID5 generation
_BODS_NS = _uuid_mod.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


# ---------------------------------------------------------------------------
# BODS helper functions (used for traversing synthetic BODS statements)
# ---------------------------------------------------------------------------

def _make_id(prefix: str, name: str) -> str:
    """Generate a deterministic BODS statementID from a prefix and name."""
    slug = f"{prefix}:{name.lower().strip()}"
    return str(_uuid_mod.uuid5(_BODS_NS, slug))


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
    source_map: Dict[str, str],
    source_url_map: Dict[str, Optional[str]],
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
        source_map: Map of statementID → source name string.
        source_url_map: Map of statementID → source URL string or None.
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
        interests = stmt.get("interests") or []
        pct = _extract_pct(interests)
        stmt_date = stmt.get("statementDate")
        interest_type = interests[0].get("type") if interests else "shareholding"

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
                    "source": source_map.get(person_id, "unknown"),
                    "source_url": source_url_map.get(person_id),
                    "verification_date": stmt_date,
                    "interest_type": interest_type,
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
                    source_map,
                    source_url_map,
                    max_depth,
                )
            )

    return results


class BeneficialOwnershipService:
    """
    BODS formatting engine for beneficial ownership tracing.

    Takes ownership data already collected by Companies House (PSC),
    SEC EDGAR, and OpenCorporates and transforms it into BODS-compliant JSON.
    OCCRP Aleph is queried as a supplementary enrichment source.
    """

    # ------------------------------------------------------------------
    # OCCRP Aleph (supplementary enrichment, API still active)
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
                        "entity_type": "person",
                        "via": [],
                        "source": "OCCRP Aleph",
                        "source_url": f"https://aleph.occrp.org/entities/{hit.get('id', '')}",
                        "verification_date": None,
                        "interest_type": "shareholding",
                    }
                )
            return results

        except Exception as exc:
            logger.warning("OCCRP Aleph search failed for %s: %s", entity_name, exc)
            return []

    # ------------------------------------------------------------------
    # BODS formatting engine
    # ------------------------------------------------------------------

    def build_bods_from_collected_data(
        self,
        entity_name: str,
        shareholders: List[Dict[str, Any]],
        directors: List[Dict[str, Any]],
        subsidiaries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a BODS-compliant JSON structure from already-collected data.

        Maps data from Companies House PSC, SEC EDGAR shareholders/directors,
        and OpenCorporates subsidiaries into the three core BODS arrays.

        Args:
            entity_name: The root entity being researched.
            shareholders: List of shareholder dicts (from Companies House / SEC EDGAR).
            directors: List of director dicts (from Companies House / SEC EDGAR).
            subsidiaries: List of subsidiary dicts (from OpenCorporates / SEC EDGAR).

        Returns:
            Dict with keys ``entities``, ``persons``, ``ownershipOrControlStatements``.
        """
        entities: List[Dict[str, Any]] = []
        persons: List[Dict[str, Any]] = []
        ownership_stmts: List[Dict[str, Any]] = []

        seen_entity_ids: set = set()
        seen_person_ids: set = set()

        # Root entity (the searched company)
        root_id = _make_id("entity", entity_name)
        entities.append(
            {
                "statementID": root_id,
                "statementType": "entityStatement",
                "name": entity_name,
                "entityType": "registeredEntity",
                "identifiers": [],
            }
        )
        seen_entity_ids.add(root_id)

        # --- Shareholders ---
        for sh in (shareholders or []):
            name = (sh.get("name") or "").strip()
            if not name:
                continue
            sh_type = (sh.get("shareholder_type") or "").lower()
            source = sh.get("source", "unknown")
            source_url = sh.get("source_url")
            filing_date = sh.get("filing_date")
            raw_pct = sh.get("ownership_percentage") or sh.get("ownership_pct") or 0.0
            try:
                ownership_pct = float(raw_pct)
            except (TypeError, ValueError):
                ownership_pct = 0.0

            is_corporate = any(
                kw in sh_type for kw in ("company", "corporate", "organisation", "organization", "entity")
            )

            if is_corporate:
                ent_id = _make_id("entity", name)
                if ent_id not in seen_entity_ids:
                    entities.append(
                        {
                            "statementID": ent_id,
                            "statementType": "entityStatement",
                            "name": name,
                            "entityType": "registeredEntity",
                            "identifiers": (
                                [{"id": source_url, "scheme": source}] if source_url else []
                            ),
                        }
                    )
                    seen_entity_ids.add(ent_id)
                interests = [{"type": "shareholding"}]
                if ownership_pct:
                    interests = [{"type": "shareholding", "share": {"exact": ownership_pct}}]
                ownership_stmts.append(
                    {
                        "statementID": _make_id("ocs", f"{name}:owns:{entity_name}"),
                        "statementType": "ownershipOrControlStatement",
                        "statementDate": filing_date,
                        "subject": {"describedByEntityStatement": root_id},
                        "interestedParty": {"describedByEntityStatement": ent_id},
                        "interests": interests,
                    }
                )
            else:
                person_id = _make_id("person", name)
                nationality = sh.get("nationality") or sh.get("jurisdiction")
                if person_id not in seen_person_ids:
                    persons.append(
                        {
                            "statementID": person_id,
                            "statementType": "personStatement",
                            "names": [{"fullName": name, "type": "individual"}],
                            "nationalities": (
                                [{"code": nationality}] if nationality else []
                            ),
                            "personType": "knownPerson",
                            "identifiers": (
                                [{"id": source_url, "scheme": source}] if source_url else []
                            ),
                        }
                    )
                    seen_person_ids.add(person_id)
                interests = [{"type": "shareholding"}]
                if ownership_pct:
                    interests = [{"type": "shareholding", "share": {"exact": ownership_pct}}]
                ownership_stmts.append(
                    {
                        "statementID": _make_id("ocs", f"{name}:owns:{entity_name}"),
                        "statementType": "ownershipOrControlStatement",
                        "statementDate": filing_date,
                        "subject": {"describedByEntityStatement": root_id},
                        "interestedParty": {"describedByPersonStatement": person_id},
                        "interests": interests,
                    }
                )

        # --- Directors (control via directorship, no share %) ---
        for dr in (directors or []):
            name = (dr.get("name") or "").strip()
            if not name:
                continue
            source = dr.get("source", "unknown")
            source_url = dr.get("source_url")
            filing_date = dr.get("filing_date")
            nationality = dr.get("nationality")
            person_id = _make_id("person", name)
            if person_id not in seen_person_ids:
                persons.append(
                    {
                        "statementID": person_id,
                        "statementType": "personStatement",
                        "names": [{"fullName": name, "type": "individual"}],
                        "nationalities": (
                            [{"code": nationality}] if nationality else []
                        ),
                        "personType": "knownPerson",
                        "identifiers": (
                            [{"id": source_url, "scheme": source}] if source_url else []
                        ),
                    }
                )
                seen_person_ids.add(person_id)
            # Only add directorship statement if not already a shareholder of same entity
            ocs_id = _make_id("ocs", f"{name}:directs:{entity_name}")
            existing_ids = {s["statementID"] for s in ownership_stmts}
            if ocs_id not in existing_ids:
                ownership_stmts.append(
                    {
                        "statementID": ocs_id,
                        "statementType": "ownershipOrControlStatement",
                        "statementDate": filing_date,
                        "subject": {"describedByEntityStatement": root_id},
                        "interestedParty": {"describedByPersonStatement": person_id},
                        "interests": [{"type": "controlViaDirectorship"}],
                    }
                )

        # --- Subsidiaries (root entity owns subsidiaries — reversed direction) ---
        for sub in (subsidiaries or []):
            name = (sub.get("name") or "").strip()
            if not name:
                continue
            jurisdiction = sub.get("jurisdiction")
            raw_pct = sub.get("ownership_pct") or sub.get("ownership_percentage")
            sub_id = _make_id("entity", name)
            if sub_id not in seen_entity_ids:
                entry: Dict[str, Any] = {
                    "statementID": sub_id,
                    "statementType": "entityStatement",
                    "name": name,
                    "entityType": "registeredEntity",
                    "identifiers": [],
                }
                if jurisdiction:
                    entry["incorporationCountryCode"] = jurisdiction
                entities.append(entry)
                seen_entity_ids.add(sub_id)
            interests: List[Dict[str, Any]] = [{"type": "shareholding"}]
            if raw_pct is not None:
                try:
                    interests = [{"type": "shareholding", "share": {"exact": float(raw_pct)}}]
                except (TypeError, ValueError):
                    pass
            # subject = subsidiary; interestedParty = root (root controls subsidiary)
            ownership_stmts.append(
                {
                    "statementID": _make_id("ocs", f"{entity_name}:owns:{name}"),
                    "statementType": "ownershipOrControlStatement",
                    "subject": {"describedByEntityStatement": sub_id},
                    "interestedParty": {"describedByEntityStatement": root_id},
                    "interests": interests,
                }
            )

        return {
            "entities": entities,
            "persons": persons,
            "ownershipOrControlStatements": ownership_stmts,
        }

    # ------------------------------------------------------------------
    # Combined entry point
    # ------------------------------------------------------------------

    def get_beneficial_owners(
        self,
        entity_name: str,
        shareholders: Optional[List[Dict[str, Any]]] = None,
        directors: Optional[List[Dict[str, Any]]] = None,
        subsidiaries: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build BODS output and derive the flat beneficial-owner list.

        Args:
            entity_name: Entity to trace.
            shareholders: Shareholder dicts from Companies House PSC / SEC EDGAR.
            directors: Director dicts from Companies House Officers / SEC EDGAR.
            subsidiaries: Subsidiary dicts from OpenCorporates / SEC EDGAR.

        Returns:
            Dict with:
            - ``bods``: Full BODS JSON (entities, persons, ownershipOrControlStatements).
            - ``owners``: Flat list of BeneficialOwner-compatible dicts.
        """
        bods = self.build_bods_from_collected_data(
            entity_name=entity_name,
            shareholders=shareholders or [],
            directors=directors or [],
            subsidiaries=subsidiaries or [],
        )

        # Index BODS statements for traversal
        entity_map: Dict[str, Dict] = {
            s["statementID"]: s for s in bods["entities"]
        }
        person_map: Dict[str, Dict] = {
            s["statementID"]: s for s in bods["persons"]
        }

        # Build source lookup maps for the traversal
        source_map: Dict[str, str] = {}
        source_url_map: Dict[str, Optional[str]] = {}
        for stmt in bods["persons"]:
            sid = stmt["statementID"]
            idents = stmt.get("identifiers") or []
            source_map[sid] = idents[0]["scheme"] if idents else "unknown"
            source_url_map[sid] = idents[0].get("id") if idents else None

        # Find root entity ID
        root_id = _make_id("entity", entity_name)

        # Derive flat owner list via recursive UBO traversal
        owners = _trace_ubo(
            entity_id=root_id,
            entity_map=entity_map,
            person_map=person_map,
            ownership_list=bods["ownershipOrControlStatements"],
            path=[],
            seen={root_id},
            source_map=source_map,
            source_url_map=source_url_map,
        )

        # Enrich with OCCRP Aleph (supplementary, dedup by name)
        aleph_owners = self.search_occrp_aleph(entity_name)
        seen_names: set = {(o.get("name") or "").lower().strip() for o in owners}
        for ao in aleph_owners:
            key = (ao.get("name") or "").lower().strip()
            if key and key not in seen_names:
                seen_names.add(key)
                owners.append(ao)

        return {"bods": bods, "owners": owners}
