"""Persist classified emails as tickets. Airtable if configured, else local JSON.

Usage:
    python tools/create_ticket.py --input .tmp/classified.json
    # tickets land in output/tickets.json (default) and approval_queue.json
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, error, warn
from shared.sandbox import validate_write_path


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_STORE = PROJECT_ROOT / "output" / "tickets.json"
APPROVAL_QUEUE_PATH = PROJECT_ROOT / "output" / "approval_queue.json"


def ticket_id(seed: int = 0) -> str:
    """Create a unique ticket ID."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    suffix = f"{random.randint(1000, 9999)}"
    return f"TICKET-{ts}-{suffix}"


def load_json_store(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        warn(f"Corrupt JSON at {path} — starting fresh")
        return []


def save_json_store(path: Path, records: list):
    validated = validate_write_path(str(path))
    validated.parent.mkdir(parents=True, exist_ok=True)
    validated.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def push_to_airtable(ticket: dict) -> dict | None:
    """Best-effort Airtable insert. Returns created record or None if not configured / failed."""
    api_key = get_optional("AIRTABLE_API_KEY")
    base_id = get_optional("AIRTABLE_BASE_ID")
    table = get_optional("AIRTABLE_TABLE_NAME", "Tickets")
    if not (api_key and base_id):
        return None
    try:
        import requests
    except ImportError:
        warn("requests not installed — skipping Airtable")
        return None

    fields = {
        "ticket_id": ticket["ticket_id"],
        "from_email": ticket.get("from_email", ""),
        "subject": ticket.get("subject", ""),
        "intent": ticket.get("intent", ""),
        "priority": ticket.get("priority", ""),
        "team": ticket.get("team", ""),
        "status": ticket.get("status", "awaiting-approval"),
        "body_excerpt": (ticket.get("body") or "")[:500],
    }
    try:
        resp = requests.post(
            f"https://api.airtable.com/v0/{base_id}/{table}",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"fields": fields},
            timeout=15,
        )
        if resp.ok:
            info(f"Airtable record created for {ticket['ticket_id']}")
            return resp.json()
        warn(f"Airtable insert failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        warn(f"Airtable error: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(description="Create tickets from classified emails")
    parser.add_argument("--input", default=".tmp/classified.json")
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Local ticket JSON store")
    args = parser.parse_args()

    load_env()

    in_path = PROJECT_ROOT / args.input
    if not in_path.exists():
        error(f"Classified input not found: {in_path}")
        sys.exit(1)

    classified = json.loads(in_path.read_text())

    store_path = Path(args.store)
    if not store_path.is_absolute():
        store_path = PROJECT_ROOT / args.store

    tickets = load_json_store(store_path)
    existing_ids = {t["email_id"] for t in tickets}

    approval_queue = load_json_store(APPROVAL_QUEUE_PATH)

    created = []
    for i, item in enumerate(classified):
        email_id = item.get("id")
        if email_id and email_id in existing_ids:
            continue  # idempotent: skip duplicates

        tid = ticket_id(i)
        now = datetime.now(timezone.utc).isoformat()
        status = "awaiting-approval" if item.get("intent") != "spam" else "spam"
        ticket = {
            "ticket_id": tid,
            "email_id": email_id,
            "from": item.get("from", ""),
            "from_email": item.get("from_email", ""),
            "from_name": item.get("from_name", ""),
            "subject": item.get("subject", ""),
            "body": item.get("body", ""),
            "body_excerpt": (item.get("body") or "")[:500],
            "received_at": item.get("received_at", now),
            "intent": item.get("intent"),
            "priority": item.get("priority"),
            "sentiment": item.get("sentiment"),
            "team": item.get("team"),
            "classification_method": item.get("method", "unknown"),
            "classification_reasoning": item.get("reasoning", ""),
            "status": status,
            "draft": None,
            "guardrail_flags": [],
            "edits": [],
            "created_at": now,
            "updated_at": now,
            "in_reply_to": item.get("in_reply_to", ""),
            "references": item.get("references", ""),
        }

        tickets.append(ticket)
        if status == "awaiting-approval":
            approval_queue.append({
                "ticket_id": tid,
                "priority": ticket["priority"],
                "team": ticket["team"],
                "from_email": ticket["from_email"],
                "subject": ticket["subject"],
                "queued_at": now,
            })
        created.append(ticket)
        push_to_airtable(ticket)

    save_json_store(store_path, tickets)
    save_json_store(APPROVAL_QUEUE_PATH, approval_queue)

    info(f"Created {len(created)} tickets (store: {store_path})")
    print(json.dumps({
        "status": "success",
        "created": len(created),
        "total_tickets": len(tickets),
        "queue_size": len(approval_queue),
        "store": str(store_path),
    }))


if __name__ == "__main__":
    main()
