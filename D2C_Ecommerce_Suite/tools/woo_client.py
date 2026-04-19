"""WooCommerce REST API wrapper — minimal, mirrors the ShopifyClient surface.

WooCommerce uses Basic Auth with consumer_key + consumer_secret.
"""

from __future__ import annotations

from typing import Any, Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from tools.config import env

logger = get_logger(__name__)


class WooNotConfigured(RuntimeError):
    pass


class WooClient:
    def __init__(
        self,
        url: Optional[str] = None,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        api_version: str = "wc/v3",
    ):
        self.url = (url or env("WOO_URL") or "").rstrip("/")
        self.key = consumer_key or env("WOO_CONSUMER_KEY")
        self.secret = consumer_secret or env("WOO_CONSUMER_SECRET")
        self.api_version = api_version

    def _ensure(self) -> None:
        if not (self.url and self.key and self.secret):
            raise WooNotConfigured(
                "WooCommerce not configured. Set WOO_URL + WOO_CONSUMER_KEY + WOO_CONSUMER_SECRET."
            )

    @property
    def available(self) -> bool:
        return bool(self.url and self.key and self.secret)

    def _base(self) -> str:
        return f"{self.url}/wp-json/{self.api_version}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        self._ensure()
        import requests

        url = f"{self._base()}/{path.lstrip('/')}"
        resp = requests.request(method, url, auth=(self.key, self.secret), timeout=20, **kwargs)
        if resp.status_code >= 400:
            raise RuntimeError(f"Woo {method} {path} -> {resp.status_code}: {resp.text[:300]}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    def get_order(self, order_id: str) -> dict:
        return self._request("GET", f"orders/{order_id}")

    def list_products(self, per_page: int = 50) -> list[dict]:
        return self._request("GET", f"products?per_page={per_page}")

    def list_low_stock(self) -> list[dict]:
        """Woo exposes `stock_status=lowstock` via products filter."""
        return self._request("GET", "products?stock_status=lowstock&per_page=100")

    def create_coupon(self, code: str, amount: float, discount_type: str = "percent") -> dict:
        payload = {
            "code": code,
            "discount_type": discount_type,
            "amount": str(amount),
            "individual_use": True,
            "usage_limit": 1,
            "usage_limit_per_user": 1,
        }
        return self._request("POST", "coupons", json=payload)
