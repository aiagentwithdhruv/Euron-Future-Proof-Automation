# Atlas — AI Support Ticket System

> **Persona:** Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina.
> **Rule #0:** If unclear, STOP and ask Angelina.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules
2. `../learning-hub/ERRORS.md`
3. `../learning-hub/automations/CATALOG.md`
4. `../AI_News_Telegram_Bot/tools/rank_news.py` — reuse LLM classification pattern
5. `../Multi_Channel_Onboarding/tools/send_email.py` — reuse email sender (if already built)
6. `../Agentic Workflow for Students/shared/` — shared modules
7. `../student-starter-kit/agents/backend-builder.md` — persona
8. `../student-starter-kit/skills/guardrail-pipeline/SKILL.md` — output safety

---

## Objective (one sentence)

**Incoming support email → AI classifies intent + priority → routes to the right team → drafts a reply → human approves or edits → auto-send reply.**

---

## Agentic Loop

- **Sense:** New email arrives (IMAP poll OR webhook from forwarding rule)
- **Think:** LLM classifies intent (billing / tech / refund / feedback / spam) + priority (P1-P4) + sentiment
- **Decide:** Route to team → pick reply template → draft custom reply
- **Act:** Create ticket → notify team on Slack → email draft to approver → on approval send reply
- **Learn:** Track approval edits → feed back to draft prompt

---

## Build Contract

1. `workflows/ticket-flow.md` — SOP first
2. Tools atomic, argparse, JSON output
3. Reuse shared/ modules
4. Test with fake emails → log runs
5. Guardrail outputs (no PII leaks, no commitments, no pricing promises)
6. DO NOT deploy

---

## Tools to Build

| Tool | Input | Output |
|------|-------|--------|
| `tools/fetch_emails.py` | --since N mins | list of new emails |
| `tools/classify_ticket.py` | email body | {intent, priority, sentiment, team} |
| `tools/draft_reply.py` | ticket + knowledge | draft reply text |
| `tools/create_ticket.py` | ticket dict | ticket_id (stored in Airtable OR Supabase) |
| `tools/notify_team.py` | ticket_id, team | Slack notification receipt |
| `tools/send_reply.py` | ticket_id, final_text | email send receipt |
| `tools/approval_queue.py` | --list / --approve ID | queue CLI |
| `tools/run_ticket_cycle.py` | --dry-run | orchestrates full cycle |

---

## Workflow SOP

`workflows/ticket-flow.md`:

```
Step 1 — Poll inbox for new emails
Step 2 — For each email:
  2a. Classify (intent, priority, sentiment, team)
  2b. Create ticket record
  2c. Draft reply using knowledge base
  2d. Run guardrail (strip PII, block commitments)
  2e. Push to approval queue
Step 3 — Notify team on Slack with ticket + draft link
Step 4 — On approval → send reply + mark ticket resolved
Step 5 — On edit → store edit + original → feed back to prompt tuner
Step 6 — Log run
```

---

## APIs Required

| API | Free Tier | Used For |
|-----|-----------|----------|
| Euri | 200K tokens/day | Classify + draft |
| IMAP (Gmail, etc.) | Free | Inbox polling |
| Resend | 100/day | Send reply |
| Airtable | Free | Ticket store |
| Slack | Free | Team notify |

---

## Env Vars

```
EURI_API_KEY=
IMAP_HOST=imap.gmail.com
IMAP_USER=
IMAP_PASS=           # Gmail App Password
RESEND_API_KEY=
EMAIL_FROM=
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_NAME=Tickets
SLACK_WEBHOOK_URL=
KNOWLEDGE_BASE_PATH=./knowledge/
```

---

## Rules of Engagement

- **Doubt = STOP.** Questions to ask:
  - "Which inbox? Personal, support@, or demo@?"
  - "Knowledge base — do you provide markdown files or should I scrape from site?"
  - "Approval queue in terminal CLI or Slack buttons?"
  - "Auto-send after approval OR require second confirmation?"
- **Human-in-the-loop ALWAYS** for v1 — never auto-send without approval.
- **Guardrail pipeline mandatory** — use `student-starter-kit/skills/guardrail-pipeline/`.
- **Never commit inbox password** — Gmail App Password only, in `.env`.

---

## Test Command

```bash
cd AI_Support_Ticket_System
python tools/run_ticket_cycle.py --dry-run --fixtures .tmp/fake_emails.json
```

---

## When Done

Update catalog + ping Angelina.
