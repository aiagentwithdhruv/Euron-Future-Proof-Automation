"""Vapi lifecycle webhooks — `/webhook/call_ended` is the critical one."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from api.auth import require_api_key
from api.logging_utils import get_logger
from api.services.call_log_service import CallLogService


logger = get_logger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"], dependencies=[Depends(require_api_key)])


@router.post("/call_ended")
async def call_ended(request: Request, background: BackgroundTasks) -> dict[str, Any]:
    """Vapi fires this on hang-up. Return 200 FAST; do summary in background."""
    raw = await request.json()
    msg = (raw or {}).get("message") or raw or {}
    call = msg.get("call") or {}
    artifact = msg.get("artifact") or {}

    call_id = (
        call.get("id")
        or msg.get("callId")
        or raw.get("callId")
        or raw.get("id")
        or "unknown"
    )
    direction = (call.get("type") or msg.get("type") or "inbound").split(".")[0]
    caller_phone = (
        (call.get("customer") or {}).get("number")
        or msg.get("callerPhone")
    )
    transcript = (
        artifact.get("transcript")
        or msg.get("transcript")
        or ""
    )
    duration_s = float(msg.get("durationSeconds") or call.get("durationSeconds") or 0)
    recording_url = artifact.get("recordingUrl") or msg.get("recordingUrl")

    logger.info(
        "webhook.call_ended",
        extra={"call_id": call_id, "duration_ms": int(duration_s * 1000)},
    )

    background.add_task(
        _finalize_async,
        call_id=call_id,
        direction=direction,
        caller_phone=caller_phone,
        transcript=transcript,
        duration_s=duration_s,
        recording_url=recording_url,
        raw_payload=raw,
    )
    return {"status": "accepted", "call_id": call_id}


def _finalize_async(
    *,
    call_id: str,
    direction: str,
    caller_phone: str | None,
    transcript: str,
    duration_s: float,
    recording_url: str | None,
    raw_payload: dict[str, Any] | None,
) -> None:
    try:
        CallLogService().finalize(
            call_id=call_id,
            direction=direction,
            caller_phone=caller_phone,
            transcript=transcript,
            duration_s=duration_s,
            recording_url=recording_url,
            raw_payload=raw_payload,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception(f"finalize_async.failed call_id={call_id}: {e}")


@router.post("/status")
async def call_status(request: Request) -> dict[str, Any]:
    """Optional: log mid-call status updates. Always returns 200 to avoid blocking Vapi."""
    try:
        raw = await request.json()
        msg = (raw or {}).get("message") or {}
        logger.info("webhook.status", extra={"call_id": (msg.get("call") or {}).get("id")})
    except Exception:  # noqa: BLE001
        pass
    return {"status": "ok"}
