"""Per-run structured logging — each module writes a row under runs/.

Keeps a single JSONL file per day per module (easy to tail, cheap to scan).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools._bootstrap import runs_dir


def log_run(module: str, event: str, payload: dict[str, Any]) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = runs_dir() / f"{today}-{module}.jsonl"
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "module": module,
        "event": event,
        **payload,
    }
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return path
