"""Orders module — request_review.

Triggered on order.fulfilled (delivered webhook is rare; we settle for
'fulfilled' + REVIEW_REQUEST_DELAY_DAYS days of backing-off in the scheduler).

For the build contract this module is fully synchronous: when it's invoked
with a fulfilled event we immediately log that a review request is DUE on
`delivered_at + REVIEW_REQUEST_DELAY_DAYS`. The actual send can be driven
either by:

  (a) a cron / n8n job that re-reads the Airtable 'review_due_at' column, or
  (b) this module invoked with `--send-pending` (see CLI).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools.airtable_client import AirtableStore, table_name
from tools.config import module_config
from tools.senders import send_email

logger = get_logger(__name__)


def _iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat()


def schedule(event: dict) -> dict:
    order = event.get("order") or {}
    if not order:
        return {"status": "skipped", "reason": "no_order"}
    if not order.get("email"):
        return {"status": "skipped", "reason": "no_email"}

    cfg = module_config()
    due_at = datetime.now(timezone.utc) + timedelta(days=cfg.review_request_delay_days)
    AirtableStore().create(
        table_name("orders"),
        {
            "OrderID": order.get("order_id"),
            "Stage": "review_scheduled",
            "ReviewDueAt": _iso(due_at),
            "Email": order.get("email"),
            "Customer": order.get("customer_name"),
        },
    )
    return {"status": "scheduled", "review_due_at": _iso(due_at)}


def send_one(order_row: dict, *, dry_run: bool = False) -> dict:
    name = (order_row.get("Customer") or "there").split()[0]
    order_name = order_row.get("OrderName") or order_row.get("OrderID")
    subject = f"How did we do on {order_name}?"
    body = (
        f"Hi {name},\n\n"
        f"We hope you're enjoying what you ordered. If you've got a minute, a short review "
        f"helps other shoppers decide — and genuinely helps us improve.\n\n"
        f"If anything's off, just reply to this email and a human will fix it.\n\n"
        f"Thanks for your support."
    )
    return send_email(to=order_row["Email"], subject=subject, body=body, dry_run=dry_run)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Request-review scheduler + one-off sender")
    parser.add_argument("--event", help="Schedule a review from an order event JSON")
    parser.add_argument("--send-test", help="Send a review test email to this address")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.send_test:
        row = {"OrderID": "TEST", "OrderName": "#TEST", "Customer": "Test User", "Email": args.send_test}
        print(json.dumps(send_one(row, dry_run=args.dry_run), default=str, indent=2))
        return 0

    if args.event:
        event = json.loads(Path(args.event).read_text())
        print(json.dumps(schedule(event), default=str, indent=2))
        return 0

    parser.error("Use --event or --send-test")
    return 2


if __name__ == "__main__":
    sys.exit(_cli())
