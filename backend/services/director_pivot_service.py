"""
Director Pivot Service — Phase 4

Discovers interlocking directorates via SEC EDGAR full-text search.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

EDGAR_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


class DirectorPivotService:
    """Find companies interlocked through shared directors via SEC EDGAR."""

    def find_director_companies(self, name: str) -> List[Dict[str, Any]]:
        """Search SEC EDGAR for filings mentioning this director.

        Args:
            name: Director full name.

        Returns:
            List of dicts with company_name, cik, role, filing_date, source_url.
        """
        try:
            params = {
                "q": f'"{name}"',
                "forms": "DEF 14A,10-K",
                "dateRange": "custom",
                "startdt": "2020-01-01",
                "_source": "file_date,period_of_report,entity_name,file_num,form_type",
                "hits.hits.total.value": 1,
                "hits.hits._source.period_of_report": 1,
            }
            resp = requests.get(EDGAR_SEARCH_URL, params=params, timeout=15)
            if resp.status_code != 200:
                logger.warning(
                    "EDGAR full-text search returned %s for director %s",
                    resp.status_code,
                    name,
                )
                return []

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            results: List[Dict[str, Any]] = []
            seen: set[str] = set()

            for hit in hits[:10]:
                src = hit.get("_source", {})
                company = src.get("entity_name", "")
                cik = src.get("file_num", "")
                filing_date = src.get("period_of_report") or src.get("file_date", "")
                form_type = src.get("form_type", "")
                acc_no = hit.get("_id", "")
                source_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
                    f"&filenum={cik}&type={form_type}&dateb=&owner=include&count=40"
                    if cik
                    else ""
                )

                key = f"{company}:{cik}"
                if company and key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "company_name": company,
                            "cik": cik,
                            "role": None,
                            "filing_date": filing_date,
                            "source_url": source_url,
                        }
                    )

            return results

        except Exception as exc:
            logger.warning("EDGAR director search failed for %s: %s", name, exc)
            return []

    def pivot_directors(self, directors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find interlocked companies for each director (parallel, capped at 10).

        Args:
            directors: List of director dicts with at least a 'name' key.

        Returns:
            List of dicts with director_name, title, companies.
        """
        capped = directors[:10]
        results: List[Dict[str, Any]] = []

        def _fetch(director: Dict[str, Any]) -> Dict[str, Any]:
            name = director.get("name", "")
            title = director.get("title", "")
            companies = self.find_director_companies(name) if name else []
            return {"director_name": name, "title": title, "companies": companies}

        with ThreadPoolExecutor(max_workers=min(len(capped), 5)) as executor:
            futures = {executor.submit(_fetch, d): d for d in capped}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as exc:
                    director = futures[future]
                    logger.warning(
                        "Director pivot failed for %s: %s",
                        director.get("name"),
                        exc,
                    )

        return results
