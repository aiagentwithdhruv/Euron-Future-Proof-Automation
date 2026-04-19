"""Euri LLM wrapper — one function for the whole suite.

Caller passes a `prompt_name` (which maps to a file in prompts/) plus the
variables; the function renders the prompt, calls Euri, and returns the raw
text. JSON-mode callers parse downstream.

If EURI_API_KEY is missing or the SDK isn't installed, the function raises
`LLMUnavailable` so each module can decide on its deterministic fallback.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import tools._bootstrap  # noqa: F401

from shared.logger import get_logger  # noqa: E402

from tools.config import env, project_root

logger = get_logger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
EURI_BASE_URL = "https://api.euron.one/api/v1/euri"


class LLMUnavailable(RuntimeError):
    pass


def _prompt_path(name: str) -> Path:
    p = project_root() / "prompts" / f"{name}.md"
    if not p.exists():
        raise FileNotFoundError(f"Prompt not found: {p}")
    return p


def render(name: str, variables: dict[str, Any]) -> str:
    text = _prompt_path(name).read_text()
    # Strip frontmatter if present.
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) >= 3 else text
    for key, val in variables.items():
        text = text.replace("{{" + key + "}}", str(val))
    return text.strip()


def generate(
    prompt_name: str,
    variables: Optional[dict[str, Any]] = None,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.5,
    max_tokens: int = 700,
    system: Optional[str] = None,
) -> str:
    api_key = env("EURI_API_KEY")
    if not api_key:
        raise LLMUnavailable("EURI_API_KEY missing")

    try:
        from openai import OpenAI  # local import
    except ImportError as e:
        raise LLMUnavailable(f"openai SDK missing: {e}")

    prompt = render(prompt_name, variables or {})

    client = OpenAI(base_url=EURI_BASE_URL, api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        raise LLMUnavailable(f"LLM call failed: {e}")

    content = (resp.choices[0].message.content or "").strip()
    logger.info("llm.generate", extra={"outputs": {"prompt": prompt_name, "len": len(content)}})
    return content


def generate_json(
    prompt_name: str,
    variables: Optional[dict[str, Any]] = None,
    **kwargs,
) -> dict:
    raw = generate(prompt_name, variables, **kwargs)
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise LLMUnavailable(f"LLM returned no JSON object. Raw: {raw[:200]}")
    return json.loads(match.group())
