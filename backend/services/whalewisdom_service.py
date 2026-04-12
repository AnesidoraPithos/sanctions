"""
WhaleWisdom Service

Fetches institutional investor data (13F filings) from WhaleWisdom.
Returns top shareholders in the standard internal shareholder schema so they
flow directly into network_service.build_network_graph() as shareholder nodes.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://whalewisdom.com"


class WhaleWisdomService:
    """
    Fetches 13F institutional holder data from WhaleWisdom.

    Output conforms to the internal shareholder schema expected by
    network_service.build_network_graph() and is compatible with the
    parallel sanctions screening step in search_routes.py.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("WHALEWISDOM_API_KEY", "")
        if self.api_key:
            logger.info("WhaleWisdomService initialised with API key")
        else:
            logger.info("WhaleWisdomService initialised — no API key (will skip gracefully)")

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def get_institutional_shareholders(
        self,
        company_name: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Return the top institutional shareholders for a company.

        Args:
            company_name: Company name to look up (resolved to ticker internally).
            limit: Maximum number of institutional holders to return (default 10).

        Returns:
            {
                'shareholders': List[Dict],   # In internal shareholder schema
                'company_info': Optional[Dict],
                'warnings': List[Dict]
            }
        """
        warnings: List[Dict[str, Any]] = []

        if not self.api_key:
            warnings.append({
                "source": "whalewisdom",
                "message": "WHALEWISDOM_API_KEY not configured — skipping institutional investor data",
                "severity": "info",
            })
            return {"shareholders": [], "company_info": None, "warnings": warnings}

        logger.info(f"WhaleWisdom: searching institutional shareholders for '{company_name}'")

        company_info = self._search_ticker(company_name)
        if not company_info:
            warnings.append({
                "source": "whalewisdom",
                "message": f"No WhaleWisdom ticker match found for '{company_name}' — skipping institutional data",
                "severity": "info",
            })
            return {"shareholders": [], "company_info": None, "warnings": warnings}

        ticker = company_info["ticker"]
        logger.info(f"WhaleWisdom: resolved '{company_name}' → {ticker}")

        raw_holders, rate_limited = self._fetch_holders(ticker, limit)

        if rate_limited:
            warnings.append({
                "source": "whalewisdom",
                "message": "WhaleWisdom API rate limit reached (429) — results may be incomplete",
                "severity": "warning",
            })

        shareholders = self._transform_holders(raw_holders, ticker)

        logger.info(
            f"WhaleWisdom: {len(shareholders)} institutional shareholders found for '{company_name}'"
        )

        return {
            "shareholders": shareholders,
            "company_info": company_info,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------ #
    # Private — HTTP                                                       #
    # ------------------------------------------------------------------ #

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Authenticated GET to WhaleWisdom.

        Returns:
            (response_json, rate_limited) — response_json is None on any error.
        """
        url = f"{_BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            resp = requests.get(url, headers=headers, params=params or {}, timeout=30)
        except requests.RequestException as exc:
            logger.warning(f"WhaleWisdom request failed [{endpoint}]: {exc}")
            return None, False

        if resp.status_code == 429:
            logger.warning(f"WhaleWisdom rate limit hit on {endpoint}")
            return None, True

        if resp.status_code in (402, 403):
            logger.warning(
                f"WhaleWisdom API plan does not cover {endpoint} (HTTP {resp.status_code})"
            )
            return None, False

        if resp.status_code == 404:
            logger.info(f"WhaleWisdom 404 for {endpoint}")
            return None, False

        if not resp.ok:
            logger.warning(
                f"WhaleWisdom returned HTTP {resp.status_code} for {endpoint}: "
                f"{resp.text[:200]}"
            )
            return None, False

        try:
            return resp.json(), False
        except ValueError:
            logger.warning(f"WhaleWisdom returned non-JSON for {endpoint}")
            return None, False

    # ------------------------------------------------------------------ #
    # Private — data fetching                                              #
    # ------------------------------------------------------------------ #

    def _search_ticker(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Resolve a company name to ticker and WhaleWisdom metadata."""
        data, _ = self._make_request(
            "/search.json",
            params={"q": company_name, "type": "stock"},
        )
        if not data:
            return None

        # API may return a list directly or under a 'results' key
        results: List[Dict[str, Any]] = (
            data if isinstance(data, list) else data.get("results", [])
        )
        if not results:
            return None

        best = results[0]
        ticker = best.get("ticker") or best.get("symbol") or ""
        if not ticker:
            return None

        return {
            "ticker": ticker.upper(),
            "name": best.get("name", company_name),
            "sector": best.get("sector", ""),
            "exchange": best.get("exchange", ""),
        }

    def _fetch_holders(
        self,
        ticker: str,
        limit: int,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Fetch raw 13F holder records from WhaleWisdom."""
        data, rate_limited = self._make_request(
            f"/stock/{ticker}/holders.json",
            params={"minimum_percent": 0, "type": "all", "limit": limit},
        )
        if data is None:
            return [], rate_limited

        # API may wrap results under 'holders', 'results', or return a list
        if isinstance(data, list):
            return data[:limit], False

        holders: List[Dict[str, Any]] = data.get("holders") or data.get("results") or []
        return holders[:limit], False

    # ------------------------------------------------------------------ #
    # Private — schema transformation                                      #
    # ------------------------------------------------------------------ #

    def _transform_holders(
        self,
        raw_holders: List[Dict[str, Any]],
        ticker: str,
    ) -> List[Dict[str, Any]]:
        """
        Map raw WhaleWisdom holder records to the internal shareholder schema.

        The output must match what network_service.build_network_graph() expects
        so results can be merged directly into the shareholders list in
        search_routes.py without further adaptation.
        """
        source_url = f"{_BASE_URL}/stock/{ticker.lower()}"
        result: List[Dict[str, Any]] = []

        for holder in raw_holders:
            name = (
                holder.get("fund_name")
                or holder.get("name")
                or holder.get("holder_name")
                or ""
            ).strip()
            if not name:
                continue

            ownership_pct = float(
                holder.get("percent_of_portfolio")
                or holder.get("ownership_pct")
                or holder.get("percentage")
                or 0.0
            )
            shares_held = int(
                holder.get("shares")
                or holder.get("shares_held")
                or holder.get("quantity")
                or 0
            )
            filing_date: str = (
                holder.get("filing_date")
                or holder.get("quarter_end")
                or holder.get("report_date")
                or ""
            )
            jurisdiction: str = holder.get("country") or "United States"

            result.append({
                "name": name,
                "shareholder_type": "Company",
                "ownership_percentage": ownership_pct,
                "shares_held": shares_held,
                "voting_rights": ownership_pct,  # 13F doesn't separate voting rights
                "jurisdiction": jurisdiction,
                "filing_date": filing_date,
                "source_url": source_url,
                "sanctions_hit": 0,  # Populated by parallel screening in search_routes.py
                "source": "whalewisdom",
            })

        return result


# ------------------------------------------------------------------ #
# Singleton                                                           #
# ------------------------------------------------------------------ #

_whalewisdom_service: Optional[WhaleWisdomService] = None


def get_whalewisdom_service() -> WhaleWisdomService:
    """Return the shared WhaleWisdomService instance."""
    global _whalewisdom_service
    if _whalewisdom_service is None:
        _whalewisdom_service = WhaleWisdomService()
    return _whalewisdom_service
