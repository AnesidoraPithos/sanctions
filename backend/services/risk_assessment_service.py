"""
Risk Assessment Service

Extracts AI-generated risk assessments from intelligence reports
and combines them with sanctions screening results for final risk determination.
"""

import re
from typing import Optional, Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class RiskAssessmentService:
    """Service for extracting and combining risk signals"""

    def extract_ai_risk_assessment(self, report_text: str) -> Dict[str, Any]:
        """
        Extract risk level and scoring breakdown from AI intelligence report.

        Args:
            report_text: Full intelligence report text

        Returns:
            {
                'level': 'HIGH' | 'MEDIUM' | 'LOW' | None,
                'score': int (0-100) | None,
                'breakdown': str | None
            }
        """
        if not report_text:
            logger.warning("Empty report text provided")
            return {'level': None, 'score': None, 'breakdown': None}

        # Scan first 3000 chars of report (Executive Summary section)
        search_text = report_text[:3000]

        # Pattern 1: Extract "Risk Level: High (Score: 78/100)"
        risk_pattern = r'Risk Level:\s*(High|Medium|Low)\s*\(Score:\s*(\d+)/100\)'
        risk_match = re.search(risk_pattern, search_text, re.IGNORECASE)

        # Pattern 2: Extract "Scoring Breakdown: ..." on next line
        breakdown_pattern = r'Scoring Breakdown:\s*(.+?)(?:\n\n|\n[A-Z]|$)'
        breakdown_match = re.search(breakdown_pattern, search_text, re.IGNORECASE | re.DOTALL)

        if risk_match:
            level = risk_match.group(1).upper()
            score = int(risk_match.group(2))
            breakdown = breakdown_match.group(1).strip() if breakdown_match else None

            logger.info(f"Extracted AI risk assessment: {level} ({score}/100)")

            return {
                'level': level,
                'score': score,
                'breakdown': breakdown
            }

        # Fallback: Try old "Threat Level: High" format (without score)
        old_pattern = r'(?:Threat|Risk) Level:\s*(High|Medium|Low)'
        old_match = re.search(old_pattern, search_text, re.IGNORECASE)

        if old_match:
            level = old_match.group(1).upper()
            logger.info(f"Extracted AI risk assessment (legacy format): {level}")

            # Estimate score based on level
            score_map = {'HIGH': 75, 'MEDIUM': 50, 'LOW': 20}
            estimated_score = score_map.get(level, 0)

            return {
                'level': level,
                'score': estimated_score,
                'breakdown': "Legacy format - no breakdown available"
            }

        logger.warning("Could not extract AI risk assessment from report")
        return {'level': None, 'score': None, 'breakdown': None}

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

    def calculate_combined_risk_level(
        self,
        sanctions_hits: List[Dict],
        ai_assessment: Dict,
        media_intelligence: Optional[Dict] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Calculate final risk level combining all signals.

        Args:
            sanctions_hits: List of sanctions matches
            ai_assessment: Dict with 'level', 'score', 'breakdown' from AI report
            media_intelligence: Media source counts (optional)

        Returns:
            Tuple of (risk_level, explanation_dict)
            - risk_level: 'SAFE' | 'LOW' | 'MID' | 'HIGH' | 'VERY_HIGH'
            - explanation_dict: Detailed reasoning for transparency
        """
        # Calculate sanctions signal
        sanctions_risk = self._calculate_sanctions_risk(sanctions_hits)

        ai_level = ai_assessment.get('level')  # HIGH/MEDIUM/LOW or None
        ai_score = ai_assessment.get('score')  # 0-100 or None

        # Build explanation components
        sanctions_signal = f"{len(sanctions_hits)} sanctions hit(s) → {sanctions_risk}"

        if ai_level and ai_score is not None:
            intelligence_signal = f"AI assessment: {ai_level} ({ai_score}/100)"
        elif ai_level:
            intelligence_signal = f"AI assessment: {ai_level}"
        else:
            intelligence_signal = "AI assessment: Not available"

        # Combination logic
        final_risk = sanctions_risk
        reasoning_parts = []

        # Rule 1: Strong sanctions signal → Keep it
        if sanctions_risk in ["VERY_HIGH", "HIGH"]:
            final_risk = sanctions_risk
            reasoning_parts.append(f"Strong sanctions match ({sanctions_risk})")

            if ai_level == "HIGH":
                reasoning_parts.append("AI assessment confirms high risk")
            elif ai_level == "MEDIUM":
                reasoning_parts.append("AI assessment shows moderate additional concerns")
            elif ai_level == "LOW":
                reasoning_parts.append("AI assessment suggests lower risk, but sanctions take precedence")

        # Rule 2: No sanctions + HIGH AI → Elevate to MID
        elif sanctions_risk == "SAFE" and ai_level == "HIGH":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to high AI intelligence score despite no sanctions")

        # Rule 3: No sanctions + MEDIUM AI → Elevate to MID
        elif sanctions_risk == "SAFE" and ai_level == "MEDIUM":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to moderate AI intelligence concerns")

        # Rule 4: Weak sanctions + HIGH AI → Elevate
        elif sanctions_risk == "LOW" and ai_level == "HIGH":
            final_risk = "MID"
            reasoning_parts.append("Elevated to MID due to weak sanctions match + high AI concerns")

        elif sanctions_risk == "MID" and ai_level == "HIGH":
            final_risk = "HIGH"
            reasoning_parts.append("Elevated to HIGH due to moderate sanctions + high AI concerns")

        # Rule 5: No sanctions + LOW/None AI → Stay SAFE or LOW
        elif sanctions_risk == "SAFE" and (ai_level == "LOW" or ai_level is None):
            final_risk = "SAFE"
            reasoning_parts.append("No significant sanctions or intelligence concerns identified")

        # Default: Keep sanctions risk
        else:
            reasoning_parts.append(f"Risk level determined primarily by sanctions screening ({sanctions_risk})")
            if ai_level:
                reasoning_parts.append(f"AI assessment ({ai_level}) provides context")

        # Build full explanation
        explanation = {
            'sanctions_signal': sanctions_signal,
            'intelligence_signal': intelligence_signal,
            'intelligence_score': ai_score,
            'intelligence_breakdown': ai_assessment.get('breakdown'),
            'final_reasoning': " | ".join(reasoning_parts)
        }

        logger.info(
            f"Combined risk calculation: "
            f"Sanctions={sanctions_risk}, AI={ai_level}, Final={final_risk}"
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
