"""Shopify + WooCommerce HMAC verification.

Shopify signs with HMAC-SHA256 + base64 of the raw request body, using the
webhook secret, and sends it in the `X-Shopify-Hmac-Sha256` header.

WooCommerce signs the raw body with HMAC-SHA256 + base64 using the webhook's
secret, sent in `X-WC-Webhook-Signature`.

Both comparisons MUST be constant-time (hmac.compare_digest) — string equality
leaks timing and is exploitable.
"""

from __future__ import annotations

import base64
import hashlib
import hmac


def compute_shopify_hmac(secret: str, raw_body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_shopify_hmac(secret: str, raw_body: bytes, header_hmac: str) -> bool:
    if not secret or not header_hmac:
        return False
    expected = compute_shopify_hmac(secret, raw_body)
    return hmac.compare_digest(expected, header_hmac.strip())


def verify_woocommerce_hmac(secret: str, raw_body: bytes, header_hmac: str) -> bool:
    # Woo uses the same algorithm (HMAC-SHA256, base64), different header.
    if not secret or not header_hmac:
        return False
    expected = compute_shopify_hmac(secret, raw_body)
    return hmac.compare_digest(expected, header_hmac.strip())
