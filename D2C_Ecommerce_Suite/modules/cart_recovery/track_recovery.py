"""Cart recovery — track_recovery.

Attribution: when an order.created webhook comes in, we look up the order's
email against the abandoned-cart store. If we find a match whose last
recovery email went out in the past 72 hours, we mark that cart as
'recovered' and attribute the revenue.

This is intentionally simple — email-match + time window — so it works
across both Shopify and Woo without needing discount-code tracking (which
would require a Shopify-only API call per order).
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

from modules.cart_recovery import detect_abandoned
from tools.airtable_client import AirtableStore, table_name

logger = get_logger(__name__)


def match_order_to_cart(order: dict) -> dict | None:
    email = (order.get("email") or "").lower()
    if not email:
        return None

    store = detect_abandoned._load_store()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=72)
    best = None
    for row in store["carts"].values():
        if row.get("status") == "completed":
            continue
        if (row.get("email") or "").lower() != email:
            continue
        last_seen = detect_abandoned._parse_iso(row.get("last_seen_at"))
        if last_seen and last_seen >= cutoff:
            # Pick the most recently abandoned cart for this email.
            if not best or (detect_abandoned._parse_iso(best.get("last_seen_at")) or datetime.min.replace(tzinfo=timezone.utc)) < last_seen:
                best = row
    return best


def attribute(event: dict) -> dict:
    order = event.get("order") or {}
    if not order:
        return {"status": "skipped", "reason": "no_order"}

    matched = match_order_to_cart(order)
    if not matched:
        return {"status": "no_match", "email": order.get("email")}

    detect_abandoned.mark_completed(matched["cart_id"])
    AirtableStore().create(
        table_name("carts"),
        {
            "CartID": matched["cart_id"],
            "Status": "recovered",
            "RecoveredOrderID": order.get("order_id"),
            "Revenue": order.get("total_price"),
            "Currency": order.get("currency"),
        },
    )
    return {
        "status": "recovered",
        "cart_id": matched["cart_id"],
        "order_id": order.get("order_id"),
        "revenue": order.get("total_price"),
        "currency": order.get("currency"),
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Attribute an order to an abandoned cart")
    parser.add_argument("--event-file", required=True)
    args = parser.parse_args()
    event = json.loads(Path(args.event_file).read_text())
    print(json.dumps(attribute(event), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
