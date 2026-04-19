"""Email sender — Resend API. Matches Multi_Channel_Onboarding behaviour.

Always safe: when `dry_run=True` or no RESEND_API_KEY is set, the function
returns a synthetic receipt and sends nothing.
"""

from __future__ import annotations

import json
from typing import Optional

import tools._bootstrap  # noqa: F401 — wire sys.path

from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_email  # noqa: E402

from tools.config import env

logger = get_logger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html: Optional[str] = None,
    from_addr: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    to_addr = validate_email(to)
    if not subject or not (body or html):
        raise ValueError("subject and (body or html) are required")

    sender = from_addr or env("EMAIL_FROM") or "d2c@example.com"

    if dry_run:
        logger.info(
            "email dry-run",
            extra={"outputs": {"to": to_addr, "subject": subject, "len": len(body or html or "")}},
        )
        return {
            "status": "success",
            "dry_run": True,
            "channel": "email",
            "to": to_addr,
            "from": sender,
            "subject": subject,
            "preview": (body or html or "")[:160],
        }

    api_key = env("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY missing — falling back to dry-run")
        return send_email(to=to_addr, subject=subject, body=body, html=html, from_addr=sender, dry_run=True)

    import requests  # local import so dry-runs don't need it

    payload = {"from": sender, "to": [to_addr], "subject": subject}
    if html:
        payload["html"] = html
    if body:
        payload["text"] = body

    resp = requests.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    logger.info("email sent", extra={"outputs": {"to": to_addr, "id": data.get("id")}})
    return {
        "status": "success",
        "channel": "email",
        "to": to_addr,
        "from": sender,
        "provider": "resend",
        "message_id": data.get("id"),
    }
