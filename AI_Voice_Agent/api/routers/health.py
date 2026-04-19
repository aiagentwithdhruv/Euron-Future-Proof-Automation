"""Health + readiness probe. No auth — intentionally public."""

from __future__ import annotations

from fastapi import APIRouter

from api.config import get_settings
from api.models import HealthResponse


router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
async def healthz() -> HealthResponse:
    s = get_settings()
    checks = {
        "api_key_configured": bool(s.api_key),
        "vapi_configured": bool(s.vapi_api_key and s.vapi_assistant_id),
        "calendar_configured": bool(s.google_calendar_id and s.google_service_account_json),
        "supabase_configured": bool(s.supabase_url and s.supabase_service_key),
        "euri_configured": bool(s.euri_api_key),
        "twilio_configured": bool(s.twilio_account_sid and s.twilio_auth_token and s.twilio_from),
        "resend_configured": bool(s.resend_api_key and s.email_from),
    }
    status = "ok" if checks["api_key_configured"] else "degraded"
    return HealthResponse(status=status, checks=checks)
