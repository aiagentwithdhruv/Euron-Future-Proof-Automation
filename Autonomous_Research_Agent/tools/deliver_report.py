"""Deliver report.md to Slack + Email + Telegram (best-effort, skip missing creds).

Usage:
    python tools/deliver_report.py --report .tmp/report.md --channels slack,email,telegram
    python tools/deliver_report.py --report .tmp/report.md --dry-run
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from shared.env_loader import load_env, get_optional
from shared.logger import info, warn, error
from shared.retry import with_retry


TELEGRAM_MAX = 4096
SLACK_MAX = 39000   # Slack 40k cap with safety margin
EMAIL_MAX = 80_000


def _escape_md_v2(text: str) -> str:
    specials = r"_*[]()~`>#+-=|{}.!"
    out = []
    for ch in text:
        if ch in specials:
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


@with_retry(max_attempts=3, base_delay=2.0)
def send_slack(webhook_url: str, report_md: str) -> dict:
    body = report_md[:SLACK_MAX]
    resp = requests.post(webhook_url, json={"text": body}, timeout=15)
    resp.raise_for_status()
    # Slack returns plain "ok"
    return {"ok": resp.text.strip() == "ok", "body": resp.text.strip()[:200]}


@with_retry(max_attempts=3, base_delay=2.0)
def send_telegram(bot_token: str, chat_id: str, report_md: str) -> dict:
    text = report_md
    if len(text) > TELEGRAM_MAX:
        text = text[:TELEGRAM_MAX - 40] + "\n\n…(truncated)"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    # Send as plain text — our markdown is rich (headings, bullets), MarkdownV2
    # would require heavy escaping on dynamic content.
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


@with_retry(max_attempts=3, base_delay=2.0)
def send_email(resend_key: str, from_addr: str, to_addr: str, subject: str, report_md: str) -> dict:
    html = "<pre style='font-family:ui-monospace,Menlo,monospace;white-space:pre-wrap;'>" + \
           report_md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</pre>"
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
        json={
            "from": from_addr,
            "to": [to_addr],
            "subject": subject,
            "html": html[:EMAIL_MAX],
            "text": report_md[:EMAIL_MAX],
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Deliver report to Slack + Email + Telegram")
    parser.add_argument("--report", required=True)
    parser.add_argument("--channels", default="slack,email,telegram",
                        help="Comma-separated subset of slack,email,telegram")
    parser.add_argument("--subject-prefix", default="Competitor Digest")
    parser.add_argument("--dry-run", action="store_true", help="Don't send, just preview")
    args = parser.parse_args()

    load_env()
    project_root = Path(__file__).parent.parent
    report_path = project_root / args.report
    if not report_path.exists():
        error(f"report file missing: {report_path}")
        sys.exit(1)
    report_md = report_path.read_text()
    channels = [c.strip().lower() for c in args.channels.split(",") if c.strip()]

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    receipts: dict = {}

    if args.dry_run:
        info("dry-run — skipping delivery, writing preview only")
        preview = report_md[:1200]
        print(json.dumps({"status": "success", "dry_run": True, "preview_chars": len(preview),
                          "channels_requested": channels}))
        return

    # Slack
    if "slack" in channels:
        webhook = get_optional("SLACK_WEBHOOK_URL")
        if not webhook:
            warn("SLACK_WEBHOOK_URL missing — skip slack")
            receipts["slack"] = {"status": "skipped", "reason": "no-credentials"}
        else:
            try:
                r = send_slack(webhook, report_md)
                receipts["slack"] = {"status": "ok", **r}
            except Exception as e:
                error(f"slack failed: {e}")
                receipts["slack"] = {"status": "error", "error": str(e)}

    # Telegram
    if "telegram" in channels:
        token = get_optional("TELEGRAM_BOT_TOKEN")
        chat_id = get_optional("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            warn("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing — skip telegram")
            receipts["telegram"] = {"status": "skipped", "reason": "no-credentials"}
        else:
            try:
                r = send_telegram(token, chat_id, report_md)
                receipts["telegram"] = {"status": "ok", "message_id": r.get("result", {}).get("message_id")}
            except Exception as e:
                error(f"telegram failed: {e}")
                receipts["telegram"] = {"status": "error", "error": str(e)}

    # Email
    if "email" in channels:
        resend_key = get_optional("RESEND_API_KEY")
        email_from = get_optional("EMAIL_FROM")
        email_to = get_optional("EMAIL_TO")
        if not (resend_key and email_from and email_to):
            warn("RESEND_API_KEY / EMAIL_FROM / EMAIL_TO missing — skip email")
            receipts["email"] = {"status": "skipped", "reason": "no-credentials"}
        else:
            try:
                subject = f"{args.subject_prefix} — {date_str}"
                r = send_email(resend_key, email_from, email_to, subject, report_md)
                receipts["email"] = {"status": "ok", "id": r.get("id")}
            except Exception as e:
                error(f"email failed: {e}")
                receipts["email"] = {"status": "error", "error": str(e)}

    print(json.dumps({"status": "success", "receipts": receipts}))


if __name__ == "__main__":
    main()
