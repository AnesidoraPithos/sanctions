"""
Fuzzy Matching Utilities for Sanctions Screening

This module provides local fuzzy matching algorithms to supplement the USA Trade API's
scoring system. It combines 5 different algorithms to create a composite similarity score.

See SCORING_SYSTEM.md for detailed documentation on how these algorithms work.
"""

import re

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler
from metaphone import doublemetaphone

# Fuzzy matching configuration (algorithm weights, thresholds, and scoring weights)
_FUZZY_CONFIG = {
    'weights': {
        'token_set': 0.30,
        'jaro_winkler': 0.25,
        'levenshtein': 0.20,
        'token_sort': 0.15,
        'phonetic': 0.10,
    },
    'thresholds': {'exact': 95, 'high': 82, 'medium': 70, 'low': 0},
    'api_weight': 0.0,
    'local_weight': 1.0,
}


def calculate_similarity_scores(query_name, result_name):
    """
    Calculate individual similarity scores using 5 different algorithms.

    Args:
        query_name (str): The search query (user input)
        result_name (str): The name from sanctions database

    Returns:
        dict: Individual scores for each algorithm (0-100 scale)
        {
            'token_set': float,
            'jaro_winkler': float,
            'levenshtein': float,
            'token_sort': float,
            'phonetic': float
        }
    """
    if not query_name or not result_name:
        return {
            'token_set': 0,
            'jaro_winkler': 0,
            'levenshtein': 0,
            'token_sort': 0,
            'phonetic': 0
        }

    # Normalize strings (lowercase, strip whitespace)
    query = query_name.strip().lower()
    result = result_name.strip().lower()

    # Algorithm 1: Token Set Ratio
    # Ignores extra tokens, focuses on shared unique tokens
    # Best for: Company names with legal suffixes
    token_set_score = fuzz.token_set_ratio(query, result)

    # Algorithm 2: Jaro-Winkler Distance
    # Optimized for names, gives bonus for matching prefixes
    # Best for: Person names, typos, company names
    jaro_winkler_score = JaroWinkler.similarity(query, result) * 100

    # Algorithm 3: Levenshtein Distance (normalized)
    # Classic edit distance: insertions, deletions, substitutions
    # Best for: Character-level similarity baseline
    levenshtein_score = fuzz.ratio(query, result)

    # Algorithm 4: Token Sort Ratio
    # Alphabetically sorts tokens before comparing
    # Best for: Word order variations
    token_sort_score = fuzz.token_sort_ratio(query, result)

    # Algorithm 5: Phonetic Matching (Double Metaphone)
    # Compares pronunciation-based phonetic codes
    # Best for: Transliteration issues (e.g., Chinese names)
    try:
        query_phonetic = doublemetaphone(query)
        result_phonetic = doublemetaphone(result)

        # Check if primary or secondary codes match
        # Double Metaphone returns (primary, secondary) tuple
        phonetic_match = (
            query_phonetic[0] == result_phonetic[0] or  # Primary codes match
            query_phonetic[0] == result_phonetic[1] or  # Query primary = result secondary
            query_phonetic[1] == result_phonetic[0] or  # Query secondary = result primary
            (query_phonetic[1] and result_phonetic[1] and
             query_phonetic[1] == result_phonetic[1])   # Secondary codes match
        )
        phonetic_score = 100.0 if phonetic_match else 0.0
    except Exception:
        # Fallback if phonetic encoding fails
        phonetic_score = 0.0

    return {
        'token_set': float(token_set_score),
        'jaro_winkler': float(jaro_winkler_score),
        'levenshtein': float(levenshtein_score),
        'token_sort': float(token_sort_score),
        'phonetic': float(phonetic_score)
    }


def get_composite_score(query_name, result_name, weights=None):
    """
    Calculate weighted composite similarity score from all algorithms.

    Args:
        query_name (str): The search query (user input)
        result_name (str): The name from sanctions database
        weights (dict, optional): Custom algorithm weights. If None, uses default config.

    Returns:
        float: Composite similarity score (0-100)
    """
    if weights is None:
        weights = _FUZZY_CONFIG['weights']

    # Get individual scores
    scores = calculate_similarity_scores(query_name, result_name)

    # Calculate weighted average
    composite_score = (
        (scores['token_set'] * weights['token_set']) +
        (scores['jaro_winkler'] * weights['jaro_winkler']) +
        (scores['levenshtein'] * weights['levenshtein']) +
        (scores['token_sort'] * weights['token_sort']) +
        (scores['phonetic'] * weights['phonetic'])
    )

    # Boost to 100 if query is an acronym of the entity name
    if check_acronym_match(query_name, result_name):
        return 100.0

    return round(composite_score, 2)


_STOP_WORDS = {'of', 'the', 'and', 'for', 'in', 'at', 'by', 'to', 'a', 'an'}


