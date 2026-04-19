"""Thin Euri LLM wrapper (OpenAI-compatible). Falls back to OpenRouter / OpenAI."""

from __future__ import annotations

import json
import os
from typing import Any

from shared import env
from shared.logger import get_logger

logger = get_logger(__name__)


def _client():
    from openai import OpenAI

    if env.get("EURI_API_KEY"):
        return OpenAI(
            base_url=env.get("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"),
            api_key=env.get("EURI_API_KEY"),
        )
    if env.get("OPENROUTER_API_KEY"):
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=env.get("OPENROUTER_API_KEY"),
        )
    if env.get("OPENAI_API_KEY"):
        return OpenAI(api_key=env.get("OPENAI_API_KEY"))
    raise EnvironmentError(
        "No LLM key configured. Set EURI_API_KEY (preferred — free) or OPENROUTER_API_KEY / OPENAI_API_KEY."
    )


def has_llm() -> bool:
    return bool(env.get("EURI_API_KEY") or env.get("OPENROUTER_API_KEY") or env.get("OPENAI_API_KEY"))


def chat(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.4,
    json_mode: bool = False,
    max_tokens: int = 800,
) -> str:
    """Return the assistant text. Raises on hard failure."""
    m = model or env.get("EURI_MODEL_PERSONALIZE", "gpt-4o-mini")
    kwargs: dict[str, Any] = {
        "model": m,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    client = _client()
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def chat_json(*, system: str, user: str, model: str | None = None, temperature: float = 0.2) -> dict:
    """Call the LLM and parse JSON. Retries once without strict mode on parse failure."""
    raw = chat(system=system, user=user, model=model, temperature=temperature, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"LLM returned non-JSON under json_mode; trying lenient parse: {raw[:160]}")
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
        raise


# ── Dry-run stub ──────────────────────────────────────────────────

def stub_response(kind: str, **fields) -> dict:
    """For --dry-run mode: return deterministic fake data without calling the API."""
    base = {
        "score_fit": {
            "fit_score": 78,
            "fit_reasoning": "[DRY-RUN] Industry match, correct geography, role is decision-maker.",
            "pain_hypothesis": "Manual lead routing slowing sales velocity.",
        },
        "personalize_email": {
            "subject": "[DRY-RUN] Quick question about {company}'s sales ops",
            "body": "Hi {name}, noticed {company} is hiring — looks like scale is on your mind...",
            "hook": "Saw your {signal}",
        },
        "linkedin_dm": {
            "dm": "[DRY-RUN] Hi {name}, noticed {company}'s recent post on {topic}...",
        },
        "prep_brief": {
            "brief_md": "# [DRY-RUN] Prep brief\n\n## Context\n...\n",
        },
        "proposal_draft": {
            "proposal_md": "# [DRY-RUN] Proposal for {company}\n\n## Summary\n...\n",
        },
    }
    out = dict(base.get(kind, {}))
    for k, v in out.items():
        if isinstance(v, str):
            out[k] = v.format(**{f: fields.get(f, f"<{f}>") for f in fields})
    return out
