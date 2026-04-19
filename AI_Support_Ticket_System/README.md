# AI Support Ticket System

> Email in → AI classifies, routes, drafts reply → human approves → auto-send.

---

## What It Does

Polls a support inbox. Every new email is classified (intent, priority, sentiment), a ticket is created, an LLM drafts a reply using the knowledge base, the draft runs through a guardrail pipeline, and the ticket lands in an approval queue. On approval, the reply sends automatically.

## Agentic Loop

- **Sense:** New email (IMAP)
- **Think:** Classify + prioritize
- **Decide:** Route + draft reply
- **Act:** Notify team + await approval + send
- **Learn:** Track approval edits → tune draft prompt

## Setup

```bash
cp .env.example .env
# Fill IMAP, EURI, AIRTABLE, RESEND, SLACK keys
```

## Run

```bash
python tools/run_ticket_cycle.py --dry-run --fixtures .tmp/fake_emails.json
python tools/approval_queue.py --list
python tools/approval_queue.py --approve TICKET-123
```

## Deploy (later)

**n8n** scheduled workflow (poll IMAP every 2-5 min) — default path for this bootcamp. See root `DEPLOY.md`.

---

**Phase:** 4
**Owner:** Atlas
