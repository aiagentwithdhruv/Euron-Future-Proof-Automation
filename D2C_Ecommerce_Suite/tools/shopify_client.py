"""Shopify Admin REST API wrapper.

Scope: the narrow slice of Shopify the suite needs — discount codes (for cart
recovery), orders lookup (for shipping/review asks), inventory levels and
variants (for stock alerts). Anything broader should be added explicitly, not
discovered by reflection.

All methods are safe to call in offline/dev mode: if SHOPIFY_STORE_DOMAIN or
SHOPIFY_ACCESS_TOKEN is missing, they raise `ShopifyNotConfigured` so callers
can fall back deterministically.
"""

from __future__ import annotations

from typing import Any, Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from tools.config import env

logger = get_logger(__name__)


class ShopifyNotConfigured(RuntimeError):
    pass


class ShopifyClient:
    def __init__(
        self,
        store_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: str = "2025-01",
    ):
        self.store_domain = store_domain or env("SHOPIFY_STORE_DOMAIN")
        self.access_token = access_token or env("SHOPIFY_ACCESS_TOKEN")
        self.api_version = api_version

    def _ensure(self) -> None:
        if not (self.store_domain and self.access_token):
            raise ShopifyNotConfigured(
                "Shopify not configured. Set SHOPIFY_STORE_DOMAIN + SHOPIFY_ACCESS_TOKEN in .env."
            )

    @property
    def available(self) -> bool:
        return bool(self.store_domain and self.access_token)

    def _base(self) -> str:
        return f"https://{self.store_domain}/admin/api/{self.api_version}"

    def _headers(self) -> dict:
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Any:
        self._ensure()
        import requests

        url = f"{self._base()}/{path.lstrip('/')}"
        resp = requests.request(method, url, headers=self._headers(), timeout=20, **kwargs)
        if resp.status_code == 429:
            raise RuntimeError("Shopify rate-limited (429). Back off and retry.")
        if resp.status_code >= 400:
            raise RuntimeError(f"Shopify {method} {path} -> {resp.status_code}: {resp.text[:300]}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    # ----- orders ---------------------------------------------------------

    def get_order(self, order_id: str) -> dict:
        data = self._request("GET", f"orders/{order_id}.json")
        return data.get("order", {})

    # ----- inventory ------------------------------------------------------

    def list_products(self, limit: int = 50) -> list[dict]:
        data = self._request("GET", f"products.json?limit={limit}")
        return data.get("products", [])

    def list_inventory_levels(self, location_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        qs = f"limit={limit}"
        if location_id:
            qs += f"&location_ids={location_id}"
        data = self._request("GET", f"inventory_levels.json?{qs}")
        return data.get("inventory_levels", [])

    # ----- discount codes (cart recovery) ---------------------------------

    def create_price_rule(self, title: str, value_percentage: float, allocation: str = "across") -> dict:
        """Create a parent price rule. `value_percentage` is negative-expected
        (e.g. 10.0 means "-10%")."""
        payload = {
            "price_rule": {
                "title": title,
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": allocation,
                "value_type": "percentage",
                "value": f"-{abs(value_percentage)}",
                "customer_selection": "all",
                "once_per_customer": True,
                "usage_limit": 1,
                "starts_at": _iso_now(),
            }
        }
        data = self._request("POST", "price_rules.json", json=payload)
        return data.get("price_rule", {})

    def create_discount_code(self, price_rule_id: str, code: str) -> dict:
        payload = {"discount_code": {"code": code}}
        data = self._request("POST", f"price_rules/{price_rule_id}/discount_codes.json", json=payload)
        return data.get("discount_code", {})


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
