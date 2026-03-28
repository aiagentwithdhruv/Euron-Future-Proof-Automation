import os
from dotenv import load_dotenv

load_dotenv()

# Scraper API Keys
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
OUTSCRAPER_API_KEY = os.getenv("OUTSCRAPER_API_KEY", "")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/service_account.json")
GOOGLE_SHEETS_SPREADSHEET_NAME = os.getenv("GOOGLE_SHEETS_SPREADSHEET_NAME", "Google Maps Leads")

# Defaults
DEFAULT_LEAD_LIMIT = int(os.getenv("DEFAULT_LEAD_LIMIT", "50"))
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

# Output — leads/ folder is at project root, not inside src/
LEADS_DIR = os.path.join(os.path.dirname(__file__), "..", "leads")
os.makedirs(LEADS_DIR, exist_ok=True)


def get_active_scraper():
    """Return which scraper to use based on available API keys."""
    if APIFY_API_TOKEN:
        return "apify"
    if OUTSCRAPER_API_KEY:
        return "outscraper"
    raise ValueError(
        "No scraper API key found. Set APIFY_API_TOKEN or OUTSCRAPER_API_KEY in your .env file."
    )
