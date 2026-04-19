"""Config loader — reads .env, validates required keys at startup."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv_if_present() -> None:
    """Lightweight .env loader (no python-dotenv dep)."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return
    with open(env_path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv_if_present()


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


@dataclass
class Settings:
    # Core
    api_key: str = field(default_factory=lambda: os.environ.get("API_KEY", ""))
    environment: str = field(default_factory=lambda: os.environ.get("ENVIRONMENT", "dev"))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    # Voice platform
    voice_platform: str = field(default_factory=lambda: os.environ.get("VOICE_PLATFORM", "vapi").lower())
    vapi_api_key: str = field(default_factory=lambda: os.environ.get("VAPI_API_KEY", ""))
    vapi_assistant_id: str = field(default_factory=lambda: os.environ.get("VAPI_ASSISTANT_ID", ""))
    vapi_phone_number_id: str = field(default_factory=lambda: os.environ.get("VAPI_PHONE_NUMBER_ID", ""))
    vapi_api_base: str = field(default_factory=lambda: os.environ.get("VAPI_API_BASE", "https://api.vapi.ai"))

    # Business context
    business_name: str = field(default_factory=lambda: os.environ.get("BUSINESS_NAME", "Acme Business"))
    business_hours: str = field(default_factory=lambda: os.environ.get("BUSINESS_HOURS", "Mon-Fri 9am-6pm"))
    business_services: str = field(default_factory=lambda: os.environ.get("BUSINESS_SERVICES", "consultations, follow-ups"))
    business_timezone: str = field(default_factory=lambda: os.environ.get("BUSINESS_TIMEZONE", "UTC"))
    recording_enabled: bool = field(default_factory=lambda: _bool("RECORDING_ENABLED", True))
    human_handoff_number: str = field(default_factory=lambda: os.environ.get("HUMAN_HANDOFF_NUMBER", ""))

    # LLM (Euri — free, OpenAI-compatible)
    euri_api_key: str = field(default_factory=lambda: os.environ.get("EURI_API_KEY", ""))
    euri_base_url: str = field(default_factory=lambda: os.environ.get("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"))
    llm_model_fast: str = field(default_factory=lambda: os.environ.get("LLM_MODEL_FAST", "gpt-4o-mini"))
    llm_model_strong: str = field(default_factory=lambda: os.environ.get("LLM_MODEL_STRONG", "gpt-4o"))

    # Calendar
    google_calendar_id: str = field(default_factory=lambda: os.environ.get("GOOGLE_CALENDAR_ID", ""))
    google_service_account_json: str = field(default_factory=lambda: os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""))
    default_slot_minutes: int = field(default_factory=lambda: _int("DEFAULT_SLOT_MINUTES", 30))

    # Twilio
    twilio_account_sid: str = field(default_factory=lambda: os.environ.get("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.environ.get("TWILIO_AUTH_TOKEN", ""))
    twilio_from: str = field(default_factory=lambda: os.environ.get("TWILIO_FROM", ""))

    # Resend
    resend_api_key: str = field(default_factory=lambda: os.environ.get("RESEND_API_KEY", ""))
    email_from: str = field(default_factory=lambda: os.environ.get("EMAIL_FROM", ""))

    # Supabase
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", ""))
    supabase_service_key: str = field(default_factory=lambda: os.environ.get("SUPABASE_SERVICE_KEY", ""))

    # Compliance
    outbound_window_start: int = field(default_factory=lambda: _int("OUTBOUND_WINDOW_START", 9))
    outbound_window_end: int = field(default_factory=lambda: _int("OUTBOUND_WINDOW_END", 19))
    max_outbound_attempts: int = field(default_factory=lambda: _int("MAX_OUTBOUND_ATTEMPTS", 3))

    def require(self, *keys: str) -> None:
        missing = [k for k in keys if not getattr(self, k, "")]
        if missing:
            raise RuntimeError(f"Missing required config: {', '.join(missing)}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
