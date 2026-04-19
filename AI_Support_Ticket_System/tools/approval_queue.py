"""Operator CLI for the approval queue.

Usage:
    python tools/approval_queue.py --list
    python tools/approval_queue.py --show TICKET-...
    python tools/approval_queue.py --edit TICKET-... --text "Final reply body"
    python tools/approval_queue.py --approve TICKET-...          # runs guardrail, then send_reply
    python tools/approval_queue.py --reject TICKET-... --reason "spam"
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env
from shared.logger import info, warn, error

from tools.guardrail import check as guardrail_check


PROJECT_ROOT = Path(__file__).parent.parent
STORE_PATH = PROJECT_ROOT / "output" / "tickets.json"
QUEUE_PATH = PROJECT_ROOT / "output" / "approval_queue.json"
EDITS_PATH = PROJECT_ROOT / ".tmp" / "draft_edits.jsonl"


def _load_tickets() -> list:
    if not STORE_PATH.exists():
        return []
    return json.loads(STORE_PATH.read_text())


def _save_tickets(tickets: list):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(tickets, indent=2, ensure_ascii=False))


def _save_queue(tickets: list):
    queue = [
        {
            "ticket_id": t["ticket_id"],
            "priority": t.get("priority"),
            "team": t.get("team"),
            "from_email": t.get("from_email"),
            "subject": t.get("subject"),
            "queued_at": t.get("created_at"),
        }
        for t in tickets if t.get("status") == "awaiting-approval"
    ]
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False))


def cmd_list(tickets: list):
    pending = [t for t in tickets if t.get("status") == "awaiting-approval"]
    if not pending:
        print("(queue empty)")
        return
    print(f"\n{len(pending)} ticket(s) awaiting approval:\n")
    print(f"{'ID':<32} {'P':<4} {'INTENT':<10} {'TEAM':<14} {'FROM':<28} SUBJECT")
    print("-" * 110)
    for t in pending:
        print(f"{t['ticket_id']:<32} {t.get('priority','?'):<4} {t.get('intent','?'):<10} "
              f"{t.get('team','triage'):<14} {(t.get('from_email') or '')[:26]:<28} "
              f"{(t.get('subject') or '')[:40]}")
    print()


def cmd_show(tickets: list, ticket_id: str):
    t = next((x for x in tickets if x["ticket_id"] == ticket_id), None)
    if not t:
        error(f"Ticket not found: {ticket_id}")
        sys.exit(1)
    print("=" * 80)
    print(f"Ticket:     {t['ticket_id']}")
    print(f"Status:     {t.get('status')}")
    print(f"Priority:   {t.get('priority')}  Intent: {t.get('intent')}  Team: {t.get('team')}")
    print(f"Sentiment:  {t.get('sentiment')}")
    print(f"From:       {t.get('from')}")
    print(f"Subject:    {t.get('subject')}")
    print(f"Received:   {t.get('received_at')}")
    print(f"Method:     classify={t.get('classification_method')}  draft={t.get('draft_method')}")
    print(f"Reasoning:  {t.get('classification_reasoning')}")
    if t.get("guardrail_blocked"):
        print("Guardrail:  *** BLOCKED — draft replaced with safe fallback ***")
    if t.get("guardrail_flags"):
        print(f"Flags:      {len(t['guardrail_flags'])} raised")
        for f in t["guardrail_flags"][:10]:
            print(f"              - {f.get('layer')}: {f.get('issue')} ({f.get('action')})")
    print("-" * 80)
    print("Customer wrote:")
    print((t.get("body") or "")[:1200])
    print("-" * 80)
    print("DRAFT (safe, send-ready):")
    print(t.get("draft") or "(no draft)")
    if t.get("draft_raw") and t.get("guardrail_blocked"):
        print("-" * 80)
        print("Raw LLM draft (for your reference — NOT sent):")
        print(t.get("draft_raw"))
    if t.get("edits"):
        print("-" * 80)
        print(f"Edits: {len(t['edits'])}")
        for e in t["edits"]:
            print(f"  - {e['at']}: {e['new_text'][:80]}...")
    print("=" * 80)


def cmd_edit(tickets: list, ticket_id: str, new_text: str):
    t = next((x for x in tickets if x["ticket_id"] == ticket_id), None)
    if not t:
        error(f"Ticket not found: {ticket_id}")
        sys.exit(1)
    if t.get("status") not in ("awaiting-approval", "approved"):
        error(f"Can only edit awaiting-approval / approved tickets, not {t.get('status')}")
        sys.exit(2)

    guarded = guardrail_check(new_text, ticket_id=ticket_id)
    if guarded["blocked"]:
        warn(f"Edit blocked by guardrail — draft replaced with safe fallback")
        print(json.dumps({
            "status": "blocked",
            "reason": "guardrail",
            "flags": guarded["flags"],
            "safe_fallback": guarded["safe_text"],
        }, indent=2))
        return

    now = datetime.now(timezone.utc).isoformat()
    edit_record = {
        "at": now,
        "original_draft": t.get("draft"),
        "new_text": guarded["safe_text"],
        "flags": guarded["flags"],
    }
    t.setdefault("edits", []).append(edit_record)
    t["final_text"] = guarded["safe_text"]
    t["updated_at"] = now
    # Append to global edits log for future prompt tuning
    EDITS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EDITS_PATH, "a") as f:
        f.write(json.dumps({"ticket_id": ticket_id, **edit_record}) + "\n")

    _save_tickets(tickets)
    info(f"Edit saved for {ticket_id}")
    print(json.dumps({"status": "success", "ticket_id": ticket_id, "flags": guarded["flags"]}))


def cmd_approve(tickets: list, ticket_id: str, dry_run: bool):
    t = next((x for x in tickets if x["ticket_id"] == ticket_id), None)
    if not t:
        error(f"Ticket not found: {ticket_id}")
        sys.exit(1)
    if t.get("status") == "sent":
        info(f"{ticket_id} already sent — no-op")
        print(json.dumps({"status": "skipped", "reason": "already-sent"}))
        return
    if t.get("status") not in ("awaiting-approval", "approved"):
        error(f"Cannot approve from status '{t.get('status')}'")
        sys.exit(2)

    # Re-run guardrail on whatever will be sent (draft OR final_text)
    body = t.get("final_text") or t.get("draft") or ""
    guarded = guardrail_check(body, ticket_id=ticket_id)
    if guarded["blocked"]:
        error("Approval blocked — guardrail flagged the text. Edit before approving.")
        print(json.dumps({"status": "blocked", "reason": "guardrail", "flags": guarded["flags"]}, indent=2))
        sys.exit(3)

    now = datetime.now(timezone.utc).isoformat()
    t["status"] = "approved"
    t["approved_at"] = now
    t["final_text"] = guarded["safe_text"]
    t["updated_at"] = now
    _save_tickets(tickets)

    # Delegate send — separate tool, reuses Resend client
    cmd = [sys.executable, str(Path(__file__).parent / "send_reply.py"), "--ticket-id", ticket_id]
    if dry_run:
        cmd.append("--dry-run")
    info(f"Dispatching send_reply.py for {ticket_id} (dry_run={dry_run})")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error(f"send_reply.py failed: {result.stderr}")
        # Revert to awaiting-approval so operator can retry
        tickets = _load_tickets()
        t2 = next(x for x in tickets if x["ticket_id"] == ticket_id)
        t2["status"] = "awaiting-approval"
        t2["updated_at"] = datetime.now(timezone.utc).isoformat()
        _save_tickets(tickets)
        sys.exit(result.returncode)

    print(result.stdout.strip() or json.dumps({"status": "success", "ticket_id": ticket_id}))


def cmd_reject(tickets: list, ticket_id: str, reason: str):
    t = next((x for x in tickets if x["ticket_id"] == ticket_id), None)
    if not t:
        error(f"Ticket not found: {ticket_id}")
        sys.exit(1)
    now = datetime.now(timezone.utc).isoformat()
    t["status"] = "rejected"
    t["rejected_at"] = now
    t["reject_reason"] = reason
    t["updated_at"] = now
    _save_tickets(tickets)
    info(f"Rejected {ticket_id}: {reason}")
    print(json.dumps({"status": "success", "ticket_id": ticket_id, "new_status": "rejected"}))


def main():
    parser = argparse.ArgumentParser(description="Support ticket approval queue CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List pending tickets")
    group.add_argument("--show", metavar="TICKET_ID", help="Show full ticket")
    group.add_argument("--edit", metavar="TICKET_ID", help="Edit the draft")
    group.add_argument("--approve", metavar="TICKET_ID", help="Approve + send")
    group.add_argument("--reject", metavar="TICKET_ID", help="Reject / mark spam")
    parser.add_argument("--text", help="New draft text for --edit")
    parser.add_argument("--reason", help="Reason for --reject")
    parser.add_argument("--dry-run", action="store_true", help="Pass --dry-run to send_reply")
    args = parser.parse_args()

    load_env()
    tickets = _load_tickets()

    if args.list:
        cmd_list(tickets)
    elif args.show:
        cmd_show(tickets, args.show)
    elif args.edit:
        if not args.text:
            error("--edit requires --text")
            sys.exit(1)
        cmd_edit(tickets, args.edit, args.text)
    elif args.approve:
        cmd_approve(tickets, args.approve, args.dry_run)
    elif args.reject:
        cmd_reject(tickets, args.reject, args.reason or "unspecified")

    # Refresh queue snapshot
    _save_queue(_load_tickets())


if __name__ == "__main__":
    main()
