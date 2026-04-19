"""Airtable MVP dashboard store.

Tables expected (configurable via env):
  - Orders     -> AIRTABLE_ORDERS_TABLE   (default: Orders)
  - Tickets    -> AIRTABLE_TICKETS_TABLE  (default: Tickets)
  - Reviews    -> AIRTABLE_REVIEWS_TABLE  (default: Reviews)
  - Carts      -> AIRTABLE_CARTS_TABLE    (default: Carts)

Rows are created via POST; updates go via PATCH by record id. If Airtable is
not configured, every call falls back to writing a JSONL row under
`.tmp/airtable/<table>.jsonl` so local runs still have persistent state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from tools.config import env

logger = get_logger(__name__)

API_BASE = "https://api.airtable.com/v0"


def _tmp_sink(table: str) -> Path:
    sink = Path(__file__).resolve().parent.parent / ".tmp" / "airtable"
    sink.mkdir(parents=True, exist_ok=True)
    return sink / f"{table}.jsonl"


class AirtableStore:
    def __init__(self, api_key: Optional[str] = None, base_id: Optional[str] = None):
        self.api_key = api_key or env("AIRTABLE_API_KEY")
        self.base_id = base_id or env("AIRTABLE_BASE_ID")

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.base_id)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _url(self, table: str, record_id: Optional[str] = None) -> str:
        base = f"{API_BASE}/{self.base_id}/{table}"
        return f"{base}/{record_id}" if record_id else base

    def create(self, table: str, fields: dict[str, Any]) -> dict:
        fields = {**fields, "CreatedAt": _iso_now()} if "CreatedAt" not in fields else fields
        if not self.available:
            return _write_local(table, {"op": "create", "fields": fields})
        import requests

        resp = requests.post(
            self._url(table),
            headers=self._headers(),
            data=json.dumps({"fields": fields}),
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.error(f"airtable create {table} {resp.status_code}: {resp.text[:200]}")
            return _write_local(table, {"op": "create", "fields": fields, "error": resp.status_code})
        return resp.json()

    def update(self, table: str, record_id: str, fields: dict[str, Any]) -> dict:
        if not self.available:
            return _write_local(table, {"op": "update", "record_id": record_id, "fields": fields})
        import requests

        resp = requests.patch(
            self._url(table, record_id),
            headers=self._headers(),
            data=json.dumps({"fields": fields}),
            timeout=15,
        )
        if resp.status_code >= 400:
            logger.error(f"airtable update {table} {resp.status_code}: {resp.text[:200]}")
            return _write_local(table, {"op": "update", "record_id": record_id, "fields": fields, "error": resp.status_code})
        return resp.json()


def _write_local(table: str, row: dict) -> dict:
    row = {**row, "_local_ts": _iso_now()}
    path = _tmp_sink(table)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"local_sink": str(path), "row": row}


def table_name(kind: str) -> str:
    defaults = {
        "orders": env("AIRTABLE_ORDERS_TABLE", "Orders"),
        "tickets": env("AIRTABLE_TICKETS_TABLE", "Tickets"),
        "reviews": env("AIRTABLE_REVIEWS_TABLE", "Reviews"),
        "carts": env("AIRTABLE_CARTS_TABLE", "Carts"),
        "stock": env("AIRTABLE_STOCK_TABLE", "Stock"),
    }
    return defaults[kind]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()
