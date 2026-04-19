"""Orchestrates post-call work: persist transcript, summarize async, update lead."""

from __future__ import annotations

from typing import Any

from api.logging_utils import get_logger
from api.services.crm_service import CRMService
from api.services.llm_service import LLMService


logger = get_logger(__name__)


class CallLogService:
    def __init__(self, crm: CRMService | None = None, llm: LLMService | None = None) -> None:
        self._crm = crm or CRMService()
        self._llm = llm or LLMService()

    def finalize(
        self,
        call_id: str,
        direction: str,
        caller_phone: str | None,
        transcript: str,
        duration_s: float,
        recording_url: str | None,
        raw_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # 1. Insert baseline row (so we never drop a call log even if summary fails)
        base = {
            "call_id": call_id,
            "direction": direction,
            "caller_phone": caller_phone,
            "transcript": transcript,
            "duration_s": duration_s,
            "recording_url": recording_url,
            "summary_status": "pending",
        }
        if self._crm.enabled:
            try:
                self._crm.insert_call_log(base)
            except Exception as e:  # noqa: BLE001
                logger.error(f"call_log.insert_failed: {e}")
        else:
            logger.warning("call_log.crm_disabled", extra={"call_id": call_id})

        # 2. Summarize (best effort)
        summary: dict[str, Any]
        if self._llm.enabled and transcript:
            try:
                summary = self._llm.summarize_call(transcript, direction, duration_s, caller_phone)
            except Exception as e:  # noqa: BLE001
                logger.error(f"call_log.summary_failed: {e}")
                summary = {"summary_status": "failed", "needs_human_review": True}
        else:
            summary = {
                "summary_status": "skipped",
                "needs_human_review": True,
                "summary": "(LLM disabled or empty transcript)",
            }

        # 3. Merge summary back onto call log
        if self._crm.enabled:
            try:
                update: dict[str, Any] = {
                    "summary": summary.get("summary"),
                    "outcome": summary.get("outcome"),
                    "tags": summary.get("tags"),
                    "sentiment": summary.get("sentiment"),
                    "caller_intent": summary.get("caller_intent"),
                    "action_items": summary.get("action_items"),
                    "needs_human_review": summary.get("needs_human_review", False),
                    "confidence": summary.get("confidence"),
                    "summary_status": summary.get("summary_status", "ok"),
                }
                self._crm.update_call_log(call_id, {k: v for k, v in update.items() if v is not None})
            except Exception as e:  # noqa: BLE001
                logger.error(f"call_log.update_failed: {e}")

        return summary
