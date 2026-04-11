"""
Risk Assessment Service

Extracts AI-generated risk assessments from intelligence reports
and combines them with sanctions screening results for final risk determination.
"""

import re
from typing import Optional, Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)

# Matches "- Indicator name: Yes [url]" or "- Indicator name: No"
_INDICATOR_RE = re.compile(
    r'-\s+([^:\n]+?):\s+(Yes|No)',
    re.IGNORECASE
)


class RiskAssessmentService:
    """Service for extracting and combining risk signals"""

    def extract_ai_risk_assessment(self, report_text: str) -> Dict[str, Any]:
        """
        Parse Yes/No risk indicators from AI intelligence report.

        Args:
            report_text: Full intelligence report text

        Returns:
            {
                'yes_count': int,
                'total_count': int,
                'indicators': [{'indicator': str, 'flagged': bool}, ...]
            }
        """
        if not report_text:
            logger.warning("Empty report text provided")
            return {'yes_count': 0, 'total_count': 0, 'indicators': []}

        indicators: List[Dict[str, Any]] = []
        for match in _INDICATOR_RE.finditer(report_text):
            indicator = match.group(1).strip()
            flagged = match.group(2).lower() == 'yes'
            indicators.append({'indicator': indicator, 'flagged': flagged})

        yes_count = sum(1 for i in indicators if i['flagged'])
        total_count = len(indicators)

        logger.info(f"Extracted Yes/No indicators: {yes_count}/{total_count} flagged")

        return {
            'yes_count': yes_count,
            'total_count': total_count,
            'indicators': indicators,
        }

    def _calculate_sanctions_risk(self, sanctions_hits: List[Dict]) -> str:
        """
        Calculate risk level based only on sanctions hits.

        Args:
            sanctions_hits: List of sanctions matches

        Returns:
            Risk level: SAFE, LOW, MID, HIGH, VERY_HIGH
        """
        if not sanctions_hits:
            return "SAFE"

        # Count high-quality matches
        high_matches = sum(
            1 for hit in sanctions_hits
            if hit.get('match_quality') in ['EXACT', 'HIGH']
        )

        medium_matches = sum(
            1 for hit in sanctions_hits
            if hit.get('match_quality') == 'MEDIUM'
        )

        # Get best combined score
        best_score = max(
            (hit.get('combined_score', 0) for hit in sanctions_hits),
            default=0
        )

        # Risk level logic
        if high_matches >= 3 or best_score >= 95:
            return "VERY_HIGH"
        elif high_matches >= 1 or best_score >= 85:
            return "HIGH"
        elif medium_matches >= 3 or best_score >= 75:
            return "MID"
        elif len(sanctions_hits) >= 1:
            return "LOW"
        else:
            return "SAFE"

    def _derive_ai_level(self, ai_assessment: Dict) -> Optional[str]:
        """Derive a HIGH/MEDIUM/LOW level from Yes/No indicator counts for combination logic."""
        yes_count = ai_assessment.get('yes_count', 0)
        total_count = ai_assessment.get('total_count', 0)
        indicators = ai_assessment.get('indicators', [])

        if total_count == 0:
            return None

        # Active sanctions listing flagged → treat as HIGH regardless of count
        for item in indicators:
            if 'sanctions' in item['indicator'].lower() and item['flagged']:
                return 'HIGH'

        if yes_count == 0:
            return 'LOW'
        elif yes_count <= 3:
            return 'MEDIUM'
        else:
            return 'HIGH'

    def calculate_combined_risk_level(
        self,
        sanctions_hits: List[Dict],
        ai_assessment: Dict,
        media_intelligence: Optional[Dict] = None,
        aleph_hits: Optional[List[Dict]] = None,   # OCCRP Aleph leak/PEP hits
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate final risk level combining all signals.

        Args:
            sanctions_hits: List of sanctions matches
            ai_assessment: Dict with 'yes_count', 'total_count', 'indicators' from AI report
            media_intelligence: Media source counts (optional)

        Returns:
            Tuple of (risk_level, explanation_dict)
            - risk_level: 'SAFE' | 'LOW' | 'MID' | 'HIGH' | 'VERY_HIGH'
            - explanation_dict: Detailed reasoning for transparency
        """
        # Calculate sanctions signal
        sanctions_risk = self._calculate_sanctions_risk(sanctions_hits)

        yes_count = ai_assessment.get('yes_count', 0)
        total_count = ai_assessment.get('total_count', 0)
        ai_level = self._derive_ai_level(ai_assessment)  # used for combination logic only

        # Build explanation components
        sanctions_signal = f"{len(sanctions_hits)} sanctions hit(s) → {sanctions_risk}"

        if total_count > 0:
            intelligence_signal = f"{yes_count} / {total_count} risk indicators flagged"
        else:
            intelligence_signal = "Risk indicator data not available"

        # Combination logic (unchanged from before, uses derived ai_level internally)
        final_risk = sanctions_risk
        reasoning_parts = []

        # Rule 1: Strong sanctions signal → Keep it
        if sanctions_risk in ["VERY_HIGH", "HIGH"]:
            final_risk = sanctions_risk
            reasoning_parts.append(f"Strong sanctions match ({sanctions_risk})")

            if ai_level == "HIGH":
                reasoning_parts.append("Intelligence indicators confirm elevated concern")
            elif ai_level == "MEDIUM":
                reasoning_parts.append("Intelligence indicators show moderate additional concerns")
            elif ai_level == "LOW":
                reasoning_parts.append("Intelligence indicators suggest lower concern, but sanctions take precedence")

        # Rule 2: No sanctions + HIGH AI → Elevate to MID
        elif sanctions_risk == "SAFE" and ai_level == "HIGH":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to multiple flagged intelligence indicators despite no sanctions")

        # Rule 3: No sanctions + MEDIUM AI → Elevate to MID
        elif sanctions_risk == "SAFE" and ai_level == "MEDIUM":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to flagged intelligence indicators")

        # Rule 4: Weak sanctions + HIGH AI → Elevate
        elif sanctions_risk == "LOW" and ai_level == "HIGH":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to weak sanctions match + multiple flagged indicators")

        elif sanctions_risk == "MID" and ai_level == "HIGH":
            final_risk = "HIGH"
            reasoning_parts.append("Elevated to HIGH due to moderate sanctions + multiple flagged indicators")

        # Rule 5: No sanctions + LOW/None AI → Stay SAFE
        elif sanctions_risk == "SAFE" and (ai_level == "LOW" or ai_level is None):
            final_risk = "SAFE"
            reasoning_parts.append("No significant sanctions or intelligence concerns identified")

        # Default: Keep sanctions risk
        else:
            reasoning_parts.append(f"Risk level determined primarily by sanctions screening ({sanctions_risk})")
            if ai_level:
                reasoning_parts.append(f"Intelligence indicators provide additional context")

        # --- Aleph signal (offshore leaks + PEP) ---
        # Runs as a post-processing elevation step so it never lowers an
        # existing HIGH/VERY_HIGH determined by sanctions or AI indicators.
        aleph_hits = aleph_hits or []
        aleph_leak_hits = [h for h in aleph_hits if h.get("is_leak_db_hit")]
        aleph_pep_hits  = [h for h in aleph_hits if h.get("is_pep")]

        aleph_signal_parts: List[str] = []

        if aleph_leak_hits and aleph_pep_hits:
            # Rule A: PEP AND leak database hit — most serious combination
            if final_risk in ("SAFE", "LOW"):
                final_risk = "HIGH"
                reasoning_parts.append(
                    f"Elevated to HIGH: entity appears in {len(aleph_leak_hits)} "
                    f"offshore leak dataset(s) AND is flagged as a PEP in OCCRP Aleph"
                )
            elif final_risk == "MID":
                final_risk = "HIGH"
                reasoning_parts.append(
                    f"Elevated to HIGH from MID: PEP status + "
                    f"{len(aleph_leak_hits)} leak dataset hit(s) in OCCRP Aleph"
                )
            # HIGH or VERY_HIGH already — no downgrade; just log
            aleph_signal_parts.append(
                f"PEP+leak: {len(aleph_pep_hits)} PEP flag(s), "
                f"{len(aleph_leak_hits)} leak DB hit(s)"
            )

        elif aleph_pep_hits:
            # Rule B: PEP only — elevate SAFE/LOW to MID; leave MID+ alone
            if final_risk in ("SAFE", "LOW"):
                final_risk = "MID"
                reasoning_parts.append(
                    f"Elevated to MID: entity is flagged as a PEP "
                    f"in OCCRP Aleph ({len(aleph_pep_hits)} result(s))"
                )
            aleph_signal_parts.append(f"PEP flag(s): {len(aleph_pep_hits)}")

        elif aleph_leak_hits:
            # Rule C: Leak DB only — elevate SAFE/LOW to MID; leave MID+ alone
            if final_risk in ("SAFE", "LOW"):
                final_risk = "MID"
                reasoning_parts.append(
                    f"Elevated to MID: entity found in "
                    f"{len(aleph_leak_hits)} offshore leak dataset(s) via OCCRP Aleph"
                )
            aleph_signal_parts.append(
                f"Leak DB hit(s): {len(aleph_leak_hits)} "
                f"({', '.join(set(h.get('dataset_label') or h.get('dataset_id', '?') for h in aleph_leak_hits))})"
            )

        aleph_signal = "; ".join(aleph_signal_parts) if aleph_signal_parts else "No Aleph hits"

        # Build full explanation
        explanation = {
            'sanctions_signal': sanctions_signal,
            'intelligence_signal': intelligence_signal,
            'intelligence_score': None,       # deprecated, kept for DB compatibility
            'intelligence_breakdown': None,   # deprecated, kept for DB compatibility
            'final_reasoning': " | ".join(reasoning_parts),
            'yes_count': yes_count,
            'total_count': total_count,
            'indicator_results': ai_assessment.get('indicators', []),
            'aleph_signal': aleph_signal,     # OCCRP Aleph leak/PEP summary
        }

        logger.info(
            f"Combined risk calculation: "
            f"Sanctions={sanctions_risk}, Indicators={yes_count}/{total_count}, "
            f"Aleph={aleph_signal}, Final={final_risk}"
        )

        return final_risk, explanation


# Global service instance
_risk_service: Optional[RiskAssessmentService] = None


def get_risk_assessment_service() -> RiskAssessmentService:
    """
    Get or create risk assessment service instance

    Returns:
        RiskAssessmentService instance
    """
    global _risk_service

    if _risk_service is None:
        _risk_service = RiskAssessmentService()

    return _risk_service
