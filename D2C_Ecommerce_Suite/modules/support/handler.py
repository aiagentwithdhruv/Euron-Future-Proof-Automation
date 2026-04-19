"""Support handler — not triggered by Shopify webhooks directly.

Shopify doesn't send 'support email received' events (that's email inbox,
handled via IMAP polling in AI_Support_Ticket_System). So this handler is
a thin shim: if/when a webhook does pass a support event in the future, it
routes here. For now it's a no-op placeholder that preserves the module
contract.
"""

from __future__ import annotations

from modules.support import ticket_workflow


def handle(event: dict) -> dict:
    payload = event.get("support") or {}
    if not payload.get("subject") or not payload.get("body") or not payload.get("from_email"):
        return {"status": "noop", "reason": "not_a_support_event"}
    return ticket_workflow.run_inbound(payload, dry_run=False)
