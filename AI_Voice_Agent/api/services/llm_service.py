"""Euri LLM wrapper — OpenAI-compatible. Used for post-call summary + tagging."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from api.config import get_settings
from api.logging_utils import get_logger


logger = get_logger(__name__)


class LLMError(RuntimeError):
    pass


class LLMService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(self._settings.euri_api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.enabled:
            raise LLMError("Euri not configured (set EURI_API_KEY)")
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            raise LLMError("openai package not installed. Add to requirements.txt.") from e
        self._client = OpenAI(
            api_key=self._settings.euri_api_key,
            base_url=self._settings.euri_base_url,
        )
        return self._client

    def summarize_call(
        self,
        transcript: str,
        call_direction: str,
        duration_s: float,
        caller_phone: str | None,
    ) -> dict[str, Any]:
        prompt_path = Path(__file__).resolve().parent.parent.parent / "prompts" / "post_call_summary.md"
        # Use inline prompt; the file is source-of-truth but we interpolate a compact version for stability.
        system = (
            "You analyze completed phone call transcripts and return structured JSON. "
            "You never hallucinate. If a field is unknown, return null."
        )
        user = _USER_TEMPLATE.format(
            business_name=self._settings.business_name,
            call_direction=call_direction,
            duration_s=int(duration_s or 0),
            caller_phone=caller_phone or "unknown",
            transcript=transcript or "(empty)",
        )
        # Primary attempt
        for model in (self._settings.llm_model_fast, self._settings.llm_model_strong):
            try:
                client = self._get_client()
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=600,
                )
                raw = resp.choices[0].message.content or "{}"
                return json.loads(raw)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"llm.summary.attempt_failed model={model}: {e}")
        # Final fallback — stub
        return {
            "summary": "Auto-summary failed; see transcript.",
            "outcome": "other",
            "tags": [],
            "sentiment": "neutral",
            "caller_intent": "unknown",
            "action_items": [],
            "customer_name": None,
            "customer_email": None,
            "booking_ref": None,
            "needs_human_review": True,
            "confidence": 0.0,
        }


_USER_TEMPLATE = """\
Below is a phone call transcript. Direction: {call_direction}.
Duration: {duration_s} seconds. Caller phone: {caller_phone}. Business: {business_name}.

TRANSCRIPT:
---
{transcript}
---

Return ONE JSON object with exactly these fields:
summary (2-3 sentence neutral summary),
outcome (one of: booked | info_given | lead_captured | escalated_to_human | not_interested | callback_requested | voicemail | wrong_person | dnc_requested | incomplete | other),
tags (array of up to 6 lowercase tags),
sentiment (positive | neutral | negative),
caller_intent (book_appointment | info_request | existing_customer | complaint | human | sales_follow_up | unknown),
action_items (array; empty if none),
customer_name (or null),
customer_email (or null),
booking_ref (or null),
needs_human_review (true | false),
confidence (0.0-1.0).

JSON only. No markdown.
"""
