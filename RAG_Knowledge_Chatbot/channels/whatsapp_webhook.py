"""
WhatsApp Cloud webhook — same brain, different I/O.
Mounts as a sub-app on the FastAPI server. Verifies Meta webhook handshake,
routes inbound text messages through tools.ask.ask(), replies via the Graph API,
and forwards low-confidence escalations with a polite hand-off message.

Wire it in api/main.py (optional):
    from channels.whatsapp_webhook import router as whatsapp_router
    app.include_router(whatsapp_router)
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException, Query, Request

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402
from tools.ask import ask  # noqa: E402

logger = get_logger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

_GRAPH = "https://graph.facebook.com/v20.0"


def _send_text(to: str, text: str) -> None:
    keys = config.require("WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID")
    url = f"{_GRAPH}/{keys['WHATSAPP_PHONE_NUMBER_ID']}/messages"
    headers = {
        "Authorization": f"Bearer {keys['WHATSAPP_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4000], "preview_url": False},
    }
    r = requests.post(url, headers=headers, json=body, timeout=15)
    if r.status_code >= 400:
        logger.error(f"whatsapp send failed {r.status_code}: {r.text[:200]}")


def _format_answer(result: dict) -> str:
    if result["status"] == "escalated":
        return (
            "I'll connect you with a human teammate — this needs a closer look. "
            "Someone will respond shortly."
        )
    cites = result.get("citations") or []
    sources = ", ".join(
        f"{c['source_id']}" + (f"#{c['section']}" if c.get("section") else "")
        for c in cites[:3]
    )
    return f"{result['answer']}\n\nSources: {sources}"


@router.get("")
def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification handshake."""
    expected = config.get("WHATSAPP_VERIFY_TOKEN")
    if hub_mode == "subscribe" and expected and hub_verify_token == expected:
        return int(hub_challenge) if hub_challenge and hub_challenge.isdigit() else hub_challenge
    raise HTTPException(status_code=403, detail="verification failed")


@router.post("")
async def inbound(request: Request) -> dict:
    payload = await request.json()
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []) or []:
                    if msg.get("type") != "text":
                        continue
                    from_num = msg["from"]
                    text = msg.get("text", {}).get("body", "").strip()
                    if not text:
                        continue
                    result = ask(text, channel="whatsapp")
                    _send_text(from_num, _format_answer(result))
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"whatsapp inbound error: {e}")
        # Return 200 so Meta doesn't retry storms; we logged it.
        return {"status": "error", "message": "handled"}
