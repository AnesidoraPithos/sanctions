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

    # Match quality thresholds (balanced precision)
    # These thresholds map combined scores to match quality classifications
    "thresholds": {
        "exact": 92,      # High confidence exact match (API 100 + good local)
        "high": 80,       # Strong fuzzy match (API 90 or API 80 + excellent local)
        "medium": 65,     # Moderate fuzzy match (API 80 + decent local)
        "low": 0          # Weak match (API 80 + poor local, likely false positive)
    },

    # Score combination weights (API-favoring for authority)
    # combined_score = (api_score × api_weight) + (local_score × local_weight)
    "api_weight": 0.60,     # 60% API score (authoritative 3-tier signal: 100/90/80)
    "local_weight": 0.40    # 40% local score (granular refinement within API tiers)
}