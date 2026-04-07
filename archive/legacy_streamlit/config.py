import os
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

# Constants
DB_FILE = "sanctions.db"

def get_gemini_key():
    return os.getenv("GEMINI_API_KEY")

# Fuzzy Matching Configuration
FUZZY_MATCHING_CONFIG = {
    # Algorithm weights (balanced for mixed entity types)
    # These weights determine how much each algorithm contributes to the local score
    "weights": {
        "token_set": 0.30,      # Company name variations (legal suffixes, word order)
        "jaro_winkler": 0.25,   # Name matching (typos, prefix emphasis)
        "levenshtein": 0.20,    # Edit distance (character-level similarity)
        "token_sort": 0.15,     # Word order variations (sorted token comparison)
        "phonetic": 0.10        # Pronunciation similarity (transliteration help)
    },

    # Match quality thresholds (recalibrated for local-only scoring)
    # With local-only scoring, these thresholds are based purely on fuzzy match quality
    # Increased from previous values to maintain high precision
    "thresholds": {
        "exact": 95,      # Very high confidence (increased from 92)
        "high": 82,       # Strong fuzzy match (lowered from 85 for legal suffix handling)
        "medium": 70,     # Moderate fuzzy match (increased from 65)
        "low": 0          # Weak match (below 70, likely false positive)
    },

    # Score combination weights (LOCAL-ONLY SCORING)
    # combined_score = (api_score × api_weight) + (local_score × local_weight)
    # Changed to 100% local scoring for uniform scoring across all sources
    "api_weight": 0.0,      # 0% API score (kept for reference only)
    "local_weight": 1.0     # 100% local score (full control over match quality)
}