"""Configuration — loads environment variables and defines constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
ENV_PATH = ROOT_DIR / ".env"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# Load environment
load_dotenv(ENV_PATH)

# API
BLOTATO_API_KEY = os.getenv("BLOTATO_API_KEY", "")
BLOTATO_BASE_URL = "https://backend.blotato.com/v2"

# LLM (via OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-sonnet-4")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Supported platforms
PLATFORMS = ["linkedin", "x", "instagram"]

# Polling
EXTRACTION_TIMEOUT = 120  # seconds
VISUAL_TIMEOUT = 180
PUBLISH_TIMEOUT = 120
POLL_INTERVAL_EXTRACT = 3
POLL_INTERVAL_VISUAL = 5
POLL_INTERVAL_PUBLISH = 3
