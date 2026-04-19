"""
JSON structured logger with secret masking.
Used by every tool. No RAG logic here.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

_SECRET_VAR_NAMES = (
    "EURI_API_KEY",
    "GOOGLE_API_KEY",
    "SUPABASE_SERVICE_KEY",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_VERIFY_TOKEN",
    "API_KEY",
)

_PATTERN = re.compile(
    r"(?:sk-|key_|token_|api[_-]?key[=:]\s*)[A-Za-z0-9_\-]{12,}"
)


def _current_secret_values() -> list[str]:
    out: list[str] = []
    for v in _SECRET_VAR_NAMES:
        val = os.environ.get(v, "")
        if val and len(val) > 6:
            out.append(val)
    return out


def mask(text: str) -> str:
    if not isinstance(text, str):
        return text
    masked = text
    for s in _current_secret_values():
        if s in masked:
            masked = masked.replace(s, "***REDACTED***")
    return _PATTERN.sub("***REDACTED***", masked)


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": mask(record.getMessage()),
        }
        for attr in ("inputs", "outputs", "duration_ms", "count", "source_id"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        if record.exc_info and record.exc_info[0]:
            entry["error"] = {
                "type": record.exc_info[0].__name__,
                "message": mask(str(record.exc_info[1])),
            }
        return json.dumps(entry, default=str)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(_JsonFormatter())
        lg.addHandler(h)
        lg.propagate = False
    lg.setLevel(getattr(logging, level.upper(), logging.INFO))
    return lg
