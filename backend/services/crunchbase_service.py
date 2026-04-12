"""
Crunchbase Service

Fetches private company intelligence (board members, funding rounds, lead investors)
from the Crunchbase API v4.

API docs: https://data.crunchbase.com/docs/using-the-api
Authentication: user_key query parameter on every request.
Rate limit: 200 requests per minute on standard plans.

Transforms raw Crunchbase data into the same internal schema used by
ConglomerateService.extract_financial_intelligence(), so the output can be
merged directly into the directors/shareholders lists consumed by
NetworkService.build_network_graph().

Board members  → directors  list (node_type: director,  edge: director_of)
Lead investors → shareholders list (node_type: shareholder, edge: shareholder_of)
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Crunchbase investment_type values that represent equity rounds worth surfacing
_EQUITY_ROUND_TYPES = {
    "angel",
    "convertible_note",
    "corporate_round",
    "equity_crowdfunding",
    "initial_coin_offering",
    "post_ipo_equity",
    "pre_seed",
    "private_equity",
    "product_crowdfunding",
    "secondary_market",
    "seed",
    "series_a",
    "series_b",
    "series_c",
    "series_d",
    "series_e",
    "series_f",
    "series_g",
    "series_h",
    "series_i",
    "series_j",
    "series_unknown",
    "undisclosed",
}


class CrunchbaseService:
    """
    Service for fetching private company intelligence from the Crunchbase API v4.

    Returns data in the same schema as ConglomerateService.extract_financial_intelligence()
    so results can be merged directly into the network tier pipeline.
    """

    BASE_URL = "https://api.crunchbase.com/api/v4"

    def __init__(self) -> None:
        self.api_key = os.getenv("CRUNCHBASE_API_KEY", "")
        if self.api_key:
            logger.info("CrunchbaseService initialised with API key")
        else:
            logger.info("CrunchbaseService initialised — no API key, will skip gracefully")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_company_intelligence(self, entity_name: str) -> Dict[str, Any]:
        """
        Search for a company by name and return its board members and lead investors
        in the internal financial intelligence schema.

        Args:
            entity_name: Company name to search for.

        Returns:
            dict: {
                'directors': list of board member dicts (matches SEC EDGAR director schema),
                'shareholders': list of lead investor dicts (matches SEC EDGAR shareholder schema),
                'funding_rounds': list of raw funding round dicts,
                'company_info': dict with Crunchbase company metadata, or None,
                'warnings': list of warning dicts
            }
        """
        warnings: List[Dict[str, Any]] = []

        if not self.api_key:
            warnings.append({
                "source": "crunchbase",
                "message": "CRUNCHBASE_API_KEY not configured — skipping Crunchbase data",
                "severity": "info",
            })
            return {
                "directors": [],
                "shareholders": [],
                "funding_rounds": [],
                "company_info": None,
                "warnings": warnings,
            }

        logger.info(f"Crunchbase search for '{entity_name}'")

        # Step 1: resolve org permalink
        permalink = self._search_org(entity_name)
        if permalink is None:
            warnings.append({
                "source": "crunchbase",
                "message": f"No Crunchbase match found for '{entity_name}'",
                "severity": "info",
            })
            return {
                "directors": [],
                "shareholders": [],
                "funding_rounds": [],
                "company_info": None,
                "warnings": warnings,
            }

        logger.info(f"Resolved '{entity_name}' to Crunchbase permalink '{permalink}'")

        # Step 2: fetch entity with board + funding round cards in a single call
        entity_data, rate_limited = self._get_org_entity(permalink)

        if rate_limited:
            warnings.append({
                "source": "crunchbase",
                "message": "Crunchbase API rate limit reached (429) — data unavailable for this search",
                "severity": "warning",
            })
            return {
                "directors": [],
                "shareholders": [],
                "funding_rounds": [],
                "company_info": None,
                "warnings": warnings,
            }

        if entity_data is None:
            warnings.append({
                "source": "crunchbase",
                "message": f"Failed to retrieve Crunchbase entity data for '{entity_name}'",
                "severity": "warning",
            })
            return {
                "directors": [],
                "shareholders": [],
                "funding_rounds": [],
                "company_info": None,
                "warnings": warnings,
            }

        # Step 3: extract cards
        cards = entity_data.get("cards", {})
        board_card = cards.get("board_members_and_advisors", [])
        rounds_card = cards.get("funding_rounds", [])

        # Step 4: transform to internal schema
        directors = self._transform_board_members(board_card, permalink)
        shareholders, funding_rounds_raw = self._transform_funding_rounds(rounds_card, permalink)

        # Step 5: build company_info summary
        props = entity_data.get("properties", {})
        company_info: Optional[Dict[str, Any]] = {
            "permalink": permalink,
            "name": props.get("short_description", entity_name),
            "website_url": props.get("website_url", ""),
            "founded_on": (props.get("founded_on") or {}).get("value", ""),
            "num_funding_rounds": props.get("num_funding_rounds", 0),
            "crunchbase_url": f"https://www.crunchbase.com/organization/{permalink}",
        }

        logger.info(
            f"Crunchbase: {len(directors)} board members, {len(shareholders)} lead investors, "
            f"{len(funding_rounds_raw)} funding rounds for '{permalink}'"
        )

        return {
            "directors": directors,
            "shareholders": shareholders,
            "funding_rounds": funding_rounds_raw,
            "company_info": company_info,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Private helpers — HTTP
    # ------------------------------------------------------------------

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Make an authenticated request to the Crunchbase API.

        Args:
            method: HTTP method ('GET' or 'POST').
            endpoint: API path (e.g. '/searches/organizations').
            params: Query parameters (user_key is injected automatically).
            json: JSON request body for POST requests.

        Returns:
            (response_json, rate_limited) — response_json is None on any error.
        """
        url = f"{self.BASE_URL}{endpoint}"
        query_params = {"user_key": self.api_key}
        if params:
            query_params.update(params)

        try:
            resp = requests.request(
                method,
                url,
                params=query_params,
                json=json,
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.warning(f"Crunchbase request failed for {endpoint}: {exc}")
            return None, False

        if resp.status_code == 429:
            logger.warning(f"Crunchbase rate limit hit on {endpoint}")
            return None, True

        if resp.status_code == 404:
            logger.info(f"Crunchbase 404 for {endpoint}")
            return None, False

        if not resp.ok:
            logger.warning(
                f"Crunchbase returned {resp.status_code} for {endpoint}: {resp.text[:200]}"
            )
            return None, False

        try:
            return resp.json(), False
        except ValueError:
            logger.warning(f"Crunchbase returned non-JSON for {endpoint}")
            return None, False

    # ------------------------------------------------------------------
    # Private helpers — data fetching
    # ------------------------------------------------------------------

    def _search_org(self, entity_name: str) -> Optional[str]:
        """
        Search for an organisation by name and return its permalink.

        Uses the Crunchbase autocomplete endpoint for speed; falls back to the
        full search endpoint if no autocomplete result is found.

        Returns:
            permalink string (e.g. 'stripe') or None if not found.
        """
        # Try autocomplete first — faster and more name-accurate
        data, _ = self._make_request(
            "GET",
            "/autocompletes",
            params={"query": entity_name, "collection_ids": "organizations", "limit": 5},
        )
        if data:
            entities = data.get("entities", [])
            if entities:
                return entities[0].get("identifier", {}).get("permalink")

        # Fall back to full search
        body = {
            "field_ids": ["short_description", "permalink"],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "facet_ids",
                    "operator_id": "includes",
                    "values": ["company"],
                },
                {
                    "type": "predicate",
                    "field_id": "name",
                    "operator_id": "contains",
                    "values": [entity_name],
                },
            ],
            "limit": 5,
        }
        data, _ = self._make_request("POST", "/searches/organizations", json=body)
        if not data:
            return None

        entities = data.get("entities", [])
        if not entities:
            return None

        return entities[0].get("identifier", {}).get("permalink")

    def _get_org_entity(
        self, permalink: str
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Fetch full organisation entity with board and funding round cards.

        A single API call returns:
        - properties: metadata fields (description, website, founded_on, etc.)
        - cards.board_members_and_advisors: current board members
        - cards.funding_rounds: all funding rounds with lead_investors

        Returns:
            (entity_data, rate_limited)
        """
        return self._make_request(
            "GET",
            f"/entities/organizations/{permalink}",
            params={
                "field_ids": "short_description,website_url,founded_on,num_funding_rounds",
                "card_ids": "board_members_and_advisors,funding_rounds",
            },
        )

    # ------------------------------------------------------------------
    # Private helpers — schema transformation
    # ------------------------------------------------------------------

    def _transform_board_members(
        self, card_data: List[Dict[str, Any]], permalink: str
    ) -> List[Dict[str, Any]]:
        """
        Map raw Crunchbase board_members_and_advisors card entries to the
        internal director schema.

        Output matches ConglomerateService.extract_financial_intelligence()
        directors list so both sources can be merged without further mapping.
        """
        source_url = f"https://www.crunchbase.com/organization/{permalink}/people"
        result = []

        for member in card_data:
            person = member.get("person_identifier") or {}
            name = person.get("value", "")
            if not name:
                continue

            job_title = member.get("title", "") or "Board Member"
            started_on_obj = member.get("started_on") or {}
            started_on = started_on_obj.get("value", "")

            result.append({
                "name": name,
                "title": job_title,
                "nationality": "",
                "biography": "",
                "other_positions": "",
                "filing_date": started_on,
                "source_url": source_url,
                "sanctions_hit": 0,
                "source": "crunchbase",
            })

        return result

    def _transform_funding_rounds(
        self, card_data: List[Dict[str, Any]], permalink: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Map raw Crunchbase funding_rounds card entries to lead investor shareholder
        records, and return the raw round data alongside.

        Each lead investor per round becomes a shareholder record. Non-lead investors
        are omitted to keep the graph focused on significant relationships.

        Output schema matches ConglomerateService.extract_financial_intelligence()
        shareholders list so both sources can be merged without further mapping.

        Returns:
            (shareholders, funding_rounds_raw)
        """
        source_url = f"https://www.crunchbase.com/organization/{permalink}/funding_rounds"
        shareholders: List[Dict[str, Any]] = []
        funding_rounds_raw: List[Dict[str, Any]] = []
        seen_investors: set = set()  # deduplicate across rounds

        for round_data in card_data:
            investment_type = round_data.get("investment_type", "")
            if investment_type not in _EQUITY_ROUND_TYPES:
                continue

            announced_obj = round_data.get("announced_on") or {}
            announced_on = announced_obj.get("value", "")

            money_raised = round_data.get("money_raised") or {}
            amount_usd = money_raised.get("value_usd", 0) or 0

            round_identifier = round_data.get("identifier") or {}
            round_name = round_identifier.get("value", investment_type)

            funding_rounds_raw.append({
                "round_name": round_name,
                "investment_type": investment_type,
                "announced_on": announced_on,
                "amount_usd": amount_usd,
            })

            # Extract lead investors from this round
            lead_investors: List[Dict[str, Any]] = round_data.get("lead_investors") or []
            for investor in lead_investors:
                investor_name = investor.get("value", "")
                if not investor_name or investor_name in seen_investors:
                    continue

                seen_investors.add(investor_name)

                # Crunchbase entity_def_id distinguishes org vs person
                entity_def = investor.get("entity_def_id", "organization")
                shareholder_type = "Individual" if entity_def == "person" else "Company"

                shareholders.append({
                    "name": investor_name,
                    "shareholder_type": shareholder_type,
                    "ownership_percentage": 0.0,
                    "voting_rights": 0.0,
                    "jurisdiction": "",
                    "filing_date": announced_on,
                    "source_url": source_url,
                    "sanctions_hit": 0,
                    "source": "crunchbase",
                    # Extra context — passed through to Cytoscape node data via **attrs
                    "funding_round_type": investment_type,
                    "funding_amount_usd": amount_usd,
                    "is_lead_investor": True,
                })

        return shareholders, funding_rounds_raw


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_crunchbase_service: Optional[CrunchbaseService] = None


def get_crunchbase_service() -> CrunchbaseService:
    """Get or create the singleton CrunchbaseService instance."""
    global _crunchbase_service
    if _crunchbase_service is None:
        _crunchbase_service = CrunchbaseService()
    return _crunchbase_service
