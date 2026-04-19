# Multi_Channel_Onboarding — Automation Rules

> Inherits from parent `../CLAUDE.md`. Project-specific context below.

---

## Project

- **Name:** Multi_Channel_Onboarding
- **Objective:** Orchestrate Email → WhatsApp → Slack → Follow-up sequence from one signup trigger
- **Phase:** 3 — No-Code Automation Mastery (Week 6: Multi-Channel Communication)
- **Status:** In Progress
- **Owner:** Atlas
- **Dispatched by:** Angelina

---

## Agentic Loop

1. **Sense:** Signup webhook / batch / DB trigger
2. **Think:** LLM personalizes copy per user segment
3. **Decide:** Which channels + which cadence
4. **Act:** Email → WhatsApp → Slack → scheduled follow-ups
5. **Learn:** Track open/reply rates → adjust next run

---

## Tech

| Layer | Choice |
|-------|--------|
| Orchestration | Python (argparse CLIs) |
| AI Model | euri/gpt-4o-mini |
| Email | Resend (free 100/day) |
| WhatsApp | Twilio OR Meta Cloud API |
| Internal Alert | Slack Incoming Webhook |
| Queue | JSON file in `.tmp/` (MVP) |
| Deploy (later) | n8n OR GitHub Actions |

---

## Inherited Rules

All rules from parent `../CLAUDE.md` apply:
- Agentic Loop architecture
- 3-layer separation (Agent → Workflows → Tools)
- 10 Operational Rules
- 14 Security Guardrails
- Budget: $2/run, $5/day
- Self-Improvement Loop
- Tool-first execution

---

## Project-Specific Rules

- **Never send to real users during dev.** Always use `--dry-run` or `--to test@example.com`.
- **WhatsApp template must be pre-approved** by Meta/Twilio before prod run.
- **Follow-up queue stays in `.tmp/`** until Angelina approves prod queue (Redis/cron/n8n).

---

## Files

```
Multi_Channel_Onboarding/
├── ATLAS-PROMPT.md   # Build brief for Atlas
├── CLAUDE.md         # This file
├── PROMPTS.md        # Prompt tracker
├── README.md         # Project description
├── .env.example      # Required keys
├── workflows/        # Markdown SOPs
├── tools/            # Python scripts
├── runs/             # Execution logs
└── .tmp/             # Intermediate files
```
