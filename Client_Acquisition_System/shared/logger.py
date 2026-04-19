"""Structured JSON logger with API-key masking."""

import json
import logging
import re
import sys
from datetime import datetime, timezone

_SECRET_PATTERNS = [
    re.compile(r"(?i)(sk-[a-z0-9]{20,})"),
    re.compile(r"(?i)(bearer\s+[a-z0-9._\-]{20,})"),
    re.compile(r"(?i)(re_[a-z0-9]{20,})"),
    re.compile(r"(?i)(hunter_[a-z0-9]{20,})"),
    re.compile(r"(?i)(apify_api_[a-z0-9]{20,})"),
]


def _mask(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": _mask(record.getMessage()),
        }
        for attr in ("prospect_id", "stage", "outputs", "cost_usd", "duration_ms"):
            if hasattr(record, attr):
                value = getattr(record, attr)
                entry[attr] = _mask(str(value)) if isinstance(value, str) else value
        if record.exc_info and record.exc_info[0]:
            entry["error"] = {
                "type": record.exc_info[0].__name__,
                "msg": _mask(str(record.exc_info[1])),
            }
        return json.dumps(entry)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
