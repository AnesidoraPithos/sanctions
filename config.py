import os
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

# Constants
DB_FILE = "sanctions.db"

def get_gemini_key():
    return os.getenv("GEMINI_API_KEY")