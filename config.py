import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables once
load_dotenv()

# Constants
DB_FILE = "sanctions.db"

# Setup Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def get_gemini_model():
    return model