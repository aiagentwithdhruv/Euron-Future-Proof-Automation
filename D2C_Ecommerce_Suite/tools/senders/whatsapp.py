"""WhatsApp sender — Twilio Messages API. Mirrors Multi_Channel_Onboarding.

Template messages (pre-approved) should be used in production. For dev, we
rely on Twilio's sandbox + `dry_run=True`.
"""

from __future__ import annotations

import re
from typing import Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from tools.config import env

logger = get_logger(__name__)

E164 = re.compile(r"^\+\d{7,15}$")


def _normalize_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw or "")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    if not E164.match(cleaned):
        raise ValueError(f"Invalid E.164 phone: {cleaned}")
    return cleaned


def send_whatsapp(
    *,
    to: str,
    message: str,
    from_num: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    to_num = _normalize_phone(to)
    if not message:
        raise ValueError("message is required")
    if len(message) > 1500:
        raise ValueError("WhatsApp message too long (>1500 chars)")

    if dry_run:
        masked = to_num[:4] + "****" + to_num[-2:] if len(to_num) > 6 else "****"
        logger.info("whatsapp dry-run", extra={"outputs": {"to": masked, "len": len(message)}})
        return {
            "status": "success",
            "dry_run": True,
            "channel": "whatsapp",
            "to": to_num,
            "preview": message[:160],
        }

    sid = env("TWILIO_ACCOUNT_SID")
    token = env("TWILIO_AUTH_TOKEN")
    sender = from_num or env("TWILIO_WHATSAPP_FROM")
    if not (sid and token and sender):
        logger.warning("Twilio creds missing — falling back to dry-run")
        return send_whatsapp(to=to_num, message=message, from_num=sender, dry_run=True)

    import requests

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {
        "From": sender if sender.startswith("whatsapp:") else f"whatsapp:{sender}",
        "To": f"whatsapp:{to_num}",
        "Body": message,
    }
    resp = requests.post(url, data=data, auth=(sid, token), timeout=15)
    if resp.status_code >= 400:
        raise RuntimeError(f"Twilio error {resp.status_code}: {resp.text[:300]}")

    payload = resp.json()
    logger.info("whatsapp sent", extra={"outputs": {"sid": payload.get("sid"), "status": payload.get("status")}})
    return {
        "status": "success",
        "channel": "whatsapp",
        "to": to_num,
        "provider": "twilio",
        "message_id": payload.get("sid"),
        "twilio_status": payload.get("status"),
    }
