"""Idempotency store — Shopify replays webhooks, so every event must be de-duped.

File-backed (SQLite at .tmp/idempotency.db). One row per (source, key). The
primary key is the Shopify webhook id (`X-Shopify-Webhook-Id`) when present;
for platforms that don't supply one, we fall back to a SHA-256 of the raw body.

A returned `False` from `mark()` means this event has been seen — skip.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from tools._bootstrap import tmp_dir

_DB_PATH = tmp_dir() / "idempotency.db"
_LOCK = threading.Lock()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH), timeout=5, isolation_level=None)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_events (
            source TEXT NOT NULL,
            event_key TEXT NOT NULL,
            topic TEXT,
            first_seen_ts REAL NOT NULL,
            PRIMARY KEY (source, event_key)
        )
        """
    )
    return conn


def body_hash(raw_body: bytes) -> str:
    return hashlib.sha256(raw_body).hexdigest()


def mark(source: str, event_key: str, topic: Optional[str] = None) -> bool:
    """Mark an event as processed. Returns True on first-seen, False on duplicate."""
    if not event_key:
        return True  # can't dedupe without a key — process defensively
    with _LOCK:
        conn = _conn()
        try:
            try:
                conn.execute(
                    "INSERT INTO processed_events (source, event_key, topic, first_seen_ts) "
                    "VALUES (?, ?, ?, ?)",
                    (source, event_key, topic, time.time()),
                )
                return True
            except sqlite3.IntegrityError:
                return False
        finally:
            conn.close()


def has_seen(source: str, event_key: str) -> bool:
    if not event_key:
        return False
    with _LOCK:
        conn = _conn()
        try:
            cur = conn.execute(
                "SELECT 1 FROM processed_events WHERE source = ? AND event_key = ?",
                (source, event_key),
            )
            return cur.fetchone() is not None
        finally:
            conn.close()


def reset(path: Optional[Path] = None) -> None:
    """Test helper: wipe the store."""
    target = path or _DB_PATH
    if target.exists():
        target.unlink()
