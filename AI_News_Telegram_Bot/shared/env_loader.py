"""Load and validate environment variables from .env file."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def load_env():
    """Load .env from project root. Skips gracefully if running in CI (GitHub Actions)."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    elif not os.getenv("CI") and not os.getenv("GITHUB_ACTIONS"):
        print("ERROR: .env file not found. Copy .env.example to .env and add your API keys.")
        sys.exit(1)


def get_required(key: str) -> str:
    """Get a required env var. Exit if missing."""
    value = os.getenv(key, "").strip()
    if not value:
        print(f"ERROR: {key} is required but not set in .env")
        sys.exit(1)
    return value


def get_optional(key: str, default: str = "") -> str:
    """Get an optional env var with a default."""
    return os.getenv(key, default).strip()
