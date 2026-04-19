"""Send an approved ticket reply via Resend. Dry-run writes to .tmp/sent_replies.jsonl.

Usage:
    python tools/send_reply.py --ticket-id TICKET-...
    python tools/send_reply.py --ticket-id TICKET-... --dry-run

Called by approval_queue.py on --approve.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, warn, error
from shared.sandbox import validate_write_path


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_STORE = PROJECT_ROOT / "output" / "tickets.json"
DRY_RUN_SINK = PROJECT_ROOT / ".tmp" / "sent_replies.jsonl"


def send_resend(to_email: str, from_email: str, subject: str, body: str, headers: dict) -> dict | None:
    """POST to Resend /emails. Returns response dict or None on failure."""
    api_key = get_optional("RESEND_API_KEY")
    if not (api_key and from_email):
        return None
    try:
        import requests
    except ImportError:
        warn("requests not installed — cannot send email")
        return None
    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }
    if headers:
        payload["headers"] = headers
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=15,
        )
        if r.ok:
            return r.json()
        warn(f"Resend error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        warn(f"Resend exception: {e}")
    return None


def append_dry_run(record: dict):
    out = validate_write_path(str(DRY_RUN_SINK))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:
        f.write(json.dumps(record) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Send approved reply")
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    from_email = get_optional("EMAIL_FROM")
    api_key = get_optional("RESEND_API_KEY")
    dry_run = args.dry_run or not (api_key and from_email)
    if dry_run and not args.dry_run:
        info("Resend not configured — dry-run (payload → .tmp/sent_replies.jsonl)")

    store_path = Path(args.store) if Path(args.store).is_absolute() else PROJECT_ROOT / args.store
    tickets = json.loads(store_path.read_text())
    ticket = next((t for t in tickets if t["ticket_id"] == args.ticket_id), None)
    if not ticket:
        error(f"Ticket not found: {args.ticket_id}")
        sys.exit(1)

    if ticket.get("status") == "sent":
        info(f"Ticket {args.ticket_id} already sent — skipping")
        print(json.dumps({"status": "skipped", "reason": "already-sent", "ticket_id": args.ticket_id}))
        return

    if ticket.get("status") not in ("approved", "awaiting-approval"):
        error(f"Ticket status must be 'approved' before send, got '{ticket.get('status')}'")
        sys.exit(2)

    body = ticket.get("final_text") or ticket.get("draft") or ""
    if not body.strip():
        error(f"No draft/final_text to send for {args.ticket_id}")
        sys.exit(2)

    to_email = ticket.get("from_email")
    if not to_email:
        error(f"No recipient email on ticket {args.ticket_id}")
        sys.exit(2)

    subject_prefix = "Re: " if not (ticket.get("subject", "").lower().startswith("re:")) else ""
    subject = f"{subject_prefix}{ticket.get('subject','Your support request')}"

    headers = {}
    if ticket.get("in_reply_to"):
        headers["In-Reply-To"] = ticket["in_reply_to"]
    if ticket.get("references"):
        headers["References"] = ticket["references"]

    now = datetime.now(timezone.utc).isoformat()
    record = {
        "ticket_id": args.ticket_id,
        "to": to_email,
        "from": from_email or "(dry-run, no EMAIL_FROM)",
        "subject": subject,
        "body": body,
        "headers": headers,
        "sent_at": now,
        "mode": "dry-run" if dry_run else "live",
    }

    if dry_run:
        append_dry_run(record)
        resend_response = None
    else:
        resend_response = send_resend(to_email, from_email, subject, body, headers)
        if resend_response is None:
            error("Resend send failed — leaving ticket in current status")
            sys.exit(3)

    ticket["status"] = "sent"
    ticket["sent_at"] = now
    ticket["send_mode"] = "dry-run" if dry_run else "live"
    if resend_response:
        ticket["resend_id"] = resend_response.get("id")
    ticket["updated_at"] = now

    store_path.write_text(json.dumps(tickets, indent=2, ensure_ascii=False))

    print(json.dumps({
        "status": "success",
        "ticket_id": args.ticket_id,
        "mode": "dry-run" if dry_run else "live",
        "to": to_email,
    }))


if __name__ == "__main__":
    main()
