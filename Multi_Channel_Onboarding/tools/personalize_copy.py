#!/usr/bin/env python3
"""Tool: personalize_copy

Generate welcome copy for 3 channels (email, whatsapp, slack) tailored to the
user's segment + language + product_interest. Uses Euri gpt-4o-mini; falls back
to deterministic templates when no LLM key is present or LLM fails.

Input: --user path to cleaned user.json produced by receive_signup.py
Output: writes .tmp/<user_id>/copy.json and prints a status JSON to stdout
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

MODEL = "gpt-4o-mini"
TEMPERATURE = 0.7


def template_copy(user: dict) -> dict:
    """Deterministic fallback — used whenever LLM is unavailable."""
    name = user.get("name", "there").split()[0]
    product = user.get("product_interest", "our platform")
    return {
        "email": {
            "subject": f"Welcome to {product}, {name}!",
            "body": (
                f"Hi {name},\n\n"
                f"Thanks for signing up for {product}. "
                f"We're thrilled to have you. Over the next few days I'll share the highest-leverage "
                f"resources we've built to help you get moving fast.\n\n"
                f"If you hit any friction, just reply to this email — a human reads every response.\n\n"
                f"— The Team"
            ),
        },
        "whatsapp": (
            f"Hey {name}! Welcome aboard {product}. "
            f"Save this number — you'll hear from us here for time-sensitive nudges. Reply STOP to opt out."
        ),
        "slack": (
            f":wave: New signup — *{user.get('name','?')}* "
            f"({user.get('email','?')}) | segment: `{user.get('segment','?')}` | "
            f"source: `{user.get('signup_source','?')}`"
        ),
        "generator": "template",
    }


def build_prompt(user: dict) -> str:
    return f"""You write onboarding copy for a new product signup.

User profile (JSON):
{json.dumps(user, indent=2, ensure_ascii=False)}

Return STRICT JSON (no markdown, no commentary) with exactly this shape:
{{
  "email": {{
    "subject": "short, benefit-led, <= 9 words",
    "body": "warm, concise, 80-130 words, plain text, ends with a single clear CTA"
  }},
  "whatsapp": "short welcome, under 300 chars, friendly, 0-1 emoji, include opt-out note",
  "slack": "one-line internal alert for the growth team, use the format ':wave: New signup — <name> (<email>) | segment: <seg> | source: <src>'"
}}

Rules:
- Language: {user.get('language','en')}
- Tone fits segment: {user.get('segment','student')}
- Reference their interest: {user.get('product_interest','')}
- No fabricated discounts, pricing, dates, or URLs.
- No placeholder text like [NAME]; use the real name from the profile.
"""


def try_llm(user: dict) -> dict | None:
    euri_key = os.environ.get("EURI_API_KEY")
    if not euri_key:
        logger.info("personalize_copy: no EURI_API_KEY — using template fallback")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("personalize_copy: openai SDK not installed — template fallback")
        return None

    client = OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri_key)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": build_prompt(user)}],
            temperature=TEMPERATURE,
            max_tokens=700,
        )
    except Exception as e:
        logger.warning(f"personalize_copy: LLM call failed — {e}")
        return None

    raw = (response.choices[0].message.content or "").strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        logger.warning("personalize_copy: LLM returned no JSON object — template fallback")
        return None

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        logger.warning(f"personalize_copy: JSON parse error — {e}")
        return None

    if not (
        isinstance(data.get("email"), dict)
        and data["email"].get("subject")
        and data["email"].get("body")
        and isinstance(data.get("whatsapp"), str)
        and isinstance(data.get("slack"), str)
    ):
        logger.warning("personalize_copy: LLM JSON missing required keys — template fallback")
        return None

    data["generator"] = "euri:gpt-4o-mini"
    return data


def main():
    parser = argparse.ArgumentParser(description="Generate per-channel welcome copy")
    parser.add_argument("--user", required=True, help="Path to user.json from receive_signup")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    user_path = Path(args.user)
    if not user_path.is_absolute():
        user_path = PROJECT_ROOT / user_path
    if not user_path.exists():
        print(json.dumps({"status": "error", "code": "user_not_found"}), file=sys.stderr)
        sys.exit(2)

    user = json.loads(user_path.read_text())

    copy = try_llm(user) or template_copy(user)

    out_path = PROJECT_ROOT / ".tmp" / user["user_id"] / "copy.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(copy, indent=2, ensure_ascii=False))

    result = {
        "status": "success",
        "user_id": user["user_id"],
        "generator": copy.get("generator"),
        "copy_path": str(out_path.relative_to(PROJECT_ROOT)),
    }
    logger.info("copy_generated", extra={"outputs": result})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
