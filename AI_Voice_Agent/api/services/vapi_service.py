"""Vapi outbound helpers — push calls to Vapi's queue API."""

from __future__ import annotations

from typing import Any

import httpx

from api.config import get_settings
from api.logging_utils import get_logger


logger = get_logger(__name__)


class VapiError(RuntimeError):
    pass


class VapiService:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        s = self._settings
        return bool(s.vapi_api_key and s.vapi_assistant_id and s.vapi_phone_number_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.vapi_api_key}",
            "Content-Type": "application/json",
        }

    def place_outbound(
        self,
        customer_phone: str,
        assistant_variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise VapiError("Vapi not configured (set VAPI_API_KEY + VAPI_ASSISTANT_ID + VAPI_PHONE_NUMBER_ID)")
        s = self._settings
        body: dict[str, Any] = {
            "assistantId": s.vapi_assistant_id,
            "phoneNumberId": s.vapi_phone_number_id,
            "customer": {"number": customer_phone},
        }
        if assistant_variables:
            body["assistantOverrides"] = {"variableValues": assistant_variables}
        with httpx.Client(timeout=30.0) as client:
            r = client.post(f"{s.vapi_api_base.rstrip('/')}/call", headers=self._headers(), json=body)
            if r.status_code >= 400:
                raise VapiError(f"Vapi outbound failed: {r.status_code} {r.text[:400]}")
            logger.info("vapi.outbound.placed", extra={"call_id": r.json().get("id", "")})
            return r.json()
