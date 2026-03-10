#!/usr/bin/env python3
"""
Test script for AI threat level extraction
Tests various phrasings to ensure robust extraction
"""

import re

def extract_ai_threat_level(report_text):
    """Extract threat level from AI intelligence report (Executive Summary)"""
    if not report_text:
        return None

    # Search first 3000 chars (Executive Summary section - increased to capture full summary)
    summary = report_text[:3000].lower()

    # Look for threat/risk level patterns (expanded patterns for better coverage)
    patterns = [
        # Original patterns
        r'threat level[:\s]+(high|medium|low)',
        r'risk level[:\s]+(high|medium|low)',
        r'overall risk[:\s]+(high|medium|low)',
        r'assessed as[:\s]+(high|medium|low)\s+(risk|threat)',
        r'represents a[:\s]+(high|medium|low)\s+risk',
        r'poses a[:\s]+(high|medium|low)\s+risk',
        # New patterns for common variations
        r'risk[:\s]+(high|medium|low)',  # "Risk: High"
        r'threat[:\s]+(high|medium|low)',  # "Threat: High"
        r'(high|medium|low)\s+risk',  # "High risk assessment"
        r'(high|medium|low)\s+threat',  # "High threat level"
        r'overall[:\s]+(high|medium|low)',  # "Overall: High"
        r'assessment[:\s]+(high|medium|low)',  # "Assessment: High"
        r'classified as[:\s]+(high|medium|low)',  # "Classified as High"
        r'rated[:\s]+(high|medium|low)',  # "Rated High"
        r'(high|medium|low)\s+(level|rating|score)',  # "High level"
        r'presents[:\s]+(high|medium|low)\s+risk',  # "Presents high risk"
        r'indicates[:\s]+(high|medium|low)\s+risk',  # "Indicates high risk"
        r'severity[:\s]+(high|medium|low)',  # "Severity: High"
        r'(?:risk|threat)\s+level\s+is\s+(high|medium|low)',  # "Risk Level is High" (non-capturing group for risk/threat)
    ]

    for pattern in patterns:
        match = re.search(pattern, summary)
        if match:
            level = match.group(1).upper()
            return 'HIGH' if level == 'HIGH' else 'MEDIUM' if level == 'MEDIUM' else 'LOW'

    # FALLBACK: If regex fails, use simple keyword search
    if 'high risk' in summary or 'high threat' in summary:
        return 'HIGH'
    elif 'medium risk' in summary or 'medium threat' in summary or 'moderate risk' in summary:
        return 'MEDIUM'
    elif 'low risk' in summary or 'low threat' in summary or 'minimal risk' in summary:
        return 'LOW'

    return None


def test_threat_extraction():
    """Test various threat level phrasings"""
    test_cases = [
        # Standard formats (should match with new prompt format)
        ("Executive Summary: Threat Level: High", "HIGH"),
        ("Executive Summary: Risk Level: Medium", "MEDIUM"),
        ("Executive Summary: Threat Level: Low", "LOW"),

        # Common variations
        ("Overall risk assessment shows a High risk", "HIGH"),
        ("The entity represents a medium risk", "MEDIUM"),
        ("Risk: High due to regulatory violations", "HIGH"),
        ("Assessment: Low risk profile", "LOW"),
        ("This presents high risk to operations", "HIGH"),
        ("Overall: Medium threat level", "MEDIUM"),
        ("Classified as High risk entity", "HIGH"),
        ("Severity: High with multiple red flags", "HIGH"),

        # Fallback keyword detection
        ("The analysis shows high risk factors present", "HIGH"),
        ("There are medium threat indicators", "MEDIUM"),
        ("This represents low risk overall", "LOW"),
        ("Moderate risk assessment indicates caution", "MEDIUM"),

        # Edge cases
        ("Threat: Low", "LOW"),
        ("Risk Level is High", "HIGH"),
        ("Rated Medium for compliance", "MEDIUM"),
        ("Indicates high risk of sanctions", "HIGH"),

        # Should NOT match (testing false positives)
        ("No clear risk indicators found", None),
        ("Entity operates normally", None),
    ]

    print("=" * 80)
    print("AI THREAT EXTRACTION TEST SUITE")
    print("=" * 80)

    passed = 0
    failed = 0

    for i, (report_text, expected) in enumerate(test_cases, 1):
        result = extract_ai_threat_level(report_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"\nTest {i}: {status}")
        print(f"  Input: '{report_text[:60]}...'")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = test_threat_extraction()
    exit(0 if success else 1)
