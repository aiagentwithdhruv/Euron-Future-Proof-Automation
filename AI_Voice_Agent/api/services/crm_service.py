"""Supabase CRM — leads, customers, call_logs, dnc_list via PostgREST."""

from __future__ import annotations

from typing import Any

import httpx

from api.config import get_settings
from api.logging_utils import get_logger


logger = get_logger(__name__)


class CRMError(RuntimeError):
    pass


class CRMService:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self._settings.supabase_url and self._settings.supabase_service_key)

    def _headers(self, prefer: str = "return=representation") -> dict[str, str]:
        key = self._settings.supabase_service_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": prefer,
        }

    def _url(self, path: str) -> str:
        return f"{self._settings.supabase_url.rstrip('/')}/rest/v1/{path.lstrip('/')}"

    def _assert_enabled(self) -> None:
        if not self.enabled:
            raise CRMError("Supabase not configured (set SUPABASE_URL + SUPABASE_SERVICE_KEY)")

    # ---------- Customers / Leads ----------

    def lookup_customer(self, phone: str) -> dict[str, Any] | None:
        self._assert_enabled()
        params = {"phone": f"eq.{phone}", "limit": "1"}
        with httpx.Client(timeout=10.0) as client:
            r = client.get(self._url("customers"), headers=self._headers(), params=params)
            if r.status_code == 200 and r.json():
                return r.json()[0]
            # Fall back to leads table
            r2 = client.get(self._url("leads"), headers=self._headers(), params=params)
            if r2.status_code == 200 and r2.json():
                return r2.json()[0]
        return None

    def upsert_lead(self, data: dict[str, Any]) -> dict[str, Any]:
        self._assert_enabled()
        payload = {k: v for k, v in data.items() if v is not None}
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                self._url("leads"),
                headers={**self._headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
                json=payload,
            )
            if r.status_code >= 400:
                raise CRMError(f"Supabase lead upsert failed: {r.status_code} {r.text[:300]}")
            data = r.json()
            return data[0] if isinstance(data, list) and data else data

    def is_on_dnc(self, phone: str) -> bool:
        if not self.enabled:
            return False
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                self._url("dnc_list"),
                headers=self._headers(),
                params={"phone": f"eq.{phone}", "limit": "1"},
            )
            return r.status_code == 200 and bool(r.json())

    def add_to_dnc(self, phone: str, reason: str = "customer_request") -> None:
        self._assert_enabled()
        with httpx.Client(timeout=10.0) as client:
            client.post(
                self._url("dnc_list"),
                headers={**self._headers(), "Prefer": "resolution=ignore-duplicates"},
                json={"phone": phone, "reason": reason},
            )

    # ---------- Call logs ----------

    def insert_call_log(self, data: dict[str, Any]) -> dict[str, Any]:
        self._assert_enabled()
        with httpx.Client(timeout=10.0) as client:
            r = client.post(self._url("call_logs"), headers=self._headers(), json=data)
            if r.status_code >= 400:
                raise CRMError(f"Supabase call_logs insert failed: {r.status_code} {r.text[:300]}")
            payload = r.json()
            return payload[0] if isinstance(payload, list) and payload else payload

    def update_call_log(self, call_id: str, data: dict[str, Any]) -> None:
        self._assert_enabled()
        with httpx.Client(timeout=10.0) as client:
            r = client.patch(
                self._url("call_logs"),
                headers=self._headers(),
                params={"call_id": f"eq.{call_id}"},
                json=data,
            )
            if r.status_code >= 400:
                logger.warning("crm.update_call_log.failed", extra={"status": r.status_code})
