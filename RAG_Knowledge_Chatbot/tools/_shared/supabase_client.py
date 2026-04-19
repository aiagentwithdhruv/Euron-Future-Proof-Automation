"""
Supabase REST client (no SDK dependency).
Exposes three primitives: upsert, rpc, insert. No RAG logic here.
"""
from __future__ import annotations

from typing import Any

import requests

from tools._shared import config
from tools._shared.logger import get_logger

logger = get_logger(__name__)


def _headers() -> dict[str, str]:
    creds = config.require("SUPABASE_URL", "SUPABASE_SERVICE_KEY")
    return {
        "apikey": creds["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {creds['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates",
    }


def _base() -> str:
    return config.require("SUPABASE_URL")["SUPABASE_URL"].rstrip("/")


def upsert(table: str, rows: list[dict[str, Any]], on_conflict: str) -> list[dict]:
    """Upsert rows into a table. `on_conflict` = column name for ON CONFLICT."""
    if not rows:
        return []
    url = f"{_base()}/rest/v1/{table}?on_conflict={on_conflict}"
    r = requests.post(url, headers=_headers(), json=rows, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else []


def insert(table: str, row: dict[str, Any]) -> dict:
    url = f"{_base()}/rest/v1/{table}"
    r = requests.post(url, headers=_headers(), json=row, timeout=30)
    r.raise_for_status()
    data = r.json() if r.content else []
    return data[0] if isinstance(data, list) and data else {}


def rpc(fn: str, params: dict[str, Any]) -> Any:
    url = f"{_base()}/rest/v1/rpc/{fn}"
    r = requests.post(url, headers=_headers(), json=params, timeout=30)
    r.raise_for_status()
    return r.json()
