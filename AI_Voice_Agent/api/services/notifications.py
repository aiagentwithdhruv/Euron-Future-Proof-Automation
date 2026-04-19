"""Twilio SMS + Resend email. Both via direct httpx — no heavyweight SDK deps."""

from __future__ import annotations

from typing import Any

import httpx

from api.config import get_settings
from api.logging_utils import get_logger


logger = get_logger(__name__)


class NotificationError(RuntimeError):
    pass


class NotificationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def sms_enabled(self) -> bool:
        s = self._settings
        return bool(s.twilio_account_sid and s.twilio_auth_token and s.twilio_from)

    @property
    def email_enabled(self) -> bool:
        s = self._settings
        return bool(s.resend_api_key and s.email_from)

    def send_sms(self, to: str, body: str) -> dict[str, Any]:
        if not self.sms_enabled:
            raise NotificationError("Twilio not configured")
        s = self._settings
        url = f"https://api.twilio.com/2010-04-01/Accounts/{s.twilio_account_sid}/Messages.json"
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                url,
                auth=(s.twilio_account_sid, s.twilio_auth_token),
                data={"From": s.twilio_from, "To": to, "Body": body},
            )
            if r.status_code >= 400:
                raise NotificationError(f"Twilio send failed: {r.status_code} {r.text[:300]}")
            data = r.json()
            logger.info("sms.sent", extra={"sid": data.get("sid")})
            return {"sid": data.get("sid"), "status": data.get("status")}

    def send_email(self, to: str, subject: str, html: str, text: str | None = None) -> dict[str, Any]:
        if not self.email_enabled:
            raise NotificationError("Resend not configured")
        s = self._settings
        payload: dict[str, Any] = {
            "from": s.email_from,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if text:
            payload["text"] = text
        with httpx.Client(timeout=10.0) as client:
            r = client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {s.resend_api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if r.status_code >= 400:
                raise NotificationError(f"Resend send failed: {r.status_code} {r.text[:300]}")
            data = r.json()
            logger.info("email.sent", extra={"id": data.get("id")})
            return {"id": data.get("id")}
