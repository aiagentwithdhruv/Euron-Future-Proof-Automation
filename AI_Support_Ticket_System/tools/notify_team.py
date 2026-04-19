"""Notify a team on Slack with the ticket + approval CLI command.

Usage:
    python tools/notify_team.py --ticket-id TICKET-...
    python tools/notify_team.py --all                   # notify every awaiting-approval ticket
    python tools/notify_team.py --ticket-id TICKET-... --dry-run
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
DRY_RUN_SINK = PROJECT_ROOT / ".tmp" / "slack_outbox.jsonl"


PRIORITY_EMOJI = {"P1": ":rotating_light:", "P2": ":warning:", "P3": ":ticket:", "P4": ":envelope:"}


def format_slack_payload(ticket: dict) -> dict:
    """Build the Slack webhook JSON for a ticket."""
    emoji = PRIORITY_EMOJI.get(ticket.get("priority", "P3"), ":ticket:")
    draft_preview = (ticket.get("draft") or "(no draft yet)")[:300]
    approve_cmd = f"python tools/approval_queue.py --approve {ticket['ticket_id']}"
    show_cmd = f"python tools/approval_queue.py --show {ticket['ticket_id']}"

    text = (
        f"{emoji} *{ticket['ticket_id']}* "
        f"[{ticket.get('priority','P?')} | {ticket.get('intent','?')} | {ticket.get('team','triage')}]\n"
        f"*From:* {ticket.get('from_email','')}\n"
        f"*Subject:* {ticket.get('subject','')}\n"
        f"*Draft preview:*\n```{draft_preview}```\n"
        f"*Review:* `{show_cmd}`\n"
        f"*Approve:* `{approve_cmd}`"
    )
    return {"text": text}


def send_to_slack(payload: dict, webhook_url: str) -> bool:
    try:
        import requests
    except ImportError:
        warn("requests not installed — cannot post to Slack")
        return False
    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.ok:
            return True
        warn(f"Slack webhook returned {r.status_code}: {r.text[:150]}")
    except Exception as e:
        warn(f"Slack webhook error: {e}")
    return False


def append_dry_run(payload: dict, ticket_id: str):
    out = validate_write_path(str(DRY_RUN_SINK))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ticket_id": ticket_id,
            "payload": payload,
        }) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Notify team on Slack")
    parser.add_argument("--ticket-id", help="Specific ticket")
    parser.add_argument("--all", action="store_true", help="Notify every awaiting-approval ticket")
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    parser.add_argument("--dry-run", action="store_true", help="Write payload to .tmp/slack_outbox.jsonl instead")
    args = parser.parse_args()

    if not (args.ticket_id or args.all):
        error("Provide --ticket-id or --all")
        sys.exit(1)

    load_env()
    webhook = get_optional("SLACK_WEBHOOK_URL")
    dry_run = args.dry_run or not webhook
    if dry_run and not args.dry_run:
        info("SLACK_WEBHOOK_URL not set — running in dry-run (payload → .tmp/slack_outbox.jsonl)")

    store_path = Path(args.store) if Path(args.store).is_absolute() else PROJECT_ROOT / args.store
    if not store_path.exists():
        error(f"Ticket store not found: {store_path}")
        sys.exit(1)
    tickets = json.loads(store_path.read_text())

    targets = []
    for t in tickets:
        if t.get("status") != "awaiting-approval":
            continue
        if args.ticket_id and t["ticket_id"] != args.ticket_id:
            continue
        if t.get("slack_notified_at"):
            continue  # idempotent
        targets.append(t)

    if not targets:
        info("No tickets to notify")
        print(json.dumps({"status": "success", "notified": 0}))
        return

    sent, skipped = 0, 0
    for t in targets:
        payload = format_slack_payload(t)
        if dry_run:
            append_dry_run(payload, t["ticket_id"])
            t["slack_notified_at"] = datetime.now(timezone.utc).isoformat()
            t["slack_mode"] = "dry-run"
            sent += 1
        else:
            if send_to_slack(payload, webhook):
                t["slack_notified_at"] = datetime.now(timezone.utc).isoformat()
                t["slack_mode"] = "live"
                sent += 1
            else:
                skipped += 1

    store_path.write_text(json.dumps(tickets, indent=2, ensure_ascii=False))
    print(json.dumps({
        "status": "success",
        "notified": sent,
        "skipped": skipped,
        "mode": "dry-run" if dry_run else "live",
    }))


if __name__ == "__main__":
    main()
