"""Cart recovery handler — called by the webhook dispatcher.

cart.* events record the candidate. order.* events (via this module, via
`track_recovery.attribute`) attribute recovered revenue — but the dispatcher
already hands order events to the orders module, so this handler stays
focused on carts only.
"""

from __future__ import annotations

from modules.cart_recovery import detect_abandoned


def handle(event: dict) -> dict:
    topic = event.get("topic", "")
    if topic in ("cart.created", "cart.abandoned_candidate"):
        return detect_abandoned.record_candidate(event)
    return {"status": "noop", "topic": topic}
