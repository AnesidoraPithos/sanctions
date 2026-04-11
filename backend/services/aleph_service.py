"""
Aleph Service (OCCRP)

Queries the OCCRP Aleph public API to detect:
  - Offshore leak database hits (Panama Papers, Pandora Papers, Paradise Papers,
    Bahamas Leaks, Offshore Leaks, Luanda Leaks, ICIJ datasets)
  - Politically Exposed Persons (PEP) flagged via properties.topics or
    schema=Person with a non-empty properties.position

API endpoint: GET https://aleph.occrp.org/api/2/search
Authentication: Optional ApiKey header (gracefully skipped if not configured).
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

_ALEPH_SEARCH_URL = "https://aleph.occrp.org/api/2/search"

# Partial strings that identify offshore leak datasets.
# Matched against both dataset['id'] and dataset['label'] (lowercased).
_LEAK_DATASET_KEYWORDS: List[str] = [
    "panama_papers",
    "pandora_papers",
    "paradise_papers",
    "bahamas_leaks",
    "offshore_leaks",
    "luanda_leaks",
    "icij",
]


def _is_leak_dataset(dataset: Dict[str, Any]) -> bool:
    """
    Return True if the dataset dict looks like a known offshore leak dataset.

    Checks are case-insensitive partial matches against both the dataset 'id'
    and 'label' fields, covering naming variations (e.g. 'panama-papers',
    'Panama Papers 2016', etc.).
    """
    dataset_id = (dataset.get("id") or "").lower()
    dataset_label = (dataset.get("label") or "").lower()
    for keyword in _LEAK_DATASET_KEYWORDS:
        # keyword uses underscores; also match hyphenated variants
        normalised_keyword = keyword.replace("_", "")
        if (
            keyword in dataset_id
            or keyword in dataset_label
            or normalised_keyword in dataset_id.replace("-", "").replace("_", "")
            or normalised_keyword in dataset_label.replace("-", "").replace("_", "")
        ):
            return True
    return False


def _is_pep(hit: Dict[str, Any]) -> bool:
    """
    Return True if an Aleph result looks like a Politically Exposed Person.

    Two detection paths:
    1. 'role.pep' present anywhere in properties.topics list.
    2. schema == 'Person' AND properties.position is non-empty.
    """
    props = hit.get("properties", {})
    topics: List[str] = props.get("topics") or []
    if "role.pep" in topics:
        return True
    if hit.get("schema") == "Person":
        position = props.get("position") or []
        if position:
            return True
    return False


class AlephService:
    """
    Service for querying OCCRP Aleph to detect offshore leak hits and PEPs.

    Returns enriched hit dicts in a flat schema consumed directly by the deep
    tier route and the risk assessment service.
    """

    def __init__(self) -> None:
        try:
            from config import settings
            self.api_key: str = getattr(settings, "ALEPH_API_KEY", "") or os.getenv("ALEPH_API_KEY", "")
        except Exception:
            self.api_key = os.getenv("ALEPH_API_KEY", "")

        if self.api_key:
            logger.info("AlephService initialised with API key")
        else:
            logger.info(
                "AlephService initialised — no ALEPH_API_KEY configured, "
                "public (rate-limited) access will be used"
            )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def search_leaks_and_peps(self, entity_name: str) -> List[Dict[str, Any]]:
        """
        Search Aleph for offshore leak hits and PEP flags for a named entity.

        Args:
            entity_name: Name of the entity or person to screen.

        Returns:
            List of hit dicts, each containing:
              name           - entity caption from Aleph
              entity_type    - Aleph schema (e.g. 'Person', 'Company', 'LegalEntity')
              dataset_id     - dataset identifier string
              dataset_label  - human-readable dataset name
              is_leak_db_hit - True if the dataset is a known offshore leak database
              is_pep         - True if the entity appears to be a PEP
              score          - Aleph relevance score (float)
              source_url     - direct Aleph entity URL
              country        - first country listed in properties.country, or ""
        """
        logger.info(f"AlephService: searching for '{entity_name}'")
        raw_results = self._fetch(entity_name)
        if raw_results is None:
            return []

        hits: List[Dict[str, Any]] = []
        for result in raw_results:
            dataset: Dict[str, Any] = result.get("dataset") or {}
            props: Dict[str, Any] = result.get("properties") or {}

            leak_hit = _is_leak_dataset(dataset)
            pep_hit = _is_pep(result)

            # Only keep results that are meaningful for our use-case
            if not leak_hit and not pep_hit:
                continue

            country_list = props.get("country") or props.get("jurisdiction") or []
            country = country_list[0] if country_list else ""

            entity_id = result.get("id", "")
            hits.append({
                "name": result.get("caption") or (props.get("name") or [""])[0],
                "entity_type": result.get("schema", ""),
                "dataset_id": dataset.get("id", ""),
                "dataset_label": dataset.get("label", ""),
                "is_leak_db_hit": leak_hit,
                "is_pep": pep_hit,
                "score": result.get("score", 0.0),
                "source_url": f"https://aleph.occrp.org/entities/{entity_id}" if entity_id else "",
                "country": country,
            })

        logger.info(
            f"AlephService: {len(hits)} relevant hits "
            f"({sum(1 for h in hits if h['is_leak_db_hit'])} leak, "
            f"{sum(1 for h in hits if h['is_pep'])} PEP) "
            f"for '{entity_name}'"
        )
        return hits

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers, adding ApiKey auth if a key is configured."""
        headers: Dict[str, str] = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        return headers

    def _fetch(self, entity_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Make the Aleph search API call.

        Returns the raw 'results' list, or None on any HTTP / parsing error.
        Empty list returned (not None) if the call succeeds but has 0 results.
        """
        params: Dict[str, Any] = {
            "q": entity_name,
            "limit": 20,
        }
        try:
            resp = requests.get(
                _ALEPH_SEARCH_URL,
                headers=self._build_headers(),
                params=params,
                timeout=20,
            )
        except requests.RequestException as exc:
            logger.warning(f"AlephService: request failed for '{entity_name}': {exc}")
            return None

        if resp.status_code == 429:
            logger.warning(f"AlephService: rate limited (429) for '{entity_name}'")
            return None

        if not resp.ok:
            logger.warning(
                f"AlephService: HTTP {resp.status_code} for '{entity_name}': "
                f"{resp.text[:200]}"
            )
            return None

        try:
            data = resp.json()
        except ValueError:
            logger.warning(f"AlephService: non-JSON response for '{entity_name}'")
            return None

        return data.get("results", [])


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_aleph_service: Optional[AlephService] = None


def get_aleph_service() -> AlephService:
    """Get or create the singleton AlephService instance."""
    global _aleph_service
    if _aleph_service is None:
        _aleph_service = AlephService()
    return _aleph_service
