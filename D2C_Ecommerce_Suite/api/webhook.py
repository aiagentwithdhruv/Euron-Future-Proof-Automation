"""FastAPI webhook receiver for Shopify + WooCommerce.

Design invariants (from ATLAS-PROMPT + project CLAUDE.md):

1. HMAC verification runs BEFORE any parsing. Signature mismatch -> 401.
2. Every event is keyed via `X-Shopify-Webhook-Id` (or sha256(body) when the
   header is absent). Duplicates return 200 without re-running handlers —
   Shopify replays on network timeouts, so this is not optional.
3. We return 200 the moment verification + dedupe succeed. The handler runs
   inside FastAPI BackgroundTasks so the store never waits on our work.
4. Handlers NEVER auto-charge. Cart recovery is discount-only by design.

Run locally:

    uvicorn api.webhook:app --reload --port 8080

Expose via ngrok / cloudflared, register the URL in the Shopify admin for the
topics listed in `SHOPIFY_SUPPORTED_TOPICS`.
"""

from __future__ import annotations

import json
from typing import Optional

# Wire sys.path for `shared.*` before the rest of the imports.
import tools._bootstrap  # noqa: F401

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, status  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from shared.logger import get_logger  # noqa: E402

from tools import events as events_tool  # noqa: E402
from tools import idempotency  # noqa: E402
from tools.config import env, ensure_env  # noqa: E402
from tools.hmac_verify import verify_shopify_hmac, verify_woocommerce_hmac  # noqa: E402
from tools.run_logger import log_run  # noqa: E402

logger = get_logger(__name__)

ensure_env()

app = FastAPI(title="D2C E-Commerce Suite Webhook Receiver", version="0.1.0")

SHOPIFY_SUPPORTED_TOPICS = {
    "orders/create",
    "orders/paid",
    "orders/fulfilled",
    "orders/updated",
    "fulfillments/create",
    "fulfillments/update",
    "checkouts/create",
    "checkouts/update",
    "carts/create",
    "carts/update",
    "products/update",
    "inventory_levels/update",
}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "d2c-webhook"}


@app.post("/webhook/shopify")
async def shopify_webhook(request: Request, background: BackgroundTasks) -> JSONResponse:
    raw = await request.body()

    secret = env("SHOPIFY_WEBHOOK_SECRET", "")
    header_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    topic = request.headers.get("X-Shopify-Topic", "")
    shop = request.headers.get("X-Shopify-Shop-Domain", "")
    webhook_id = request.headers.get("X-Shopify-Webhook-Id", "")

    # 1. Security: HMAC check on raw body.
    if not secret:
        logger.error("SHOPIFY_WEBHOOK_SECRET missing — refusing to process webhook")
        raise HTTPException(status_code=500, detail="server_misconfigured")

    if not verify_shopify_hmac(secret, raw, header_hmac):
        logger.warning("shopify hmac mismatch", extra={"outputs": {"topic": topic, "shop": shop}})
        raise HTTPException(status_code=401, detail="hmac_mismatch")

    # 2. Topic allow-list.
    if topic and topic not in SHOPIFY_SUPPORTED_TOPICS:
        logger.info("shopify topic ignored", extra={"outputs": {"topic": topic}})
        return JSONResponse({"status": "ignored", "topic": topic}, status_code=status.HTTP_200_OK)

    # 3. Parse payload (body is already verified).
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid_json")

    # 4. Idempotency — Shopify retries on timeout.
    event_key = webhook_id or idempotency.body_hash(raw)
    if not idempotency.mark("shopify", event_key, topic=topic):
        logger.info("shopify duplicate event", extra={"outputs": {"event_key": event_key, "topic": topic}})
        return JSONResponse({"status": "duplicate", "event_key": event_key}, status_code=status.HTTP_200_OK)

    event = events_tool.normalize(source="shopify", topic=topic, raw=payload, event_id=event_key)
    log_run("webhook", "received", {"source": "shopify", "topic": event["topic"], "event_id": event_key, "shop": shop})

    # 5. Ack fast; process async.
    background.add_task(_dispatch_event, event)
    return JSONResponse({"status": "accepted", "topic": event["topic"], "event_id": event_key}, status_code=status.HTTP_200_OK)


@app.post("/webhook/woocommerce")
async def woocommerce_webhook(request: Request, background: BackgroundTasks) -> JSONResponse:
    raw = await request.body()

    secret = env("WOO_WEBHOOK_SECRET", "")
    header_hmac = request.headers.get("X-WC-Webhook-Signature", "")
    topic = request.headers.get("X-WC-Webhook-Topic", "")
    webhook_id = request.headers.get("X-WC-Webhook-Delivery-Id", "")

    if not secret:
        logger.error("WOO_WEBHOOK_SECRET missing")
        raise HTTPException(status_code=500, detail="server_misconfigured")

    if not verify_woocommerce_hmac(secret, raw, header_hmac):
        logger.warning("woo hmac mismatch", extra={"outputs": {"topic": topic}})
        raise HTTPException(status_code=401, detail="hmac_mismatch")

    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="invalid_json")

    event_key = webhook_id or idempotency.body_hash(raw)
    if not idempotency.mark("woocommerce", event_key, topic=topic):
        return JSONResponse({"status": "duplicate", "event_key": event_key}, status_code=status.HTTP_200_OK)

    # Woo's topics look like "order.created", "product.updated" — pass through.
    event = events_tool.normalize(source="woocommerce", topic=topic, raw=payload, event_id=event_key)
    log_run("webhook", "received", {"source": "woocommerce", "topic": event["topic"], "event_id": event_key})

    background.add_task(_dispatch_event, event)
    return JSONResponse({"status": "accepted", "topic": event["topic"], "event_id": event_key}, status_code=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _dispatch_event(event: dict) -> None:
    """Route a normalised event to the right module handler.

    Lives in a plain function (not async) so it runs in the BackgroundTasks
    thread pool without blocking the event loop. Each handler is wrapped in
    try/except so a failure in one module cannot poison others.
    """
    topic = event.get("topic", "")

    # Late imports: keep the webhook responsive and avoid circular modules.
    handlers = []
    if topic.startswith("order."):
        from modules.orders import handler as orders_handler

        handlers.append(("orders", orders_handler.handle))
        # Review ask fires off the fulfilled/paid event too.
        from modules.reviews import handler as reviews_handler

        handlers.append(("reviews", reviews_handler.handle))
    elif topic.startswith("cart."):
        from modules.cart_recovery import handler as cart_handler

        handlers.append(("cart_recovery", cart_handler.handle))
    elif topic.startswith("product.") or topic.startswith("inventory."):
        from modules.inventory import handler as inventory_handler

        handlers.append(("inventory", inventory_handler.handle))

    if not handlers:
        logger.info("no handler for topic", extra={"outputs": {"topic": topic}})
        return

    for name, fn in handlers:
        try:
            result = fn(event) or {}
            log_run(name, "handled", {"topic": topic, "event_id": event.get("event_id"), "result": result})
        except Exception as e:  # noqa: BLE001 — isolation on purpose
            logger.error(f"handler {name} failed: {e}")
            log_run(name, "error", {"topic": topic, "event_id": event.get("event_id"), "error": str(e)})
