"""Orders module — send_confirmation.

Given a normalised order event, compose + deliver an order confirmation via
email (and WhatsApp if phone present), then record the row in Airtable.

Runs in 2 modes:
 - as a library function (called by modules/orders/handler.py from webhook)
 - as a CLI (`python modules/orders/send_confirmation.py --event path.json`)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Script-run path setup: walk up until we find `tools/_bootstrap.py`.
_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools import llm
from tools.airtable_client import AirtableStore, table_name
from tools.senders import send_email, send_whatsapp

logger = get_logger(__name__)


def compose_confirmation(event: dict) -> dict:
    order = event.get("order") or {}
    name = order.get("customer_name") or "there"
    items = order.get("line_items") or []
    total = f"{order.get('total_price')} {order.get('currency') or ''}".strip()
    eta = "3-5 business days"

    try:
        vars_ = {
            "customer_name": name,
            "items": "\n".join(f"- {i.get('quantity')}x {i.get('title')}" for i in items),
            "total": total,
            "eta": eta,
            "order_name": order.get("order_name") or order.get("order_id"),
        }
        data = llm.generate_json("order_confirmation_v1", vars_, temperature=0.4, max_tokens=400)
        subject = data.get("subject") or f"Order confirmed — {order.get('order_name') or order.get('order_id')}"
        body = data.get("body") or ""
        whatsapp = data.get("whatsapp") or ""
    except (llm.LLMUnavailable, json.JSONDecodeError) as e:
        logger.info(f"order confirmation -> template fallback: {e}")
        subject = f"Order confirmed — {order.get('order_name') or order.get('order_id')}"
        line_list = "\n".join(f"  - {i.get('quantity')}x {i.get('title')}" for i in items) or "  - items on the way"
        body = (
            f"Hi {name.split()[0] if name != 'there' else 'there'},\n\n"
            f"Your order {order.get('order_name') or order.get('order_id')} is confirmed.\n\n"
            f"{line_list}\n\n"
            f"Total: {total}\n"
            f"Estimated delivery: {eta}.\n\n"
            f"We'll email you again the moment it ships.\n\n"
            f"Thank you!"
        )
        whatsapp = (
            f"Hey {name}! Your order {order.get('order_name') or order.get('order_id')} is confirmed. "
            f"ETA {eta}. We'll update you when it ships."
        )
    return {"subject": subject, "body": body, "whatsapp": whatsapp}


def run(event: dict, *, dry_run: bool = False) -> dict:
    order = event.get("order") or {}
    if not order:
        return {"status": "skipped", "reason": "no_order_payload"}
    if not order.get("email") and not order.get("phone"):
        return {"status": "skipped", "reason": "no_contact"}

    copy = compose_confirmation(event)
    result = {"status": "success", "order_id": order.get("order_id"), "channels": []}

    if order.get("email"):
        receipt = send_email(
            to=order["email"],
            subject=copy["subject"],
            body=copy["body"],
            dry_run=dry_run,
        )
        result["channels"].append(receipt)

    if order.get("phone"):
        try:
            receipt = send_whatsapp(to=order["phone"], message=copy["whatsapp"], dry_run=dry_run)
            result["channels"].append(receipt)
        except ValueError as e:
            # invalid phone — log but don't fail the order.
            logger.warning(f"whatsapp skipped: {e}")
            result["channels"].append({"status": "skipped", "channel": "whatsapp", "reason": str(e)})

    # Persist to Airtable / local sink.
    store = AirtableStore()
    store.create(
        table_name("orders"),
        {
            "OrderID": order.get("order_id"),
            "OrderName": order.get("order_name"),
            "Customer": order.get("customer_name"),
            "Email": order.get("email"),
            "Total": order.get("total_price"),
            "Currency": order.get("currency"),
            "Stage": "confirmed",
        },
    )
    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Send order confirmation for a saved event JSON")
    parser.add_argument("--event", required=True, help="Path to event JSON")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    event = json.loads(Path(args.event).read_text())
    result = run(event, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
