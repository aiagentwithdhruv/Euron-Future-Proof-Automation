"""Reviews handler — invoked by the webhook dispatcher.

For the MVP, Shopify order webhooks are what schedule review asks (via
`modules/orders/request_review`). Third-party review platforms POST their
own webhooks at us via `/webhook/reviews` (not yet wired — stub here for
when it is).
"""

from __future__ import annotations

from modules.orders import request_review


def handle(event: dict) -> dict:
    topic = event.get("topic", "")
    if topic == "order.fulfilled":
        return request_review.schedule(event)
    return {"status": "noop", "topic": topic}
