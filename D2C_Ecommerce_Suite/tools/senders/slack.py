"""Slack sender — incoming webhook. Used for internal alerts (low stock, negative reviews)."""

from __future__ import annotations

from typing import Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_url  # noqa: E402

from tools.config import env

logger = get_logger(__name__)


def send_slack(
    *,
    message: str,
    webhook_url: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    if not message:
        raise ValueError("message is required")
    if len(message) > 3500:
        raise ValueError("Slack message too long (>3500 chars)")

    if dry_run:
        logger.info("slack dry-run", extra={"outputs": {"len": len(message)}})
        return {"status": "success", "dry_run": True, "channel": "slack", "preview": message[:200]}

    url = webhook_url or env("SLACK_WEBHOOK_URL")
    if not url:
        logger.warning("SLACK_WEBHOOK_URL missing — falling back to dry-run")
        return send_slack(message=message, dry_run=True)

    url = validate_url(url)

    import requests

    resp = requests.post(url, json={"text": message}, timeout=10)
    if resp.status_code >= 400 or resp.text.strip().lower() != "ok":
        raise RuntimeError(f"Slack webhook failed {resp.status_code}: {resp.text[:200]}")

    logger.info("slack posted")
    return {"status": "success", "channel": "slack", "provider": "slack_webhook"}
