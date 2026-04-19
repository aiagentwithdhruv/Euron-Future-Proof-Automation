#!/usr/bin/env python3
"""Tool: send_email

Send a single transactional email. Resend API primary, SMTP fallback.
Supports --dry-run so dev never hits real users.

Input: --to, --subject, --body (or --body-file), optional --from, --dry-run
Output: JSON receipt on stdout
"""

import argparse
import json
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_email  # noqa: E402

logger = get_logger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def send_via_resend(api_key: str, from_addr: str, to: str, subject: str, body: str) -> dict:
    import requests

    resp = requests.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": from_addr, "to": [to], "subject": subject, "text": body},
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return {"provider": "resend", "message_id": data.get("id")}


def send_via_smtp(
    host: str, port: int, user: str, password: str, from_addr: str, to: str, subject: str, body: str
) -> dict:
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.starttls(context=ctx)
        if user and password:
            server.login(user, password)
        server.send_message(msg)

    return {"provider": "smtp", "message_id": msg["Message-ID"] or "smtp-sent"}


def main():
    parser = argparse.ArgumentParser(description="Send transactional email (Resend | SMTP)")
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--body", help="Plain-text body")
    group.add_argument("--body-file", help="Path to file containing the body")
    parser.add_argument("--from", dest="from_addr", help="Override EMAIL_FROM")
    parser.add_argument("--dry-run", action="store_true", help="Print payload, do not send")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    try:
        to_addr = validate_email(args.to)
    except ValueError as e:
        print(json.dumps({"status": "error", "code": "invalid_email", "detail": str(e)}), file=sys.stderr)
        sys.exit(2)

    body = args.body
    if args.body_file:
        body_path = Path(args.body_file)
        if not body_path.is_absolute():
            body_path = PROJECT_ROOT / body_path
        body = body_path.read_text()

    from_addr = args.from_addr or os.environ.get("EMAIL_FROM") or "onboarding@example.com"

    if args.dry_run:
        logger.info("send_email dry-run", extra={"outputs": {"to": to_addr, "subject": args.subject}})
        print(json.dumps({
            "status": "success",
            "dry_run": True,
            "channel": "email",
            "to": to_addr,
            "from": from_addr,
            "subject": args.subject,
            "body_preview": body[:160],
        }))
        return

    resend_key = os.environ.get("RESEND_API_KEY")
    smtp_host = os.environ.get("SMTP_HOST")

    try:
        if resend_key:
            receipt = send_via_resend(resend_key, from_addr, to_addr, args.subject, body)
        elif smtp_host:
            receipt = send_via_smtp(
                smtp_host,
                int(os.environ.get("SMTP_PORT", "587")),
                os.environ.get("SMTP_USER", ""),
                os.environ.get("SMTP_PASS", ""),
                from_addr,
                to_addr,
                args.subject,
                body,
            )
        else:
            raise RuntimeError(
                "No email provider configured. Set RESEND_API_KEY or SMTP_HOST in .env, "
                "or re-run with --dry-run."
            )
    except Exception as e:
        logger.error(f"email send failed: {e}")
        print(json.dumps({"status": "error", "code": "send_failed", "detail": str(e)}), file=sys.stderr)
        sys.exit(1)

    result = {"status": "success", "channel": "email", "to": to_addr, **receipt}
    logger.info("email_sent", extra={"outputs": {"to": to_addr, "provider": receipt["provider"]}})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
