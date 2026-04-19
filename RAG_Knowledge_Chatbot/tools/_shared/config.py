"""
Env loader + config accessor. No RAG logic.
Loads .env at import time, exposes typed getters.
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def _load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()


def get(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def require(*keys: str) -> dict[str, str]:
    missing: list[str] = []
    out: dict[str, str] = {}
    for k in keys:
        v = os.environ.get(k)
        if not v:
            missing.append(k)
        else:
            out[k] = v
    if missing:
        raise EnvironmentError(
            f"Missing required env vars: {', '.join(missing)}. "
            f"Set them in {ENV_PATH} (see .env.example)."
        )
    return out


def get_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def get_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default
