"""Mask secrets in any string before logging or displaying."""

import os
import re

_SECRET_KEYS = ["TELEGRAM_BOT_TOKEN", "NEWSAPI_KEY", "EURI_API_KEY",
                "TAVILY_API_KEY", "OPENROUTER_API_KEY"]


def mask(text: str) -> str:
    """Replace known secret values with masked versions."""
    for key in _SECRET_KEYS:
        value = os.getenv(key, "")
        if value and len(value) > 4:
            masked = value[:4] + "*" * (len(value) - 4)
            text = text.replace(value, masked)
    return text
