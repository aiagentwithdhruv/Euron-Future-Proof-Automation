"""Google Calendar — availability + booking via service account."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from api.config import get_settings
from api.logging_utils import get_logger


logger = get_logger(__name__)


class CalendarError(RuntimeError):
    pass


class CalendarService:
    """Thin wrapper over Google Calendar. Lazy imports so the app can boot without the SDK."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._service = None

    @property
    def enabled(self) -> bool:
        return bool(self._settings.google_calendar_id and self._settings.google_service_account_json)

    def _get_service(self):
        if self._service is not None:
            return self._service
        if not self.enabled:
            raise CalendarError("Google Calendar not configured (set GOOGLE_CALENDAR_ID + GOOGLE_SERVICE_ACCOUNT_JSON)")

        try:
            from google.oauth2 import service_account  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
        except ImportError as e:
            raise CalendarError(
                "Google Calendar SDK not installed. Add google-api-python-client + google-auth to requirements."
            ) from e

        raw = self._settings.google_service_account_json
        creds_data: dict[str, Any]
        # Accept either a path or a base64-encoded JSON blob or a raw JSON string
        if raw.startswith("{"):
            creds_data = json.loads(raw)
        elif raw.endswith(".json"):
            with open(raw) as fh:
                creds_data = json.load(fh)
        else:
            creds_data = json.loads(base64.b64decode(raw).decode("utf-8"))

        creds = service_account.Credentials.from_service_account_info(
            creds_data,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    # ---------- Availability ----------

    def find_slots(
        self,
        date_preference: str | None,
        duration_minutes: int,
        count: int,
        business_hours_start: int = 9,
        business_hours_end: int = 18,
    ) -> list[dict[str, Any]]:
        """Return up to `count` open slots matching the preference. Best-effort parsing of preference."""
        svc = self._get_service()
        tz = self._settings.business_timezone or "UTC"

        # Parse preference → time window
        start_window, end_window = self._window_from_preference(date_preference)

        events_result = svc.events().list(  # type: ignore[attr-defined]
            calendarId=self._settings.google_calendar_id,
            timeMin=start_window.isoformat(),
            timeMax=end_window.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
        ).execute()

        busy = [(self._parse(e["start"]), self._parse(e["end"])) for e in events_result.get("items", [])
                if "dateTime" in e.get("start", {}) and "dateTime" in e.get("end", {})]

        slots: list[dict[str, Any]] = []
        cursor = start_window
        step = timedelta(minutes=duration_minutes)
        while cursor + step <= end_window and len(slots) < count:
            slot_end = cursor + step
            hour = cursor.astimezone(timezone.utc).hour  # naive check in UTC; fine-tune with zoneinfo in prod
            if self._within_hours(cursor, business_hours_start, business_hours_end):
                if not self._overlaps(cursor, slot_end, busy):
                    slots.append({
                        "start": cursor.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_minutes": duration_minutes,
                        "timezone": tz,
                    })
            cursor += timedelta(minutes=30)
        return slots

    @staticmethod
    def _within_hours(dt: datetime, start_hour: int, end_hour: int) -> bool:
        return start_hour <= dt.hour < end_hour

    @staticmethod
    def _overlaps(start: datetime, end: datetime, busy: list[tuple[datetime, datetime]]) -> bool:
        for b_start, b_end in busy:
            if start < b_end and end > b_start:
                return True
        return False

    @staticmethod
    def _parse(obj: dict[str, Any]) -> datetime:
        val = obj.get("dateTime") or obj.get("date")
        if not val:
            raise CalendarError("Event missing start/end")
        # Python 3.11+ handles the trailing Z in fromisoformat, but normalise for older versions
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)

    def _window_from_preference(self, preference: str | None) -> tuple[datetime, datetime]:
        now = datetime.now(timezone.utc)
        # Default: next 7 days
        start = now + timedelta(hours=1)
        end = now + timedelta(days=7)
        if not preference:
            return start, end
        pref = preference.lower()
        if "tomorrow" in pref:
            d = (now + timedelta(days=1)).date()
            start = datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc)
            end = start + timedelta(days=1)
        elif "this week" in pref:
            end = now + timedelta(days=7)
        elif "next week" in pref:
            start = now + timedelta(days=7)
            end = start + timedelta(days=7)
        return start, end

    # ---------- Booking ----------

    def create_event(
        self,
        start_iso: str,
        duration_minutes: int,
        summary: str,
        description: str,
        attendee_email: str | None = None,
    ) -> dict[str, Any]:
        svc = self._get_service()
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end = start + timedelta(minutes=duration_minutes)
        body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": self._settings.business_timezone or "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": self._settings.business_timezone or "UTC"},
        }
        if attendee_email:
            body["attendees"] = [{"email": attendee_email}]

        event = svc.events().insert(  # type: ignore[attr-defined]
            calendarId=self._settings.google_calendar_id,
            body=body,
            sendUpdates="all" if attendee_email else "none",
        ).execute()
        logger.info("calendar.booked", extra={"booking_id": event.get("id")})
        return event
