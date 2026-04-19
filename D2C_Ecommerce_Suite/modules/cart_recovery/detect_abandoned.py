"""Cart recovery — detect_abandoned.

Two inputs feed this module:
  (1) Webhook events with topic `cart.abandoned_candidate` (we receive these
      from `checkouts/update` on Shopify and record them). A cart is
      promoted to "abandoned" only if it remains untouched for at least
      ABANDONED_CART_DELAY_MIN minutes.
  (2) A scheduled run (cron / n8n) invokes this module with `--scan` to
      promote candidates to abandoned + schedule the 3-step recovery.

The cart store lives in Airtable (or local sink) as a `Carts` table with
columns: CartID, Email, TotalPrice, Currency, RecoveryStep, NextActionAt.

Never auto-charges. Only schedules discount-code emails.
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

from tools._bootstrap import tmp_dir
from tools.airtable_client import AirtableStore, table_name
from tools.config import module_config

logger = get_logger(__name__)

CART_STORE = tmp_dir() / "carts.json"


def _load_store() -> dict:
    if not CART_STORE.exists():
        return {"carts": {}}
    try:
        return json.loads(CART_STORE.read_text())
    except json.JSONDecodeError:
        return {"carts": {}}


def _save_store(store: dict) -> None:
    CART_STORE.write_text(json.dumps(store, indent=2, ensure_ascii=False, default=str))


def record_candidate(event: dict) -> dict:
    """Webhook entry point — records an abandoned-cart candidate."""
    cart = event.get("cart") or {}
    if not cart.get("cart_id") or not cart.get("email"):
        return {"status": "skipped", "reason": "no_cart_or_email"}

    store = _load_store()
    cart_id = cart["cart_id"]
    row = store["carts"].get(cart_id, {})
    row.update({
        "cart_id": cart_id,
        "email": cart.get("email"),
        "phone": cart.get("phone"),
        "customer_name": cart.get("customer_name"),
        "total_price": cart.get("total_price"),
        "currency": cart.get("currency"),
        "abandoned_checkout_url": cart.get("abandoned_checkout_url"),
        "line_items": cart.get("line_items"),
        "last_seen_at": event.get("occurred_at"),
        "recovery_step": row.get("recovery_step", 0),
        "status": row.get("status", "candidate"),
    })
    store["carts"][cart_id] = row
    _save_store(store)

    AirtableStore().create(
        table_name("carts"),
        {
            "CartID": cart_id,
            "Email": cart.get("email"),
            "TotalPrice": cart.get("total_price"),
            "Currency": cart.get("currency"),
            "Status": "candidate",
            "Stage": "observed",
        },
    )
    return {"status": "recorded", "cart_id": cart_id}


def promote(now: datetime | None = None) -> list[dict]:
    """Scheduled scan: promote candidates older than the delay into 'abandoned'
    and compute their next-step timestamp. Returns rows ready to send."""
    cfg = module_config()
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=cfg.abandoned_cart_delay_min)

    store = _load_store()
    ready = []
    for row in store["carts"].values():
        if row.get("status") == "completed":
            continue
        last_seen = _parse_iso(row.get("last_seen_at"))
        if not last_seen:
            continue

        step = row.get("recovery_step", 0)
        if step == 0 and last_seen <= cutoff:
            row["recovery_step"] = 1
            row["status"] = "abandoned"
            ready.append(row)
        elif step == 1 and last_seen + timedelta(hours=cfg.abandoned_cart_step2_hrs) <= now:
            row["recovery_step"] = 2
            ready.append(row)
        elif step == 2 and last_seen + timedelta(days=cfg.abandoned_cart_step3_days) <= now:
            row["recovery_step"] = 3
            ready.append(row)

    _save_store(store)
    return ready


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def mark_completed(cart_id: str) -> None:
    store = _load_store()
    if cart_id in store["carts"]:
        store["carts"][cart_id]["status"] = "completed"
        _save_store(store)


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Detect abandoned carts + promote to recovery")
    parser.add_argument("--scan", action="store_true", help="Scan + promote")
    parser.add_argument("--event-file", help="Record a candidate from event JSON")
    args = parser.parse_args()

    if args.event_file:
        event = json.loads(Path(args.event_file).read_text())
        print(json.dumps(record_candidate(event), indent=2, default=str))
    elif args.scan:
        ready = promote()
        print(json.dumps({"ready": ready, "count": len(ready)}, indent=2, default=str))
    else:
        parser.error("Use --scan or --event-file")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
