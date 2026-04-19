"""Pydantic schemas — request + response + Vapi tool-call adapter."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


# ---------- Tool inputs ----------


class CheckAvailabilityRequest(BaseModel):
    service_type: str | None = None
    date_preference: str | None = Field(
        default=None,
        description="Natural language or ISO date. Examples: 'next Tuesday', '2026-04-22'.",
    )
    duration_minutes: int = 30
    count: int = 3


class BookAppointmentRequest(BaseModel):
    slot_start_iso: str = Field(..., description="ISO-8601 start, e.g. 2026-04-22T15:00:00-07:00")
    duration_minutes: int = 30
    customer_name: str
    customer_phone: str
    customer_email: EmailStr | None = None
    service_type: str | None = None
    notes: str | None = None


class CaptureLeadRequest(BaseModel):
    name: str | None = None
    phone: str
    email: EmailStr | None = None
    reason: str | None = None
    notes: str | None = None
    source: str = "inbound_voice"
    outcome: str | None = None
    callback_requested: bool = False
    callback_at: str | None = None
    follow_up_on: str | None = None


class LookupCustomerRequest(BaseModel):
    phone: str


class EscalateRequest(BaseModel):
    call_id: str
    reason: str
    priority: Literal["low", "normal", "high"] = "normal"
    transcript_so_far: str | None = None


class SendConfirmationRequest(BaseModel):
    booking_id: str | None = None
    customer_phone: str | None = None
    customer_email: EmailStr | None = None
    summary: str | None = None


# ---------- Vapi tool-call adapter ----------


class VapiToolCallFunction(BaseModel):
    name: str
    arguments: str | dict[str, Any] = ""


class VapiToolCall(BaseModel):
    id: str
    type: str = "function"
    function: VapiToolCallFunction


class VapiMessage(BaseModel):
    type: str | None = None
    toolCalls: list[VapiToolCall] | None = None
    call: dict[str, Any] | None = None
    artifact: dict[str, Any] | None = None
    transcript: str | None = None
    summary: str | None = None
    endedReason: str | None = None
    durationSeconds: float | None = None
    recordingUrl: str | None = None


class VapiWebhook(BaseModel):
    message: VapiMessage


def parse_tool_arguments(raw: str | dict[str, Any]) -> dict[str, Any]:
    """Vapi sends arguments either stringified JSON or a dict; normalize to dict."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


# ---------- Responses ----------


class ToolResult(BaseModel):
    toolCallId: str
    result: Any


class VapiToolResponse(BaseModel):
    results: list[ToolResult]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str = "AI_Voice_Agent"
    version: str = "0.1.0"
    checks: dict[str, bool]
