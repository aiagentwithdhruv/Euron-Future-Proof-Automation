"""Inventory module — check_stock_levels.

Pulls stock from Shopify (primary) or Woo (fallback). Returns a list of
variants with `inventory_quantity` + `low = True` where below threshold.

Two ways to run:
  - Scheduled: `python modules/inventory/check_stock_levels.py --poll`
  - Event-driven: called from the webhook handler when Shopify sends
    `inventory_levels/update` — we cross-check only the affected product.
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

from tools.config import module_config
from tools.shopify_client import ShopifyClient, ShopifyNotConfigured
from tools.woo_client import WooClient, WooNotConfigured

logger = get_logger(__name__)


def _from_shopify(client: ShopifyClient, threshold: int) -> list[dict]:
    out = []
    for product in client.list_products(limit=100):
        for variant in product.get("variants") or []:
            qty = variant.get("inventory_quantity")
            if qty is None:
                continue
            out.append({
                "source": "shopify",
                "product_id": str(product.get("id")),
                "product_title": product.get("title"),
                "variant_id": str(variant.get("id")),
                "variant_title": variant.get("title"),
                "sku": variant.get("sku"),
                "inventory_quantity": int(qty),
                "low": int(qty) <= threshold,
            })
    return out


def _from_woo(client: WooClient, threshold: int) -> list[dict]:
    out = []
    for product in client.list_products(per_page=100):
        qty = product.get("stock_quantity")
        if qty is None:
            continue
        out.append({
            "source": "woocommerce",
            "product_id": str(product.get("id")),
            "product_title": product.get("name"),
            "variant_id": str(product.get("id")),
            "variant_title": None,
            "sku": product.get("sku"),
            "inventory_quantity": int(qty),
            "low": int(qty) <= threshold,
        })
    return out


def poll(*, threshold: int | None = None) -> list[dict]:
    cfg = module_config()
    limit = threshold if threshold is not None else cfg.low_stock_threshold

    shopify = ShopifyClient()
    if shopify.available:
        try:
            return _from_shopify(shopify, limit)
        except Exception as e:
            logger.warning(f"shopify stock poll failed: {e}")

    woo = WooClient()
    if woo.available:
        try:
            return _from_woo(woo, limit)
        except Exception as e:
            logger.warning(f"woo stock poll failed: {e}")

    logger.info("no platform configured — returning empty stock list")
    return []


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Poll inventory levels across platforms")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args()

    if args.poll:
        rows = poll(threshold=args.threshold)
        low = [r for r in rows if r["low"]]
        payload = {"total_variants": len(rows), "low_count": len(low), "low": low}
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return 0

    parser.error("Use --poll")
    return 2


if __name__ == "__main__":
    sys.exit(_cli())
