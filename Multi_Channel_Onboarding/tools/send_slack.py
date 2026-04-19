#!/usr/bin/env python3
"""Tool: send_slack

Post an internal alert to a Slack Incoming Webhook.
Supports --dry-run.

Input: --message (required), optional --webhook-url, --dry-run
Output: JSON receipt on stdout
"""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_url  # noqa: E402

logger = get_logger(__name__)


def post_webhook(url: str, message: str) -> dict:
    import requests

    resp = requests.post(url, json={"text": message}, timeout=10)
    if resp.status_code >= 400 or resp.text.strip().lower() != "ok":
        raise RuntimeError(f"Slack webhook failed {resp.status_code}: {resp.text[:200]}")
    return {"provider": "slack_webhook", "ok": True}


def main():
    parser = argparse.ArgumentParser(description="Post message to Slack via incoming webhook")
    parser.add_argument("--message", required=True, help="Alert text")
    parser.add_argument("--webhook-url", help="Override SLACK_WEBHOOK_URL")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, do not post")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    if len(args.message) > 3500:
        print(json.dumps({"status": "error", "code": "message_too_long"}), file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        logger.info("send_slack dry-run")
        print(json.dumps({
            "status": "success",
            "dry_run": True,
            "channel": "slack",
            "message_preview": args.message[:200],
        }))
        return

    webhook = args.webhook_url or os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        print(json.dumps({
            "status": "error",
            "code": "missing_webhook",
            "detail": "Set SLACK_WEBHOOK_URL in .env or use --dry-run.",
        }), file=sys.stderr)
        sys.exit(1)

    try:
        webhook = validate_url(webhook)
        receipt = post_webhook(webhook, args.message)
    except ValueError as e:
        print(json.dumps({"status": "error", "code": "invalid_url", "detail": str(e)}), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        logger.error(f"slack send failed: {e}")
        print(json.dumps({"status": "error", "code": "send_failed", "detail": str(e)}), file=sys.stderr)
        sys.exit(1)

    result = {"status": "success", "channel": "slack", **receipt}
    logger.info("slack_posted")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
