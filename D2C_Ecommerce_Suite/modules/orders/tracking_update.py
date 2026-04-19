"""Orders module — tracking_update.

Fires when a fulfillment is created or updated. Notifies the customer via
email + WhatsApp with the carrier tracking link.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools.airtable_client import AirtableStore, table_name
from tools.senders import send_email, send_whatsapp

logger = get_logger(__name__)


def run(event: dict, *, dry_run: bool = False) -> dict:
    order = event.get("order") or {}
    if not order:
        return {"status": "skipped", "reason": "no_order_payload"}

    tracking = order.get("tracking_number")
    url = order.get("tracking_url")
    if not (tracking or url):
        return {"status": "skipped", "reason": "no_tracking_info"}

    name = order.get("customer_name") or "there"
    first = name.split()[0] if name != "there" else "there"
    link_line = f"Track it here: {url}" if url else f"Tracking number: {tracking}"

    subject = f"Your order is on the way — {order.get('order_name') or order.get('order_id')}"
    body = (
        f"Hi {first},\n\n"
        f"Great news — your order has shipped.\n\n"
        f"{link_line}\n\n"
        f"You'll get another update once it lands.\n\n"
        f"Thanks!"
    )
    whatsapp = (
        f"Hey {first}! Your order {order.get('order_name') or order.get('order_id')} just shipped. "
        f"{link_line}"
    )

    result = {"status": "success", "order_id": order.get("order_id"), "channels": []}

    if order.get("email"):
        result["channels"].append(
            send_email(to=order["email"], subject=subject, body=body, dry_run=dry_run)
        )
    if order.get("phone"):
        try:
            result["channels"].append(
                send_whatsapp(to=order["phone"], message=whatsapp, dry_run=dry_run)
            )
        except ValueError as e:
            result["channels"].append({"status": "skipped", "channel": "whatsapp", "reason": str(e)})

    AirtableStore().create(
        table_name("orders"),
        {
            "OrderID": order.get("order_id"),
            "Stage": "shipped",
            "Tracking": tracking,
            "TrackingURL": url,
        },
    )
    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Send tracking update for a saved event JSON")
    parser.add_argument("--event", required=True, help="Path to event JSON")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    event = json.loads(Path(args.event).read_text())
    print(json.dumps(run(event, dry_run=args.dry_run), ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
