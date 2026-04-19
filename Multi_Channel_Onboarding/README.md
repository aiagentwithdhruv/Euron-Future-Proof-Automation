# Multi-Channel Onboarding

> One signup → Email + WhatsApp + Slack alert + scheduled follow-up drip. Driven by AI personalization.

---

## What It Does

New user signs up → system validates and enriches profile → LLM generates personalized copy → dispatches across 3 live channels (email, WhatsApp, Slack internal alert) → schedules Day 2 and Day 5 follow-ups. Every run is logged; open/reply metrics feed back to improve channel priority.

## Agentic Loop

- **Sense:** Signup webhook / batch / DB trigger
- **Think:** Personalize copy via Euri gpt-4o-mini
- **Decide:** Sequence channels + cadence per segment
- **Act:** Email → WhatsApp → Slack → scheduled follow-ups
- **Learn:** Track opens/replies → tune next run

## Setup

```bash
cp .env.example .env
# Fill: EURI_API_KEY, RESEND_API_KEY, TWILIO_*, SLACK_WEBHOOK_URL
```

## Run

```bash
# Dry-run with fake payload
python tools/run_onboarding.py --signup .tmp/fake_signup.json --dry-run

# Real run
python tools/run_onboarding.py --signup .tmp/real_signup.json
```

## Deploy (later)

Two paths (both free): **n8n** webhook workflow for real-time signups, OR **GitHub Actions** for batch CSV mode. See root `DEPLOY.md`.

---

**Phase:** 3 — No-Code Automation Mastery
**Built:** _(pending)_
**Owner:** Atlas
