"""Lightweight .env loader. Also supports CI env vars (GITHUB_ACTIONS)."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


def load_env(env_path: str | Path | None = None) -> None:
    path = Path(env_path) if env_path else ENV_PATH
    if not path.exists():
        if os.getenv("GITHUB_ACTIONS") or os.getenv("CI"):
            return
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


def require(*keys: str) -> dict:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(
            f"Missing env vars: {', '.join(missing)}. Set them in {ENV_PATH}."
        )
    return {k: os.environ[k] for k in keys}


def get(key: str, default=None):
    return os.environ.get(key, default)


def is_dry_run(cli_flag: bool) -> bool:
    if cli_flag:
        return True
    return os.environ.get("DRY_RUN_DEFAULT", "").lower() == "true"
