"""Smoke test — boots the app with a fake API_KEY, exercises every route.

Does NOT hit external services. Just verifies the contract:
  - /healthz is public and reports service availability
  - tool endpoints require X-Api-Key
  - tool endpoints accept both direct JSON and Vapi envelope
  - webhook accepts Vapi call.ended payload and returns 200 fast
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path and set minimal env BEFORE importing the app
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("API_KEY", "smoke-key")
os.environ.setdefault("BUSINESS_NAME", "Smoke Test Biz")
# Intentionally leave Google/Supabase/Twilio/Resend unset — services should degrade gracefully.

from fastapi.testclient import TestClient  # noqa: E402

# Reset the cached settings if the module was already imported in another session
from api import config  # noqa: E402
config.get_settings.cache_clear()

from api.main import app  # noqa: E402


client = TestClient(app)
HEADERS = {"X-Api-Key": "smoke-key"}
BAD = {"X-Api-Key": "wrong"}


def assert_status(actual: int, expected: int, ctx: str) -> None:
    if actual != expected:
        raise AssertionError(f"{ctx}: expected {expected}, got {actual}")


def test_health_public() -> None:
    r = client.get("/healthz")
    assert_status(r.status_code, 200, "healthz")
    body = r.json()
    assert body["service"] == "AI_Voice_Agent", body
    assert body["checks"]["api_key_configured"] is True, body
    print("  healthz:", body["status"], body["checks"])


def test_auth_required() -> None:
    r = client.post("/tool/lookup_customer", json={"phone": "+15551234567"})
    assert_status(r.status_code, 401, "no-auth lookup")
    r2 = client.post("/tool/lookup_customer", json={"phone": "+15551234567"}, headers=BAD)
    assert_status(r2.status_code, 401, "bad-auth lookup")
    print("  auth gate: 401 on no-key AND bad-key")


def test_check_availability_direct_body() -> None:
    r = client.post(
        "/tool/check_availability",
        json={"service_type": "cleaning", "date_preference": "next week", "duration_minutes": 30, "count": 3},
        headers=HEADERS,
    )
    assert_status(r.status_code, 200, "check_availability direct")
    body = r.json()
    assert body["status"] in ("ok", "unavailable"), body
    assert body["status"] == "unavailable", "Google Calendar not configured — must degrade"
    print("  check_availability (direct):", body["status"], "-", body.get("message", "")[:60])


def test_check_availability_vapi_envelope() -> None:
    envelope = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "check_availability",
                        "arguments": json.dumps({"date_preference": "tomorrow"}),
                    },
                }
            ],
        }
    }
    r = client.post("/tool/check_availability", json=envelope, headers=HEADERS)
    assert_status(r.status_code, 200, "check_availability vapi envelope")
    body = r.json()
    assert "results" in body and body["results"][0]["toolCallId"] == "call_abc123", body
    print("  check_availability (vapi envelope): ok, wrapped in results[]")


def test_escalate_no_human_number() -> None:
    envelope = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_escalate",
                    "type": "function",
                    "function": {
                        "name": "escalate_to_human",
                        "arguments": json.dumps({"call_id": "c1", "reason": "asked for human", "priority": "high"}),
                    },
                }
            ],
        }
    }
    r = client.post("/tool/escalate_to_human", json=envelope, headers=HEADERS)
    assert_status(r.status_code, 200, "escalate")
    body = r.json()["results"][0]["result"]
    assert body["status"] == "no_human_available", body
    print("  escalate_to_human (no HUMAN_HANDOFF_NUMBER): status=no_human_available -> offer callback")


def test_capture_lead_no_crm() -> None:
    r = client.post(
        "/tool/capture_lead",
        json={"phone": "+15551234567", "name": "Smoke Tester", "reason": "testing"},
        headers=HEADERS,
    )
    assert_status(r.status_code, 200, "capture_lead")
    body = r.json()
    assert body["status"] == "error" and "Supabase" in body["message"], body
    print("  capture_lead (no CRM): degrades with explicit error message")


def test_send_confirmation_no_providers() -> None:
    r = client.post(
        "/tool/send_confirmation",
        json={"customer_phone": "+15551234567", "customer_email": "x@y.com", "summary": "test"},
        headers=HEADERS,
    )
    assert_status(r.status_code, 200, "send_confirmation")
    body = r.json()
    assert body["sms"]["status"] == "not_configured", body
    assert body["email"]["status"] == "not_configured", body
    print("  send_confirmation (no Twilio/Resend): both channels report not_configured cleanly")


def test_webhook_call_ended() -> None:
    payload = {
        "message": {
            "type": "end-of-call-report",
            "call": {"id": "call_xyz", "customer": {"number": "+15551234567"}, "type": "inbound"},
            "artifact": {"transcript": "Hi, I want to book for next week."},
            "durationSeconds": 42.5,
        }
    }
    r = client.post("/webhook/call_ended", json=payload, headers=HEADERS)
    assert_status(r.status_code, 200, "webhook call_ended")
    body = r.json()
    assert body["status"] == "accepted" and body["call_id"] == "call_xyz", body
    print("  webhook call_ended: accepted=True, call_id=call_xyz (background task dispatched)")


def test_webhook_status_lenient() -> None:
    r = client.post("/webhook/status", json={"message": {"call": {"id": "c2"}}}, headers=HEADERS)
    assert_status(r.status_code, 200, "webhook status")
    print("  webhook status: 200 (never blocks Vapi)")


if __name__ == "__main__":
    print("== AI Voice Agent smoke test ==")
    for fn in [
        test_health_public,
        test_auth_required,
        test_check_availability_direct_body,
        test_check_availability_vapi_envelope,
        test_escalate_no_human_number,
        test_capture_lead_no_crm,
        test_send_confirmation_no_providers,
        test_webhook_call_ended,
        test_webhook_status_lenient,
    ]:
        print(f"- {fn.__name__}")
        fn()
    print("== ALL PASS ==")
