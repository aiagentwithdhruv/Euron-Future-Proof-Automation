"""Normalize raw platform webhook payloads into a small internal schema.

Input: platform (shopify|woocommerce) + topic + raw dict.
Output: a minimal `Event` dict that every module consumes:

    {
      "source":     "shopify" | "woocommerce",
      "topic":      "orders/create" | "carts/abandoned" | "products/update" | ...,
      "event_id":   "<X-Shopify-Webhook-Id or body-hash>",
      "occurred_at": ISO8601,
      "order":      {...normalised fields...}  (when applicable)
      "cart":       {...normalised fields...}  (when applicable)
      "product":    {...normalised fields...}  (when applicable)
      "raw":        <original payload kept for audit>
    }

The module handlers work off this shape, so swapping Shopify for Woo is a
change in one place (this file) — not everywhere.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


SHOPIFY_TOPIC_MAP = {
    "orders/create": "order.created",
    "orders/paid": "order.paid",
    "orders/fulfilled": "order.fulfilled",
    "orders/updated": "order.updated",
    "fulfillments/create": "order.shipped",
    "fulfillments/update": "order.shipping_updated",
    "checkouts/create": "cart.created",
    "checkouts/update": "cart.abandoned_candidate",
    "carts/create": "cart.created",
    "carts/update": "cart.abandoned_candidate",
    "products/update": "product.updated",
    "inventory_levels/update": "inventory.updated",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_order_shopify(raw: dict) -> dict:
    customer = raw.get("customer") or {}
    line_items = [
        {
            "title": li.get("title"),
            "quantity": li.get("quantity"),
            "price": li.get("price"),
            "sku": li.get("sku"),
            "variant_id": li.get("variant_id"),
        }
        for li in (raw.get("line_items") or [])
    ]
    return {
        "order_id": str(raw.get("id") or raw.get("name") or ""),
        "order_name": raw.get("name"),
        "email": (raw.get("email") or customer.get("email") or "").strip().lower() or None,
        "phone": raw.get("phone") or customer.get("phone"),
        "customer_name": _full_name(customer),
        "total_price": raw.get("total_price"),
        "currency": raw.get("currency"),
        "fulfillment_status": raw.get("fulfillment_status"),
        "financial_status": raw.get("financial_status"),
        "tracking_number": _first_tracking(raw),
        "tracking_url": _first_tracking_url(raw),
        "line_items": line_items,
        "abandoned_checkout_url": raw.get("abandoned_checkout_url"),
    }


def _normalize_cart_shopify(raw: dict) -> dict:
    customer = raw.get("customer") or {}
    line_items = [
        {
            "title": li.get("title"),
            "quantity": li.get("quantity"),
            "price": li.get("price"),
            "sku": li.get("sku"),
        }
        for li in (raw.get("line_items") or [])
    ]
    return {
        "cart_id": str(raw.get("id") or raw.get("token") or ""),
        "email": (raw.get("email") or customer.get("email") or "").strip().lower() or None,
        "phone": raw.get("phone") or customer.get("phone"),
        "customer_name": _full_name(customer),
        "total_price": raw.get("total_price") or raw.get("subtotal_price"),
        "currency": raw.get("currency") or raw.get("presentment_currency"),
        "abandoned_checkout_url": raw.get("abandoned_checkout_url"),
        "updated_at": raw.get("updated_at"),
        "line_items": line_items,
    }


def _normalize_product_shopify(raw: dict) -> dict:
    variants = [
        {
            "variant_id": v.get("id"),
            "sku": v.get("sku"),
            "inventory_quantity": v.get("inventory_quantity"),
            "title": v.get("title"),
            "price": v.get("price"),
        }
        for v in (raw.get("variants") or [])
    ]
    return {
        "product_id": str(raw.get("id") or ""),
        "title": raw.get("title"),
        "status": raw.get("status"),
        "variants": variants,
    }


def _normalize_woocommerce(topic: str, raw: dict) -> dict:
    # Woo's shape differs — this is a conservative mapping.
    if topic.startswith("order."):
        billing = raw.get("billing") or {}
        line_items = [
            {"title": li.get("name"), "quantity": li.get("quantity"), "price": li.get("price"), "sku": li.get("sku")}
            for li in (raw.get("line_items") or [])
        ]
        return {
            "order_id": str(raw.get("id") or ""),
            "order_name": f"#{raw.get('number', raw.get('id'))}",
            "email": (billing.get("email") or "").strip().lower() or None,
            "phone": billing.get("phone"),
            "customer_name": f"{billing.get('first_name','')} {billing.get('last_name','')}".strip() or None,
            "total_price": raw.get("total"),
            "currency": raw.get("currency"),
            "fulfillment_status": raw.get("status"),
            "financial_status": raw.get("status"),
            "line_items": line_items,
        }
    if topic.startswith("product."):
        return {
            "product_id": str(raw.get("id") or ""),
            "title": raw.get("name"),
            "status": raw.get("status"),
            "variants": [
                {
                    "variant_id": raw.get("id"),
                    "sku": raw.get("sku"),
                    "inventory_quantity": raw.get("stock_quantity"),
                    "title": raw.get("name"),
                    "price": raw.get("price"),
                }
            ],
        }
    return {}


def _full_name(customer: dict) -> Optional[str]:
    first = customer.get("first_name") or ""
    last = customer.get("last_name") or ""
    name = f"{first} {last}".strip()
    return name or None


def _first_tracking(raw: dict) -> Optional[str]:
    for f in raw.get("fulfillments") or []:
        if f.get("tracking_number"):
            return f.get("tracking_number")
    return raw.get("tracking_number")


def _first_tracking_url(raw: dict) -> Optional[str]:
    for f in raw.get("fulfillments") or []:
        if f.get("tracking_url"):
            return f.get("tracking_url")
    return raw.get("tracking_url")


def normalize(
    *,
    source: str,
    topic: str,
    raw: dict,
    event_id: str,
) -> dict:
    """Produce an Event dict from a raw webhook payload."""
    canonical_topic = SHOPIFY_TOPIC_MAP.get(topic, topic) if source == "shopify" else topic

    event: dict = {
        "source": source,
        "topic": canonical_topic,
        "platform_topic": topic,
        "event_id": event_id,
        "occurred_at": _iso_now(),
        "raw": raw,
    }

    if source == "shopify":
        if canonical_topic.startswith("order."):
            event["order"] = _normalize_order_shopify(raw)
        elif canonical_topic.startswith("cart."):
            event["cart"] = _normalize_cart_shopify(raw)
        elif canonical_topic.startswith("product.") or canonical_topic.startswith("inventory."):
            event["product"] = _normalize_product_shopify(raw)
    elif source == "woocommerce":
        norm = _normalize_woocommerce(canonical_topic, raw)
        if canonical_topic.startswith("order."):
            event["order"] = norm
        elif canonical_topic.startswith("product."):
            event["product"] = norm
    return event
