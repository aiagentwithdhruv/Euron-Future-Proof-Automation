# Multi_Channel_Onboarding — Prompts

> All prompts used in this project. Also indexed in root `PROMPTS.md`.

---

## Prompts Built

| Name | Purpose | File | Variables | Category |
|------|---------|------|-----------|----------|
| `personalize_welcome_v1` | Generate per-channel (email + whatsapp + slack) welcome copy in one shot | `tools/personalize_copy.py` (inline) | `user_profile` (name, email, segment, language, product_interest, signup_source) | content |

### `personalize_welcome_v1` — Full Text

```
You write onboarding copy for a new product signup.

User profile (JSON):
{user_json}

Return STRICT JSON (no markdown, no commentary) with exactly this shape:
{
  "email": {
    "subject": "short, benefit-led, <= 9 words",
    "body": "warm, concise, 80-130 words, plain text, ends with a single clear CTA"
  },
  "whatsapp": "short welcome, under 300 chars, friendly, 0-1 emoji, include opt-out note",
  "slack": "one-line internal alert for the growth team, use the format ':wave: New signup — <name> (<email>) | segment: <seg> | source: <src>'"
}

Rules:
- Language: {language}
- Tone fits segment: {segment}
- Reference their interest: {product_interest}
- No fabricated discounts, pricing, dates, or URLs.
- No placeholder text like [NAME]; use the real name from the profile.
```

**Model:** `euri/gpt-4o-mini` @ `temperature=0.7, max_tokens=700`
**Fallback:** Deterministic template in `template_copy()` when `EURI_API_KEY` missing or LLM call fails.

---

## Prompts Deferred

| Name | Why deferred |
|------|--------------|
| `segment_user` | MVP takes `segment` as an explicit field on the signup payload. Auto-segmentation will be added in v2 when we have enough signups to train classification rules. |

---

## Build Prompt

`ATLAS-PROMPT.md` is the full build brief for this project.

---

**Last Updated:** 2026-04-19
