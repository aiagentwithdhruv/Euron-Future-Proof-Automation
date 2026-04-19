"""JSON-backed state store for the pipeline.

One file per table:
  state/pipeline.json     -> {prospect_id: prospect_record}
  state/transitions.log   -> append-only JSONL of stage transitions
  state/suppression.json  -> [{"email": "...", "reason": "...", "at": "..."}]
  state/enrich_cache.json -> {domain: enrich_result}
  state/replies.json      -> [{"prospect_id": "...", "at": "...", ...}]

Airtable mirror is optional (AIRTABLE_API_KEY).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(exist_ok=True)

PIPELINE_PATH = STATE_DIR / "pipeline.json"
TRANSITIONS_PATH = STATE_DIR / "transitions.log"
SUPPRESSION_PATH = STATE_DIR / "suppression.json"
ENRICH_CACHE_PATH = STATE_DIR / "enrich_cache.json"
REPLIES_PATH = STATE_DIR / "replies.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


# ── Prospect CRUD ─────────────────────────────────────────────────

def new_prospect_id() -> str:
    return f"prs_{uuid.uuid4().hex[:10]}"


def load_pipeline() -> dict:
    return _read_json(PIPELINE_PATH, {})


def save_pipeline(pipeline: dict) -> None:
    _write_json(PIPELINE_PATH, pipeline)


def upsert_prospect(record: dict) -> dict:
    pipeline = load_pipeline()
    pid = record.get("prospect_id") or new_prospect_id()
    record["prospect_id"] = pid
    record.setdefault("created_at", _now())
    record["updated_at"] = _now()
    existing = pipeline.get(pid, {})
    merged = {**existing, **record}
    pipeline[pid] = merged
    save_pipeline(pipeline)
    return merged


def get_prospect(prospect_id: str) -> dict | None:
    return load_pipeline().get(prospect_id)


def prospects_where(status: str | None = None, stage: str | None = None) -> list[dict]:
    pipeline = load_pipeline()
    out = []
    for p in pipeline.values():
        if status and p.get("status") != status:
            continue
        if stage and p.get("stage") != stage:
            continue
        out.append(p)
    return out


def transition(prospect_id: str, new_stage: str, new_status: str, reason: str = "") -> dict:
    pipeline = load_pipeline()
    p = pipeline.get(prospect_id)
    if not p:
        raise KeyError(f"unknown prospect: {prospect_id}")
    old_stage = p.get("stage")
    old_status = p.get("status")
    p["stage"] = new_stage
    p["status"] = new_status
    p["updated_at"] = _now()
    pipeline[prospect_id] = p
    save_pipeline(pipeline)

    with TRANSITIONS_PATH.open("a") as f:
        f.write(json.dumps({
            "at": _now(),
            "prospect_id": prospect_id,
            "from_stage": old_stage,
            "from_status": old_status,
            "to_stage": new_stage,
            "to_status": new_status,
            "reason": reason,
        }) + "\n")
    return p


# ── Suppression (CAN-SPAM / DPDP opt-out) ─────────────────────────

def load_suppression() -> list[dict]:
    return _read_json(SUPPRESSION_PATH, [])


def is_suppressed(email: str) -> bool:
    if not email:
        return False
    email = email.lower().strip()
    return any(entry.get("email", "").lower() == email for entry in load_suppression())


def add_suppression(email: str, reason: str = "manual") -> None:
    if not email:
        return
    data = load_suppression()
    email = email.lower().strip()
    if any(e.get("email", "").lower() == email for e in data):
        return
    data.append({"email": email, "reason": reason, "at": _now()})
    _write_json(SUPPRESSION_PATH, data)


# ── Enrich cache ──────────────────────────────────────────────────

def cache_get(domain: str) -> dict | None:
    if not domain:
        return None
    return _read_json(ENRICH_CACHE_PATH, {}).get(domain.lower())


def cache_set(domain: str, data: dict) -> None:
    if not domain:
        return
    cache = _read_json(ENRICH_CACHE_PATH, {})
    cache[domain.lower()] = {**data, "cached_at": _now()}
    _write_json(ENRICH_CACHE_PATH, cache)


# ── Replies inbox ─────────────────────────────────────────────────

def record_reply(prospect_id: str, sentiment: str, body_preview: str = "") -> None:
    replies = _read_json(REPLIES_PATH, [])
    replies.append({
        "prospect_id": prospect_id,
        "sentiment": sentiment,
        "body_preview": body_preview[:400],
        "at": _now(),
    })
    _write_json(REPLIES_PATH, replies)
