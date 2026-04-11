"""
Configuration Management

Loads environment variables and provides application settings.
Uses pydantic-settings for validation and type safety.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Legacy constants for compatibility with core modules
DB_FILE = os.path.join(os.path.dirname(__file__), '..', 'sanctions.db')

# Fuzzy Matching Configuration (required by core/matching_utils.py)
FUZZY_MATCHING_CONFIG = {
    # Algorithm weights (balanced for mixed entity types)
    "weights": {
        "token_set": 0.30,      # Company name variations
        "jaro_winkler": 0.25,   # Name matching
        "levenshtein": 0.20,    # Edit distance
        "token_sort": 0.15,     # Word order variations
        "phonetic": 0.10        # Pronunciation similarity
    },
    # Match quality thresholds
    "thresholds": {
        "exact": 95,      # Very high confidence
        "high": 82,       # Strong fuzzy match
        "medium": 70,     # Moderate fuzzy match
        "low": 0          # Weak match
    },
    # Score combination weights
    "api_weight": 0.0,      # 0% API score
    "local_weight": 1.0     # 100% local score
}

# Legacy function for compatibility
def get_gemini_key():
    """Get Gemini API key from environment"""
    return os.getenv("GEMINI_API_KEY")


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # API Keys
    USA_TRADE_GOV_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENCORPORATES_API_KEY: str = ""  # Optional - Phase 2 (network tier)
    COMPANIES_HOUSE_API_KEY: str = ""  # Optional - UK corporate data via Companies House

    # Database
    DATABASE_PATH: str = "../sanctions.db"  # Relative to backend/

    # LLM Configuration
    LLM_PROVIDER: str = "ollama"  # ollama or openai
    LLM_MODEL: str = "llama3"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Research Configuration
    FUZZY_THRESHOLD_DEFAULT: int = 80
    MAX_SEARCH_RESULTS: int = 100
    REQUEST_TIMEOUT: int = 60  # seconds - increased for parallel searches (was 30)
    MAX_LEVEL_2_SEARCHES: int = 20  # Maximum subsidiaries to search for level 2
    MAX_LEVEL_3_SEARCHES: int = 10  # Maximum subsidiaries to search for level 3

    # Parallelization Configuration
    MAX_PARALLEL_SUBSIDIARY_SEARCHES: int = 10  # Max concurrent subsidiary API searches
    MAX_PARALLEL_SANCTIONS_SCREENING: int = 20  # Max concurrent sanctions screenings

    # Feature Flags
    ENABLE_NETWORK_TIER: bool = True   # Phase 2 - IMPLEMENTED ✅
    ENABLE_DEEP_TIER: bool = False     # Phase 3

    # Phase 4 settings
    ENABLE_PHASE4_FEATURES: bool = True
    LITTLESIS_API_KEY: str = ""
    MAX_DIRECTOR_PIVOT_COUNT: int = 10
    MAX_WHOIS_DOMAINS: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
settings = Settings()

# Validate critical settings on startup
def validate_settings():
    """Validate that critical settings are configured"""
    warnings = []

    if not settings.USA_TRADE_GOV_API_KEY:
        warnings.append("USA_TRADE_GOV_API_KEY not set - sanctions API will fail")

    if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY not set but LLM_PROVIDER is 'openai'")

    if not os.path.exists(settings.DATABASE_PATH):
        warnings.append(f"Database not found at {settings.DATABASE_PATH}")

    return warnings


if __name__ == "__main__":
    # Test configuration
    print("Configuration loaded:")
    print(f"  Host: {settings.HOST}:{settings.PORT}")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  LLM Provider: {settings.LLM_PROVIDER}")
    print(f"  Database: {settings.DATABASE_PATH}")

    warnings = validate_settings()
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
