"""Tool endpoints Vapi calls via HTTP. Accepts either the Vapi tool-call envelope
or a direct JSON body (makes local curl testing straightforward)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from api.auth import require_api_key
from api.config import get_settings
from api.logging_utils import get_logger
from api.models import (
    BookAppointmentRequest,
    CaptureLeadRequest,
    CheckAvailabilityRequest,
    EscalateRequest,
    LookupCustomerRequest,
    SendConfirmationRequest,
    ToolResult,
    VapiToolResponse,
    parse_tool_arguments,
)
from api.services.calendar_service import CalendarError, CalendarService
from api.services.crm_service import CRMError, CRMService
from api.services.notifications import NotificationError, NotificationService


logger = get_logger(__name__)

router = APIRouter(prefix="/tool", tags=["tools"], dependencies=[Depends(require_api_key)])


# ---------- Adapter: accept Vapi envelope OR direct body ----------


async def _extract_args(request: Request, expected_tool: str) -> tuple[dict[str, Any], str | None]:
    """Return (args_dict, tool_call_id). tool_call_id is non-None if Vapi envelope."""
    raw = await request.json()
    if isinstance(raw, dict) and isinstance(raw.get("message"), dict):
        msg = raw["message"]
        tool_calls = msg.get("toolCalls") or []
        for tc in tool_calls:
            if (tc.get("function") or {}).get("name") == expected_tool:
                args = parse_tool_arguments((tc.get("function") or {}).get("arguments", ""))
                return args, tc.get("id")
        # Vapi envelope but tool name not matched; fall through to direct-body handling
    if isinstance(raw, dict):
        return raw, None
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")


def _wrap(tool_call_id: str | None, result: Any) -> Any:
    """Wrap a result in Vapi's response shape if this came via tool-call envelope."""
    if tool_call_id:
        return VapiToolResponse(results=[ToolResult(toolCallId=tool_call_id, result=result)])
    return result


# ---------- check_availability ----------


@router.post("/check_availability")
async def check_availability(request: Request) -> Any:
    args, tcid = await _extract_args(request, "check_availability")
    payload = CheckAvailabilityRequest(**args)
    cal = CalendarService()
    try:
        slots = cal.find_slots(
            date_preference=payload.date_preference,
            duration_minutes=payload.duration_minutes,
            count=payload.count,
        )
        result = {"status": "ok", "slots": slots}
    except CalendarError as e:
        logger.warning(f"check_availability.calendar_error: {e}")
        result = {"status": "unavailable", "message": str(e), "slots": []}
    return _wrap(tcid, result)


# ---------- book_appointment ----------


@router.post("/book_appointment")
async def book_appointment(request: Request) -> Any:
    args, tcid = await _extract_args(request, "book_appointment")
    payload = BookAppointmentRequest(**args)
    cal = CalendarService()
    s = get_settings()
    summary_line = f"{payload.service_type or 'Appointment'} — {payload.customer_name}"
    description = "\n".join(
        filter(None, [
            f"Customer: {payload.customer_name}",
            f"Phone: {payload.customer_phone}",
            f"Email: {payload.customer_email}" if payload.customer_email else "",
            f"Service: {payload.service_type}" if payload.service_type else "",
            f"Notes: {payload.notes}" if payload.notes else "",
            f"Booked via AI Voice Agent ({s.business_name}).",
        ])
    )
    try:
        event = cal.create_event(
            start_iso=payload.slot_start_iso,
            duration_minutes=payload.duration_minutes,
            summary=summary_line,
            description=description,
            attendee_email=payload.customer_email,
        )
        result = {
            "status": "ok",
            "booking_id": event.get("id"),
            "event_link": event.get("htmlLink"),
            "start": payload.slot_start_iso,
            "duration_minutes": payload.duration_minutes,
        }
        # Also persist the lead
        try:
            CRMService().upsert_lead({
                "phone": payload.customer_phone,
                "name": payload.customer_name,
                "email": payload.customer_email,
                "source": "inbound_voice",
                "outcome": "booked",
                "booking_ref": event.get("id"),
            })
        except CRMError as e:
            logger.warning(f"book.upsert_lead_failed: {e}")
    except CalendarError as e:
        logger.error(f"book.calendar_error: {e}")
        result = {"status": "error", "message": str(e)}
    return _wrap(tcid, result)


# ---------- capture_lead ----------


@router.post("/capture_lead")
async def capture_lead(request: Request) -> Any:
    args, tcid = await _extract_args(request, "capture_lead")
    payload = CaptureLeadRequest(**args)
    crm = CRMService()
    try:
        lead = crm.upsert_lead(payload.model_dump(exclude_none=True))
        result = {"status": "ok", "lead_id": (lead or {}).get("id"), "phone": payload.phone}
    except CRMError as e:
        logger.error(f"capture_lead.error: {e}")
        result = {"status": "error", "message": str(e)}
    return _wrap(tcid, result)


