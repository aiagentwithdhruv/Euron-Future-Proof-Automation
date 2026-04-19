"""Structured JSON logger with secret masking."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any


_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|authorization|bearer|token|secret|password)\s*[:=]\s*[^\s\"]+"),
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)x-[a-z-]*key:\s*[^\s\"]+"),
]


def mask_secrets(text: str) -> str:
    if not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(lambda m: m.group(0).split(":")[0].split("=")[0] + "=***", out)
    return out


def mask_dict(d: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    sensitive = ("key", "token", "secret", "password", "authorization", "auth")
    for k, v in d.items():
        if any(s in k.lower() for s in sensitive):
            masked[k] = "***"
        elif isinstance(v, dict):
            masked[k] = mask_dict(v)
        elif isinstance(v, str):
            masked[k] = mask_secrets(v)
        else:
            masked[k] = v
    return masked


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": mask_secrets(record.getMessage()),
        }
        for attr in ("call_id", "tool", "outcome", "duration_ms", "path", "status"):
            if hasattr(record, attr):
                entry[attr] = getattr(record, attr)
        if record.exc_info and record.exc_info[0]:
            entry["error"] = {
                "type": record.exc_info[0].__name__,
                "message": mask_secrets(str(record.exc_info[1])),
            }
        return json.dumps(entry)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(JSONFormatter())
        logger.addHandler(h)
        logger.propagate = False
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger
