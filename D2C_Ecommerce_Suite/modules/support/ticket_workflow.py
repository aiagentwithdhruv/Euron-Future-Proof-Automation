"""Support module — ticket_workflow.

Full lifecycle for a single inbound support email:

    classify -> create ticket row -> draft reply (with RAG + guardrails) ->
    push to approval queue -> on approval, send reply via Resend.

This module owns the orchestration. Classifier + drafter are side modules.

Invocation modes:
  - Library: `run_inbound({subject, body, from_email, ...})`
  - CLI:    `python modules/support/ticket_workflow.py --inbound path.json`
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from modules.support import classify_email, draft_reply
from tools.airtable_client import AirtableStore, table_name
from tools.senders import send_email, send_slack
from tools._bootstrap import tmp_dir

logger = get_logger(__name__)


def run_inbound(inbound: dict, *, dry_run: bool = True) -> dict:
    subject = inbound.get("subject") or "(no subject)"
    body = inbound.get("body") or ""
    from_email = inbound.get("from_email")
    if not from_email:
        return {"status": "rejected", "reason": "missing_from_email"}

    ticket_id = inbound.get("ticket_id") or f"T{int(datetime.now(timezone.utc).timestamp())}"

    classification = classify_email.classify(subject, body)
    draft_payload = draft_reply.draft(subject=subject, body=body, classification=classification)
    draft_reply.persist(ticket_id, {"ticket_id": ticket_id, "to": from_email, **draft_payload})

    # Record the ticket + push to approval queue (a file-backed queue).
    AirtableStore().create(
        table_name("tickets"),
        {
            "TicketID": ticket_id,
            "From": from_email,
            "Subject": subject,
            "Intent": classification["intent"],
            "Priority": classification["priority"],
            "Sentiment": classification["sentiment"],
            "Team": classification["team"],
            "Status": "awaiting_approval",
        },
    )

    queue_path = tmp_dir() / "approval_queue.jsonl"
    with queue_path.open("a") as f:
        f.write(
            json.dumps(
                {
                    "ticket_id": ticket_id,
                    "to": from_email,
                    "subject": draft_payload["subject"],
                    "priority": classification["priority"],
                    "team": classification["team"],
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    # Let the team know.
    alert = (
        f":ticket: *{classification['priority']}* ticket for `{classification['team']}` — "
        f"`{ticket_id}` ({classification['intent']}/{classification['sentiment']}). "
        f"Draft ready for approval."
    )
    send_slack(message=alert, dry_run=dry_run)

    return {
        "status": "queued_for_approval",
        "ticket_id": ticket_id,
        "classification": classification,
        "draft_path": str((tmp_dir() / "tickets" / f"{ticket_id}.draft.json").relative_to(tmp_dir().parent)),
    }


def approve_and_send(ticket_id: str, *, edits: dict | None = None, dry_run: bool = True) -> dict:
    draft_path = tmp_dir() / "tickets" / f"{ticket_id}.draft.json"
    if not draft_path.exists():
        return {"status": "error", "reason": "draft_not_found"}

    draft = json.loads(draft_path.read_text())
    subject = (edits or {}).get("subject") or draft["subject"]
    body = (edits or {}).get("body") or draft["body"]

    receipt = send_email(to=draft["to"], subject=subject, body=body, dry_run=dry_run)

    AirtableStore().update(
        table_name("tickets"),
        record_id="",  # local sink path — record id lookup would require a query we skip in MVP
        fields={"TicketID": ticket_id, "Status": "sent"},
    )

    # Keep original draft + edits for later prompt tuning.
    if edits:
        (tmp_dir() / "tickets" / f"{ticket_id}.edits.json").write_text(
            json.dumps({"original": draft, "edits": edits}, indent=2, ensure_ascii=False)
        )

    return {"status": "sent", "ticket_id": ticket_id, "receipt": receipt}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Support ticket workflow")
    sub = parser.add_subparsers(dest="cmd", required=True)

    inbound = sub.add_parser("inbound", help="Process a new inbound email")
    inbound.add_argument("--file", required=True, help="Path to inbound JSON")
    inbound.add_argument("--dry-run", action="store_true")

    approve = sub.add_parser("approve", help="Approve and send a drafted reply")
    approve.add_argument("--ticket-id", required=True)
    approve.add_argument("--edits-file", help="Optional JSON file with edits {subject, body}")
    approve.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.cmd == "inbound":
        payload = json.loads(Path(args.file).read_text())
        print(json.dumps(run_inbound(payload, dry_run=args.dry_run), indent=2, default=str))
    elif args.cmd == "approve":
        edits = json.loads(Path(args.edits_file).read_text()) if args.edits_file else None
        print(json.dumps(approve_and_send(args.ticket_id, edits=edits, dry_run=args.dry_run), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