# ---------- lookup_customer ----------


@router.post("/lookup_customer")
async def lookup_customer(request: Request) -> Any:
    args, tcid = await _extract_args(request, "lookup_customer")
    payload = LookupCustomerRequest(**args)
    crm = CRMService()
    if crm.is_on_dnc(payload.phone):
        return _wrap(tcid, {"status": "dnc", "found": False, "message": "Phone is on DNC list"})
    try:
        record = crm.lookup_customer(payload.phone)
    except CRMError as e:
        logger.warning(f"lookup_customer.crm_error: {e}")
        return _wrap(tcid, {"status": "error", "found": False, "message": str(e)})
    if not record:
        return _wrap(tcid, {"status": "ok", "found": False})
    # Surface only the fields the assistant needs
    safe = {
        "status": "ok",
        "found": True,
        "name": record.get("name"),
        "email": record.get("email"),
        "last_service": record.get("last_service"),
        "last_booking_at": record.get("last_booking_at"),
        "notes": record.get("notes"),
    }
    return _wrap(tcid, safe)


# ---------- escalate_to_human ----------


@router.post("/escalate_to_human")
async def escalate_to_human(request: Request) -> Any:
    args, tcid = await _extract_args(request, "escalate_to_human")
    payload = EscalateRequest(**args)
    s = get_settings()
    # We acknowledge escalation immediately; the actual transfer is configured in the
    # voice platform (Vapi assistant's transferCall tool). This endpoint just logs the
    # reason + flags the call log so ops has a record.
    logger.info(
        "escalate.requested",
        extra={"call_id": payload.call_id, "reason": payload.reason},
    )
    try:
        crm = CRMService()
        if crm.enabled:
            crm.update_call_log(payload.call_id, {
                "escalated": True,
                "escalation_reason": payload.reason,
                "escalation_priority": payload.priority,
            })
    except CRMError as e:
        logger.warning(f"escalate.log_failed: {e}")
    result: dict[str, Any] = {
        "status": "ok",
        "transfer_to": s.human_handoff_number or "configured_in_voice_platform",
        "priority": payload.priority,
        "message": "Escalation acknowledged. Voice platform will execute the transfer.",
    }
    if not s.human_handoff_number:
        result["status"] = "no_human_available"
        result["message"] = "No human handoff number configured. Offer a callback instead."
    return _wrap(tcid, result)


# ---------- send_confirmation ----------


@router.post("/send_confirmation")
async def send_confirmation(request: Request) -> Any:
    args, tcid = await _extract_args(request, "send_confirmation")
    payload = SendConfirmationRequest(**args)
    s = get_settings()
    notif = NotificationService()
    sms_result: dict[str, Any] = {"status": "skipped"}
    email_result: dict[str, Any] = {"status": "skipped"}

    body = payload.summary or f"Your appointment with {s.business_name} is confirmed. Booking ref: {payload.booking_id or '(tbd)'}."

    if payload.customer_phone and notif.sms_enabled:
        try:
            r = notif.send_sms(payload.customer_phone, body)
            sms_result = {"status": "ok", **r}
        except NotificationError as e:
            logger.warning(f"confirmation.sms_failed: {e}")
            sms_result = {"status": "error", "message": str(e)}
    elif payload.customer_phone and not notif.sms_enabled:
        sms_result = {"status": "not_configured"}

    if payload.customer_email and notif.email_enabled:
        html = f"<p>Hi,</p><p>{body}</p><p>— {s.business_name}</p>"
        try:
            r = notif.send_email(payload.customer_email, f"Confirmation — {s.business_name}", html, text=body)
            email_result = {"status": "ok", **r}
        except NotificationError as e:
            logger.warning(f"confirmation.email_failed: {e}")
            email_result = {"status": "error", "message": str(e)}
    elif payload.customer_email and not notif.email_enabled:
        email_result = {"status": "not_configured"}

    status_overall = "ok" if "ok" in (sms_result.get("status"), email_result.get("status")) else "error"
    return _wrap(tcid, {"status": status_overall, "sms": sms_result, "email": email_result})


# ---------- Debug: direct tool-call envelope ----------


@router.post("/_vapi_envelope")
async def vapi_envelope_debug(body: dict[str, Any] = Body(...)) -> Any:
    """Accept a Vapi tool-calls envelope, route to the right handler by name.

    Handy when Vapi is configured to hit a single URL with the envelope. In that
    mode, the assistant sends tool_calls in a single payload; we dispatch them
    all and return a combined response.
    """
    msg = (body or {}).get("message") or {}
    tool_calls = msg.get("toolCalls") or []
    if not tool_calls:
        return {"results": []}

    results: list[dict[str, Any]] = []
    # Map tool names → coroutines. Reuse the individual handlers by calling their
    # logic. Simple approach: inline each.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Per-tool URLs are the recommended Vapi setup. Use /tool/<name> directly.",
    )
