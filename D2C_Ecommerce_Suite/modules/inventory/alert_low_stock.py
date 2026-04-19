"""Inventory module — alert_low_stock.

Given a low-stock list, send a single Slack + email alert to the ops team.
Alerts are de-duped on a per-run basis: we only alert when a variant's
count is *new* or *worse* than what we last alerted about. The baseline
is held in `.tmp/stock_state.json`.
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

from modules.inventory import check_stock_levels
from tools.airtable_client import AirtableStore, table_name
from tools.config import env, module_config
from tools._bootstrap import tmp_dir
from tools.senders import send_email, send_slack

logger = get_logger(__name__)

STATE = tmp_dir() / "stock_state.json"


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False, default=str))


def _should_alert(state: dict, variant_id: str, qty: int) -> bool:
    prev = state.get(variant_id)
    # Alert if: never alerted before, or qty has dropped further.
    return prev is None or int(qty) < int(prev.get("last_qty", qty + 1))


def run(*, dry_run: bool = False) -> dict:
    cfg = module_config()
    rows = check_stock_levels.poll()
    low = [r for r in rows if r["low"]]
    state = _load_state()

    new_alerts = []
    for r in low:
        vid = r["variant_id"]
        if _should_alert(state, vid, r["inventory_quantity"]):
            new_alerts.append(r)
            state[vid] = {"last_qty": r["inventory_quantity"], "last_alert_at": datetime.now(timezone.utc).isoformat()}

    _save_state(state)

    if not new_alerts:
        return {"status": "no_new_alerts", "low_count": len(low), "threshold": cfg.low_stock_threshold}

    # Compose a single digest Slack message + email.
    lines = [f"• *{r['product_title']}* ({r['sku'] or 'no-sku'}): {r['inventory_quantity']} left"
             for r in new_alerts]
    slack_msg = (
        f":package: *Low stock alert* — {len(new_alerts)} variant(s) at or below "
        f"threshold {cfg.low_stock_threshold}:\n" + "\n".join(lines)
    )

    result = {"status": "alerted", "count": len(new_alerts), "channels": []}
    result["channels"].append(send_slack(message=slack_msg, dry_run=dry_run))

    ops_email = env("OPS_EMAIL")
    if ops_email:
        body = (
            f"{len(new_alerts)} variant(s) have hit the low-stock threshold "
            f"({cfg.low_stock_threshold}).\n\n" + "\n".join(f"- {l[2:]}" for l in lines)
        )
        result["channels"].append(send_email(
            to=ops_email,
            subject=f"[ops] {len(new_alerts)} low-stock alert(s)",
            body=body,
            dry_run=dry_run,
        ))

    store = AirtableStore()
    for r in new_alerts:
        store.create(
            table_name("stock"),
            {
                "SKU": r["sku"],
                "ProductTitle": r["product_title"],
                "VariantID": r["variant_id"],
                "Qty": r["inventory_quantity"],
                "Status": "low_stock",
                "AlertedAt": datetime.now(timezone.utc).isoformat(),
            },
        )

    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Alert on low stock")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(dry_run=args.dry_run), indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
