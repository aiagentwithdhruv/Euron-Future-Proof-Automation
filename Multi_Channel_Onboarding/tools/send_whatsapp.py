#!/usr/bin/env python3
"""Tool: send_whatsapp

Send a WhatsApp message via Twilio Messages API.
Supports --dry-run so dev never hits real numbers.

Input: --to (E.164 phone), --message, optional --from, --dry-run
Output: JSON receipt on stdout
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

E164 = re.compile(r"^\+\d{7,15}$")


def validate_phone(raw: str) -> str:
    cleaned = re.sub(r"[^\d+]", "", raw or "")
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    if not E164.match(cleaned):
        raise ValueError(f"Invalid E.164 phone: {cleaned}")
    return cleaned


def send_via_twilio(sid: str, token: str, from_num: str, to_num: str, body: str) -> dict:
    import requests

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    data = {
        "From": from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}",
        "To": f"whatsapp:{to_num}",
        "Body": body,
    }
    resp = requests.post(url, data=data, auth=(sid, token), timeout=15)
    if resp.status_code >= 400:
        raise RuntimeError(f"Twilio error {resp.status_code}: {resp.text[:300]}")
    payload = resp.json()
    return {"provider": "twilio", "message_id": payload.get("sid"), "status": payload.get("status")}


def main():
    parser = argparse.ArgumentParser(description="Send a WhatsApp message (Twilio)")
    parser.add_argument("--to", required=True, help="Recipient phone in E.164, e.g. +919876543210")
    parser.add_argument("--message", required=True, help="Message body")
    parser.add_argument("--from", dest="from_num", help="Override TWILIO_WHATSAPP_FROM")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, do not send")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    try:
        to_num = validate_phone(args.to)
    except ValueError as e:
        print(json.dumps({"status": "error", "code": "invalid_phone", "detail": str(e)}), file=sys.stderr)
        sys.exit(2)

    if len(args.message) > 1500:
        print(json.dumps({"status": "error", "code": "message_too_long", "detail": "max 1500 chars"}), file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        masked_to = to_num[:4] + "****" + to_num[-2:] if len(to_num) > 6 else "****"
        logger.info("send_whatsapp dry-run", extra={"outputs": {"to": masked_to}})
        print(json.dumps({
            "status": "success",
            "dry_run": True,
            "channel": "whatsapp",
            "to": to_num,
            "message_preview": args.message[:160],
        }))
        return

    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_num = args.from_num or os.environ.get("TWILIO_WHATSAPP_FROM")

    if not (sid and token and from_num):
        err = "Missing Twilio creds. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM, or use --dry-run."
        print(json.dumps({"status": "error", "code": "missing_creds", "detail": err}), file=sys.stderr)
        sys.exit(1)

    try:
        receipt = send_via_twilio(sid, token, from_num, to_num, args.message)
    except Exception as e:
        logger.error(f"whatsapp send failed: {e}")
        print(json.dumps({"status": "error", "code": "send_failed", "detail": str(e)}), file=sys.stderr)
        sys.exit(1)

    result = {"status": "success", "channel": "whatsapp", "to": to_num, **receipt}
    logger.info("whatsapp_sent", extra={"outputs": {"provider": "twilio", "status": receipt.get("status")}})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
