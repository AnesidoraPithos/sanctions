"""
Infrastructure Correlation Service — Phase 4

WHOIS lookups on media-extracted domains; detects shared registrants.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InfrastructureService:
    """Correlate digital infrastructure via WHOIS lookups."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def extract_domains(self, urls: List[str]) -> List[str]:
        """Extract unique hostnames from a list of URLs."""
        seen: set[str] = set()
        domains: List[str] = []
        for url in urls:
            if not url:
                continue
            try:
                host = urlparse(url).hostname or ""
                # Strip www. prefix
                host = re.sub(r"^www\.", "", host.lower())
                if host and host not in seen:
                    seen.add(host)
                    domains.append(host)
            except Exception:
                pass
        return domains

    def whois_lookup(self, domain: str) -> Dict[str, Any]:
        """Perform a WHOIS lookup and return structured data.

        Args:
            domain: Hostname to query.

        Returns:
            Dict with registrant_org, registrar, creation_date, nameservers.
        """
        try:
            import whois  # type: ignore

            w = whois.whois(domain)
            nameservers: List[str] = []
            raw_ns = w.get("name_servers") or []
            if isinstance(raw_ns, str):
                raw_ns = [raw_ns]
            for ns in raw_ns:
                ns_clean = str(ns).lower().strip()
                if ns_clean and ns_clean not in nameservers:
                    nameservers.append(ns_clean)

            creation = w.get("creation_date")
            if isinstance(creation, list):
                creation = creation[0]
            creation_str = str(creation.date()) if hasattr(creation, "date") else (str(creation) if creation else None)

            return {
                "registrant_org": w.get("org") or w.get("registrant") or None,
                "registrar": w.get("registrar") or None,
                "creation_date": creation_str,
                "nameservers": nameservers[:5],
            }
        except Exception as exc:
            logger.debug("WHOIS failed for %s: %s", domain, exc)
            return {
                "registrant_org": None,
                "registrar": None,
                "creation_date": None,
                "nameservers": [],
            }

    def correlate_infrastructure(
        self, entity_name: str, urls: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract domains from URLs, WHOIS each (cap 15), group by shared registrant.

        Args:
            entity_name: Primary entity name (used to flag directly related domains).
            urls: List of article/source URLs from media intelligence.

        Returns:
            List of InfrastructureHit-compatible dicts.
        """
        domains = self.extract_domains(urls)[:15]
        if not domains:
            return []

        # Collect WHOIS data
        whois_data: List[Dict[str, Any]] = []
        for domain in domains:
            info = self.whois_lookup(domain)
            whois_data.append(
                {
                    "domain": domain,
                    "registrant_org": info["registrant_org"],
                    "registrar": info["registrar"],
                    "creation_date": info["creation_date"],
                    "nameservers": info["nameservers"],
                }
            )

        # Group by registrant_org to find related entities
        registrant_map: Dict[str, List[str]] = {}
        for item in whois_data:
            org = item.get("registrant_org")
            if org:
                registrant_map.setdefault(org, []).append(item["domain"])

        ns_map: Dict[str, List[str]] = {}
        for item in whois_data:
            for ns in item.get("nameservers", []):
                ns_root = ".".join(ns.rstrip(".").split(".")[-2:])
                ns_map.setdefault(ns_root, []).append(item["domain"])

        results: List[Dict[str, Any]] = []
        for item in whois_data:
            related: List[str] = []

            # Domains sharing the same registrant_org
            org = item.get("registrant_org")
            if org and org in registrant_map:
                related.extend(
                    [d for d in registrant_map[org] if d != item["domain"]]
                )

            # Domains sharing a nameserver root
            for ns in item.get("nameservers", []):
                ns_root = ".".join(ns.rstrip(".").split(".")[-2:])
                if ns_root in ns_map:
                    related.extend(
                        [d for d in ns_map[ns_root] if d != item["domain"]]
                    )

            # Deduplicate
            seen: set[str] = set()
            deduped: List[str] = []
            for r in related:
                if r not in seen:
                    seen.add(r)
                    deduped.append(r)

            results.append(
                {
                    "domain": item["domain"],
                    "registrant_org": item["registrant_org"],
                    "registrar": item["registrar"],
                    "creation_date": item["creation_date"],
                    "nameservers": item["nameservers"],
                    "related_entities": deduped,
                }
            )

        return results
