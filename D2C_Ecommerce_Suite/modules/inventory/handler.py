"""Inventory handler — routes product/inventory webhooks.

On `inventory.updated`, we delegate the decision to check_stock_levels
(which already knows how to read the platform) + alert_low_stock (which
handles dedupe). Kept deliberately thin — all state / logic lives inside
the module functions so the handler remains a switch-board.
"""

from __future__ import annotations

import tools._bootstrap  # noqa: F401

from modules.inventory import alert_low_stock


def handle(event: dict) -> dict:
    topic = event.get("topic", "")
    if topic in ("inventory.updated", "product.updated"):
        # Cheap pass: re-scan + alert on new low-stock variants.
        return alert_low_stock.run(dry_run=False)
    return {"status": "noop", "topic": topic}
