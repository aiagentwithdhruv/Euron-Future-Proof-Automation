"""Inventory module — suggest_reorder.

Analyses recent sales velocity and current stock to suggest a reorder
quantity. The model is simple and transparent:

    velocity_per_day = units_sold / window_days
    days_of_cover    = inventory_quantity / max(velocity_per_day, 0.1)
    suggested_qty    = ceil(velocity_per_day * target_cover_days)

LLM is used only for the human-facing reason (one sentence explaining the
suggestion). The NUMBERS stay deterministic — we never trust an LLM with
arithmetic that affects a purchase order.

CRITICAL: this module only SUGGESTS. It does not place POs. Auto-ordering
is off by design per Angelina's brief (alerts-only until she says otherwise).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools import llm

logger = get_logger(__name__)


def suggest(
    *,
    sku: str,
    product_title: str,
    last_30d_sales: int,
    current_stock: int,
    target_cover_days: int = 30,
    window_days: int = 30,
) -> dict:
    velocity = last_30d_sales / max(window_days, 1)
    days_cover = current_stock / max(velocity, 0.1)
    suggested = int(math.ceil(max(0.0, velocity * target_cover_days - current_stock)))

    reason = None
    try:
        data = llm.generate_json(
            "reorder_suggestion",
            {
                "sku": sku,
                "product_title": product_title,
                "last_30d_sales": last_30d_sales,
                "current_stock": current_stock,
                "velocity_per_day": round(velocity, 2),
                "days_of_cover": round(days_cover, 1),
                "suggested_qty": suggested,
                "target_cover_days": target_cover_days,
            },
            temperature=0.2,
            max_tokens=180,
        )
        reason = (data.get("reason") or "").strip() or None
    except (llm.LLMUnavailable, json.JSONDecodeError):
        reason = None

    if not reason:
        reason = (
            f"Velocity ~{velocity:.1f}/day gives ~{days_cover:.0f} days of cover at current stock; "
            f"reorder {suggested} to hit a {target_cover_days}-day cover target."
        )

    return {
        "sku": sku,
        "product_title": product_title,
        "velocity_per_day": round(velocity, 2),
        "days_of_cover": round(days_cover, 1),
        "suggested_qty": suggested,
        "reason": reason,
        "auto_order_enabled": False,  # invariant — never flip this without Angelina.
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Suggest a reorder quantity")
    parser.add_argument("--sku", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--last-30d-sales", type=int, required=True)
    parser.add_argument("--current-stock", type=int, required=True)
    parser.add_argument("--target-cover-days", type=int, default=30)
    args = parser.parse_args()
    result = suggest(
        sku=args.sku,
        product_title=args.title,
        last_30d_sales=args.last_30d_sales,
        current_stock=args.current_stock,
        target_cover_days=args.target_cover_days,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
