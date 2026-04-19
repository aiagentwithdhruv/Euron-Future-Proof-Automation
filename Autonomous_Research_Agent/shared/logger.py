"""Structured logging with automatic secret masking."""

import json
import os
from datetime import datetime, timezone


_SECRET_KEYS = [
    "TELEGRAM_BOT_TOKEN", "NEWSAPI_KEY", "EURI_API_KEY",
    "TAVILY_API_KEY", "OPENROUTER_API_KEY", "APIFY_API_TOKEN",
    "SLACK_WEBHOOK_URL", "RESEND_API_KEY",
]


def _mask_secrets(text: str) -> str:
    for key in _SECRET_KEYS:
        value = os.getenv(key, "")
        if value and len(value) > 4:
            masked = value[:4] + "*" * (len(value) - 4)
            text = text.replace(value, masked)
    return text


def log(level: str, message: str, **extra):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "message": _mask_secrets(message),
    }
    if extra:
        entry["data"] = {k: _mask_secrets(str(v)) for k, v in extra.items()}
    print(json.dumps(entry))


def info(message: str, **extra):
    log("INFO", message, **extra)


def error(message: str, **extra):
    log("ERROR", message, **extra)


def warn(message: str, **extra):
    log("WARN", message, **extra)
