# Atlas — Multi-Channel Onboarding Automation

> **Persona:** You are Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina (top PM).
> **Rule #0:** If ANY requirement is unclear, STOP and ask Angelina. Never assume.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules (Agentic Loop, 3-layer arch, 10 ops rules, 14 security guardrails)
2. `../learning-hub/ERRORS.md` — 12 logged errors to avoid
3. `../learning-hub/CLAUDE.md` — Diamond self-learning protocol
4. `../learning-hub/automations/CATALOG.md` — reusable components from previous builds
5. `../Agentic Workflow for Students/shared/` — shared security modules (import, don't rewrite)
6. `../student-starter-kit/agents/backend-builder.md` — your agent persona
7. `../AI_News_Telegram_Bot/` — reference for scheduled runner + Telegram delivery
8. `../Social-Media-Automations/` — reference for multi-platform dispatch

---

## Objective (one sentence)

**When a new user signs up, orchestrate a sequenced multi-channel welcome flow across Email → WhatsApp → Slack (internal alert) → Follow-up drip, driven by one trigger.**

---

## Agentic Loop — This Automation

- **Sense:** New signup event (webhook from form / Supabase row insert / CSV batch)
- **Think:** LLM reads user profile → decides tone, language, product focus, optimal send times
- **Decide:** Which channels + which sequence + which follow-up cadence (based on user segment)
- **Act:** Send email → WhatsApp message → Slack internal alert → schedule Day 2 / Day 5 follow-ups
- **Learn:** Log open/reply rates per channel → next run adjusts channel priority

---

## Build Contract

1. **Scaffold** folder structure already done by Angelina (workflows/, tools/, runs/, .tmp/)
2. **Workflow FIRST** — write `workflows/onboarding-flow.md` (numbered SOP in English) BEFORE any Python
3. **Tools = atomic CLIs** — one job each, argparse, `.env` secrets, JSON stdout, proper exit codes
4. **Reuse from shared/** — `env_loader.py`, `logger.py`, `cost_tracker.py`, `sandbox.py`
5. **Test locally** with fake signup payload → log to `runs/YYYY-MM-DD-test.md`
6. **DO NOT DEPLOY** — Angelina dispatches deploy separately

---

## Tools to Build

| Tool | Input | Output | Notes |
|------|-------|--------|-------|
| `tools/receive_signup.py` | JSON webhook payload | validated user dict | Sanitize via shared/sanitize.py |
| `tools/personalize_copy.py` | user dict + template | customized message text | Euri gpt-4o-mini, temp 0.7 |
| `tools/send_email.py` | to, subject, body | delivery receipt | Use Resend API (free 100/day) OR SMTP |
| `tools/send_whatsapp.py` | phone, message | delivery receipt | WhatsApp Business API OR Twilio |
| `tools/send_slack.py` | channel, message | delivery receipt | Slack webhook URL |
| `tools/schedule_followup.py` | user_id, delay_days, message | scheduled task id | JSON file-based queue in `.tmp/` |
| `tools/run_onboarding.py` | signup JSON | orchestration receipt | Calls above tools in sequence |

---

## Workflow SOP to Write

`workflows/onboarding-flow.md` must contain:

```
Step 1 — Receive signup (webhook or batch)
Step 2 — Validate + enrich user data
Step 3 — Generate personalized copy (AI)
Step 4 — Send welcome email (channel 1)
Step 5 — Send WhatsApp welcome (channel 2)
Step 6 — Fire internal Slack alert (channel 3)
Step 7 — Schedule Day 2 nudge
Step 8 — Schedule Day 5 deep-value email
Step 9 — Log everything to runs/
```

Plus error-handling branch per step.

---

## APIs Required

| API | Free Tier | Used For |
|-----|-----------|----------|
| Euri | 200K tokens/day free | Personalization |
| Resend | 100 emails/day free | Email |
| Twilio / WhatsApp Cloud | Trial credits | WhatsApp |
| Slack Incoming Webhook | Free | Internal alert |

---

## Env Vars Needed

```
EURI_API_KEY=
RESEND_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=
SLACK_WEBHOOK_URL=
```

Write these to `.env.example`.

---

## Rules of Engagement

- **Doubt = STOP.** Ask Angelina in chat before inventing. Sample questions to ask if unsure:
  - "Which email provider does Dhruv want — Resend or SMTP?"
  - "Should WhatsApp use Twilio trial or Meta Cloud API?"
  - "Is the signup source a webhook, a CSV upload, or Supabase trigger?"
- **Reuse > rewrite.** If a tool exists in `Agentic Workflow for Students/shared/` or any other built project, import it.
- **Never skip the workflow SOP.** Agent needs instructions before hands get to work.
- **Log every error to `../learning-hub/ERRORS.md`** the moment it happens (don't batch).
- **Log learnings to `../learning-hub/LEARNINGS.md`** at end of session.
- **Update `../learning-hub/automations/CATALOG.md`** when the build is complete.

---

## Test Command (success = passing this)

```bash
cd Multi_Channel_Onboarding
python tools/run_onboarding.py --signup .tmp/fake_signup.json --dry-run
# Should print JSON: {"status": "success", "channels_sent": [...], "scheduled": [...]}
```

---

## When Done

1. Update `PROMPTS.md` in this folder with prompts used
2. Add one-liner to root `PROMPTS.md`
3. Add entry to `../learning-hub/automations/CATALOG.md`
4. Ping Angelina with: "Multi-Channel Onboarding — built, local test passed, ready for deploy dispatch"