def check_acronym_match(query: str, entity_name: str) -> bool:
    """
    Returns True if query is an acronym formed from the first letters
    of each significant word in entity_name (stop words excluded).
    Requires query length >= 3 to avoid false positives.

    Example: "BAAI" matches "Beijing Academy of Artificial Intelligence"
      words (stop words removed): Beijing, Academy, Artificial, Intelligence
      initials: B-A-A-I = "BAAI"
    """
    query = query.strip().upper()
    if len(query) < 3:
        return False
    # Strip trailing parentheticals e.g. "(BAAI)" before computing initials
    clean_name = re.sub(r'\s*\([^)]*\)\s*$', '', entity_name).strip()
    words = clean_name.split()
    initials = ''.join(
        w[0].upper() for w in words
        if w.lower() not in _STOP_WORDS and len(w) >= 2
    )
    return query == initials


def classify_match_quality(combined_score, thresholds=None):
    """
    Classify match quality based on combined score.

    Args:
        combined_score (float): Combined API + local score (0-100)
        thresholds (dict, optional): Custom thresholds. If None, uses default config.

    Returns:
        str: Match quality classification ('EXACT', 'HIGH', 'MEDIUM', 'LOW')
    """
    if thresholds is None:
        thresholds = _FUZZY_CONFIG['thresholds']

    if combined_score >= thresholds['exact']:
        return 'EXACT'
    elif combined_score >= thresholds['high']:
        return 'HIGH'
    elif combined_score >= thresholds['medium']:
        return 'MEDIUM'
    else:
        return 'LOW'


def combine_scores(api_score, local_score, api_weight=None, local_weight=None):
    """
    Combine API score and local score using weighted average.

    NOTE: With local-only scoring (api_weight=0.0, local_weight=1.0),
    this effectively returns local_score. API score is kept for reference
    but not used in the final calculation.

    Args:
        api_score (float or None): Score from USA Trade API (typically 80, 90, or 100)
                                   None for local database entities
        local_score (float): Local composite score (0-100)
        api_weight (float, optional): Weight for API score. If None, uses default config.
        local_weight (float, optional): Weight for local score. If None, uses default config.

    Returns:
        float: Combined score (0-100)
    """
    if api_weight is None:
        api_weight = _FUZZY_CONFIG['api_weight']  # Default: 0.0
    if local_weight is None:
        local_weight = _FUZZY_CONFIG['local_weight']  # Default: 1.0

    # If API score is None (from local DB), return local score directly
    if api_score is None:
        return round(local_score, 2)

    # Calculate weighted combination
    # With api_weight=0.0 and local_weight=1.0, this returns local_score
    combined = (api_score * api_weight) + (local_score * local_weight)
    return round(combined, 2)


def get_match_info(query_name, result_name, api_score):
    """
    Convenience function to get all matching information at once.

    Args:
        query_name (str): The search query (user input)
        result_name (str): The name from sanctions database
        api_score (float): Score from USA Trade API

    Returns:
        dict: Complete matching information
        {
            'api_score': float,
            'local_score': float,
            'combined_score': float,
            'match_quality': str,
            'similarity_breakdown': dict
        }
    """
    # Get individual algorithm scores
    similarity_breakdown = calculate_similarity_scores(query_name, result_name)

    # Calculate local composite score
    local_score = get_composite_score(query_name, result_name)

    # Combine API and local scores
    combined_score = combine_scores(api_score, local_score)

    # Classify match quality
    match_quality = classify_match_quality(combined_score)

    return {
        'api_score': api_score,
        'local_score': local_score,
        'combined_score': combined_score,
        'match_quality': match_quality,
        'similarity_breakdown': similarity_breakdown
    }


# Example usage and testing
if __name__ == "__main__":
    # Test cases from SCORING_SYSTEM.md

    print("=" * 80)
    print("FUZZY MATCHING TEST CASES")
    print("=" * 80)

    test_cases = [
        ("Huawei", "Huawei", 100, "Perfect exact match"),
        ("Huawei Technologies", "Huawei Technologies Co Ltd", 100, "Exact match with legal suffix"),
        ("Huawei", "Huawai", 90, "Close fuzzy match (typo)"),
        ("Huawei Tech", "Huawei Technologies Limited", 90, "Moderate fuzzy match"),
        ("Huawei", "Hawaii Trading Company", 80, "False positive caught"),
        ("Apple", "Appleton Industries", 80, "Strong false positive"),
    ]

    for query, result, api_score, description in test_cases:
        print(f"\n{description}")
        print(f"Query: '{query}' → Result: '{result}'")
        print(f"API Score: {api_score}")

        match_info = get_match_info(query, result, api_score)

        print(f"Local Score: {match_info['local_score']}")
        print(f"Combined Score: {match_info['combined_score']}")
        print(f"Match Quality: {match_info['match_quality']}")
        print(f"Breakdown: {match_info['similarity_breakdown']}")
        print("-" * 80)
