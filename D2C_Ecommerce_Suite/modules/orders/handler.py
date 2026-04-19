"""Orders handler — invoked by the webhook dispatcher.

Maps normalised topics to the right send/schedule function.
"""

from __future__ import annotations

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from modules.orders import request_review, send_confirmation, tracking_update

logger = get_logger(__name__)


def handle(event: dict) -> dict:
    topic = event.get("topic", "")
    dry_run = False

    if topic in ("order.created", "order.paid"):
        return send_confirmation.run(event, dry_run=dry_run)
    if topic in ("order.shipped", "order.shipping_updated", "order.fulfilled"):
        result = tracking_update.run(event, dry_run=dry_run)
        if topic in ("order.fulfilled",):
            result["review_schedule"] = request_review.schedule(event)
        return result
    if topic == "order.updated":
        # Generic updated — log only; specific transitions are handled above.
        return {"status": "noop", "topic": topic}
    return {"status": "noop", "topic": topic}
