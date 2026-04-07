"""
Conglomerate Service

Handles corporate structure discovery and financial intelligence extraction.
Wraps agents/research_agent.py and core/database.py for network tier research.

Fallback Strategy:
1. SEC EDGAR (no API key needed) - Best for US public companies
2. OpenCorporates API (requires API key) - Skip if key unavailable
3. Wikipedia + DuckDuckGo (no API key needed) - Always available fallback
"""

import logging
from typing import Dict, Any, List, Optional

from services.research_agent import SanctionsResearchAgent
from db_operations.db import get_directors, get_shareholders, get_transactions
from config import settings

logger = logging.getLogger(__name__)


class ConglomerateService:
    """
    Service for discovering corporate structures and financial intelligence

    Reuses existing research_agent.py methods with graceful API key handling
    """

    def __init__(self):
        """Initialize conglomerate service with research agent"""
        # SanctionsResearchAgent reads API keys from environment variables
        self.research_agent = SanctionsResearchAgent()
        logger.info("ConglomerateService initialized")

    def discover_subsidiaries(
        self,
        parent_company: str,
        depth: int = 1,
        ownership_threshold: int = 0,
        include_sisters: bool = True,
        max_level_2_searches: int = 20,
        max_level_3_searches: int = 10
    ) -> Dict[str, Any]:
        """
        Multi-source subsidiary discovery with graceful fallback

        Fallback strategy (tries in order, skips if API key missing):
        1. SEC EDGAR (no API key needed) - Best for US public companies
        2. OpenCorporates API (requires API key) - Skip if key unavailable
        3. Wikipedia + DuckDuckGo (no API key needed) - Always available fallback

        Args:
            parent_company: Name of the parent company to search
            depth: Search depth (1-3 levels of subsidiaries)
            ownership_threshold: Minimum ownership percentage (0-100)
            include_sisters: Whether to include sister companies
            max_level_2_searches: Max subsidiaries to search for level 2 (default: 20)
            max_level_3_searches: Max subsidiaries to search for level 3 (default: 10)

        Returns:
            dict: {
                'subsidiaries': List of subsidiary dicts,
                'sisters': List of sister company dicts,
                'parent': Parent company dict or None,
                'method': 'api' or 'sec_edgar' or 'wikipedia+duckduckgo',
                'source_url': URL of the data source,
                'warnings': List of warning messages
            }
        """
        logger.info(
            f"Starting conglomerate search for '{parent_company}' "
            f"(depth={depth}, ownership_threshold={ownership_threshold}%, "
            f"include_sisters={include_sisters}, max_level_2_searches={max_level_2_searches}, "
            f"max_level_3_searches={max_level_3_searches})"
        )

        warnings = []

        # Check if OpenCorporates API key is available
        # The research agent reads from environment variable directly
        if not os.getenv('OPENCORPORATES_API_KEY'):
            warnings.append({
                "source": "opencorporates",
                "message": "OpenCorporates API key not configured - skipping",
                "severity": "info"
            })
            logger.warning("OpenCorporates API key not configured - will use fallback methods")

        # Call research agent's find_subsidiaries method
        # This already implements the fallback strategy
        try:
            results = self.research_agent.find_subsidiaries(
                parent_company_name=parent_company,
                depth=depth,
                include_sisters=include_sisters,
                ownership_threshold=ownership_threshold,
                max_level_2_searches=max_level_2_searches,
                max_level_3_searches=max_level_3_searches
            )

            # Add data sources used
            # Prefer data_sources_tried from research_agent (full transparency)
            data_sources_used = results.get('data_sources_tried', [])

            if not data_sources_used:
                # Fallback if old version of research_agent doesn't provide data_sources_tried
                data_sources = []
                method = results.get('method', 'unknown')

                if method == 'api':
                    data_sources.append('opencorporates')
                elif 'sec_edgar' in method:  # FIXED: matches 'sec_edgar_10k', 'sec_edgar_20f', etc.
                    data_sources.append('sec_edgar')
                elif 'wikipedia' in method:
                    data_sources.extend(['wikipedia', 'duckduckgo'])
                elif method == 'duckduckgo':
                    data_sources.append('duckduckgo')

                data_sources_used = data_sources

            results['data_sources_used'] = data_sources_used
            results['warnings'] = warnings

            logger.info(
                f"Conglomerate search complete: "
                f"{len(results.get('subsidiaries', []))} subsidiaries, "
                f"{len(results.get('sisters', []))} sisters found "
                f"using {results.get('method', 'unknown')} method"
            )

            return results

        except Exception as e:
            logger.error(f"Conglomerate search failed: {str(e)}", exc_info=True)
            # Return empty results with error warning
            return {
                'subsidiaries': [],
                'sisters': [],
                'parent': None,
                'method': 'error',
                'source_url': None,
                'data_sources_used': [],
                'warnings': warnings + [{
                    "source": "conglomerate_service",
                    "message": f"Subsidiary search failed: {str(e)}",
                    "severity": "error"
                }]
            }

    def extract_financial_intelligence(
        self,
        company_name: str,
        cik: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract directors, shareholders, transactions from SEC filings

        No API key required - uses public SEC EDGAR database

        Args:
            company_name: Name of the company
            cik: Company CIK (optional, improves accuracy)

        Returns:
            dict: {
                'directors': List of director dicts,
                'shareholders': List of shareholder dicts,
                'transactions': List of transaction dicts,
                'warnings': List of warning messages
            }
        """
        logger.info(f"Extracting financial intelligence for '{company_name}'")

        warnings = []

        try:
            # Get directors from database
            directors = get_directors(company_name=company_name, cik=cik)
            logger.info(f"Found {len(directors)} directors")

            # Get shareholders from database
            shareholders = get_shareholders(company_name=company_name, cik=cik)
            logger.info(f"Found {len(shareholders)} shareholders")

            # Get transactions from database
            transactions = get_transactions(company_name=company_name, cik=cik)
            logger.info(f"Found {len(transactions)} transactions")

            # Add warnings if no financial intelligence data found
            if not directors and not shareholders and not transactions:
                warnings.append({
                    "source": "sec_edgar_financial_intelligence",
                    "message": f"No directors, shareholders, or transactions found in SEC filings for '{company_name}'. Note: Subsidiary data may still be available from other sections of the filing.",
                    "severity": "info"
                })

            return {
                'directors': directors,
                'shareholders': shareholders,
                'transactions': transactions,
                'warnings': warnings
            }

        except Exception as e:
            logger.error(f"Financial intelligence extraction failed: {str(e)}", exc_info=True)
            return {
                'directors': [],
                'shareholders': [],
                'transactions': [],
                'warnings': [{
                    "source": "financial_intelligence",
                    "message": f"Failed to extract financial data: {str(e)}",
                    "severity": "error"
                }]
            }

    def search_sec_edgar_for_cik(self, company_name: str) -> Optional[str]:
        """
        Search SEC EDGAR for company CIK number

        Args:
            company_name: Name of the company

        Returns:
            str: CIK number if found, None otherwise
        """
        try:
            logger.info(f"Searching SEC EDGAR for CIK: {company_name}")
            cik = self.research_agent.search_sec_edgar_cik(company_name)

            if cik:
                logger.info(f"Found CIK for '{company_name}': {cik}")
                return cik
            else:
                logger.info(f"No CIK found for '{company_name}'")
                return None

        except Exception as e:
            logger.error(f"SEC EDGAR CIK search failed: {str(e)}", exc_info=True)
            return None


# Singleton instance
_conglomerate_service = None


def get_conglomerate_service() -> ConglomerateService:
    """Get or create singleton conglomerate service instance"""
    global _conglomerate_service
    if _conglomerate_service is None:
        _conglomerate_service = ConglomerateService()
    return _conglomerate_service
