"""
Companies House Service

Fetches UK company intelligence (Officers and Persons with Significant Control)
from the Companies House public API.

API docs: https://developer-specs.company-information.service.gov.uk/
Authentication: HTTP Basic Auth — API key as username, empty password.
Rate limit: 600 requests per 5 minutes.

Transforms raw CH data into the same internal schema used by
ConglomerateService.extract_financial_intelligence(), so the output can be
merged directly into the directors/shareholders lists consumed by
NetworkService.build_network_graph().
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Maps Companies House officer_role values to human-readable titles
_ROLE_MAP: Dict[str, str] = {
    "director": "Director",
    "secretary": "Company Secretary",
    "llp-designated-member": "Designated Member",
    "llp-member": "LLP Member",
    "corporate-director": "Corporate Director",
    "corporate-secretary": "Corporate Secretary",
    "corporate-member": "Corporate Member",
    "judicial-factor": "Judicial Factor",
    "receiver-and-manager": "Receiver and Manager",
    "cic-manager": "CIC Manager",
    "nominee-director": "Nominee Director",
    "nominee-secretary": "Nominee Secretary",
}

# Ownership percentage midpoints for Companies House natures_of_control bands
_OWNERSHIP_BANDS: List[tuple] = [
    ("75-to-100-percent", 87.5),
    ("50-to-75-percent", 62.5),
    ("25-to-50-percent", 37.5),
    ("more-than-25-percent", 25.0),
]


def _normalise_role(raw_role: str) -> str:
    """Convert a CH officer_role slug to a display title."""
    return _ROLE_MAP.get(raw_role, raw_role.replace("-", " ").title())


def _parse_ownership_pct(natures_of_control: List[str], prefix: str) -> float:
    """
    Extract an ownership/voting percentage from a natures_of_control list.

    Args:
        natures_of_control: List of CH control nature strings.
        prefix: Either "ownership-of-shares" or "voting-rights".

    Returns:
        Midpoint percentage as a float, or 0.0 if not determinable.
    """
    for clause in natures_of_control:
        if prefix not in clause:
            continue
        for band_key, midpoint in _OWNERSHIP_BANDS:
            if band_key in clause:
                return midpoint
    return 0.0


class CompaniesHouseService:
    """
    Service for fetching UK company intelligence from Companies House API.

    Returns data in the same schema as ConglomerateService.extract_financial_intelligence()
    so results can be merged directly into the network tier pipeline.
    """

    BASE_URL = "https://api.company-information.service.gov.uk"

    def __init__(self) -> None:
        self.api_key = os.getenv("COMPANIES_HOUSE_API_KEY", "")
        if self.api_key:
            logger.info("CompaniesHouseService initialised with API key")
        else:
            logger.info("CompaniesHouseService initialised — no API key, will skip gracefully")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_company_intelligence(self, entity_name: str) -> Dict[str, Any]:
        """
        Search for a UK company by name and return its officers and PSC data
        in the internal financial intelligence schema.

        Args:
            entity_name: Company name to search for.

        Returns:
            dict: {
                'directors': list of director dicts (matches SEC EDGAR schema),
                'shareholders': list of shareholder dicts (PSC, matches SEC EDGAR schema),
                'company_info': dict with CH company metadata, or None,
                'warnings': list of warning dicts
            }
        """
        warnings: List[Dict[str, Any]] = []

        if not self.api_key:
            warnings.append({
                "source": "companies_house",
                "message": "COMPANIES_HOUSE_API_KEY not configured — skipping UK corporate data",
                "severity": "info",
            })
            return {"directors": [], "shareholders": [], "company_info": None, "warnings": warnings}

        logger.info(f"Companies House search for '{entity_name}'")

        # Step 1: resolve company number
        company_info = self._search_company(entity_name)
        if company_info is None:
            warnings.append({
                "source": "companies_house",
                "message": f"No Companies House match found for '{entity_name}'",
                "severity": "info",
            })
            return {"directors": [], "shareholders": [], "company_info": None, "warnings": warnings}

        company_number = company_info["company_number"]
        logger.info(
            f"Resolved '{entity_name}' to Companies House number {company_number} "
            f"({company_info['name']})"
        )

        # Step 2: fetch officers and PSC in parallel-ish (sequential is fine here)
        raw_officers, rate_limited_officers = self._get_officers(company_number)
        raw_pscs, rate_limited_pscs = self._get_pscs(company_number)

        if rate_limited_officers or rate_limited_pscs:
            warnings.append({
                "source": "companies_house",
                "message": "Companies House API rate limit reached (429) — partial data returned",
                "severity": "warning",
            })

        # Step 3: transform to internal schema
        directors = self._transform_officers(raw_officers, company_number)
        shareholders = self._transform_pscs(raw_pscs, company_number)

        logger.info(
            f"Companies House: {len(directors)} officers, {len(shareholders)} PSC entries "
            f"for {company_number}"
        )

        return {
            "directors": directors,
            "shareholders": shareholders,
            "company_info": company_info,
            "warnings": warnings,
        }

    # ------------------------------------------------------------------
    # Private helpers — HTTP
    # ------------------------------------------------------------------

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> tuple[Optional[Dict[str, Any]], bool]:
        """
        Make an authenticated GET request to the Companies House API.

        Returns:
            (response_json, rate_limited) — response_json is None on any error.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            resp = requests.get(
                url,
                auth=HTTPBasicAuth(self.api_key, ""),
                params=params or {},
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.warning(f"Companies House request failed for {endpoint}: {exc}")
            return None, False

        if resp.status_code == 429:
            logger.warning(f"Companies House rate limit hit on {endpoint}")
            return None, True

        if resp.status_code == 404:
            logger.info(f"Companies House 404 for {endpoint}")
            return None, False

        if not resp.ok:
            logger.warning(
                f"Companies House returned {resp.status_code} for {endpoint}: {resp.text[:200]}"
            )
            return None, False

        try:
            return resp.json(), False
        except ValueError:
            logger.warning(f"Companies House returned non-JSON for {endpoint}")
            return None, False

    # ------------------------------------------------------------------
    # Private helpers — data fetching
    # ------------------------------------------------------------------

    def _search_company(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Search Companies House for a company by name.

        Prefers active companies; falls back to the first result if none are active.

        Returns:
            dict with company_number, name, company_status, address_snippet,
            date_of_creation — or None if not found.
        """
        data, _ = self._make_request("/search/companies", params={"q": name, "items_per_page": 5})
        if not data:
            return None

        items: List[Dict[str, Any]] = data.get("items", [])
        if not items:
            return None

        # Prefer first active result
        chosen = next(
            (item for item in items if item.get("company_status") == "active"), items[0]
        )

        return {
            "company_number": chosen["company_number"],
            "name": chosen.get("title", name),
            "company_status": chosen.get("company_status", ""),
            "address_snippet": chosen.get("address_snippet", ""),
            "date_of_creation": chosen.get("date_of_creation", ""),
        }

    def _get_officers(self, company_number: str) -> tuple[List[Dict[str, Any]], bool]:
        """
        Fetch active officers for a company.

        Returns:
            (officers_list, rate_limited)
        """
        data, rate_limited = self._make_request(
            f"/company/{company_number}/officers",
            params={"items_per_page": 100},
        )
        if data is None:
            return [], rate_limited

        all_items: List[Dict[str, Any]] = data.get("items", [])
        # Exclude resigned officers
        active = [item for item in all_items if not item.get("resigned_on")]
        return active, False

    def _get_pscs(self, company_number: str) -> tuple[List[Dict[str, Any]], bool]:
        """
        Fetch active Persons with Significant Control for a company.

        Returns:
            (pscs_list, rate_limited)
        """
        data, rate_limited = self._make_request(
            f"/company/{company_number}/persons-with-significant-control",
            params={"items_per_page": 100},
        )
        if data is None:
            return [], rate_limited

        all_items: List[Dict[str, Any]] = data.get("items", [])
        # Exclude ceased PSCs
        active = [item for item in all_items if not item.get("ceased_on")]
        return active, False

    # ------------------------------------------------------------------
    # Private helpers — schema transformation
    # ------------------------------------------------------------------

    def _transform_officers(
        self, officers: List[Dict[str, Any]], company_number: str
    ) -> List[Dict[str, Any]]:
        """
        Map raw Companies House officer records to the internal director schema.

        Output schema matches ConglomerateService.extract_financial_intelligence()
        directors list so both sources can be merged without further mapping.
        """
        source_url = (
            f"https://find-and-update.company-information.service.gov.uk"
            f"/company/{company_number}/officers"
        )
        result = []
        for officer in officers:
            result.append({
                "name": officer.get("name", ""),
                "title": _normalise_role(officer.get("officer_role", "")),
                "nationality": officer.get("nationality", ""),
                "biography": "",
                "other_positions": "",
                "filing_date": officer.get("appointed_on", ""),
                "source_url": source_url,
                "sanctions_hit": 0,
                "source": "companies_house",
            })
        return result

    def _transform_pscs(
        self, pscs: List[Dict[str, Any]], company_number: str
    ) -> List[Dict[str, Any]]:
        """
        Map raw Companies House PSC records to the internal shareholder schema.

        Output schema matches ConglomerateService.extract_financial_intelligence()
        shareholders list so both sources can be merged without further mapping.
        """
        source_url = (
            f"https://find-and-update.company-information.service.gov.uk"
            f"/company/{company_number}/persons-with-significant-control"
        )
        result = []
        for psc in pscs:
            kind = psc.get("kind", "")
            natures = psc.get("natures_of_control", [])
            shareholder_type = "Individual" if "individual" in kind else "Company"
            jurisdiction = psc.get("country_of_residence") or psc.get("nationality", "")

            result.append({
                "name": psc.get("name", ""),
                "shareholder_type": shareholder_type,
                "ownership_percentage": _parse_ownership_pct(natures, "ownership-of-shares"),
                "voting_rights": _parse_ownership_pct(natures, "voting-rights"),
                "jurisdiction": jurisdiction,
                "filing_date": psc.get("notified_on", ""),
                "source_url": source_url,
                "sanctions_hit": 0,
                "source": "companies_house",
            })
        return result


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------

_companies_house_service: Optional[CompaniesHouseService] = None


def get_companies_house_service() -> CompaniesHouseService:
    """Get or create the singleton CompaniesHouseService instance."""
    global _companies_house_service
    if _companies_house_service is None:
        _companies_house_service = CompaniesHouseService()
    return _companies_house_service
