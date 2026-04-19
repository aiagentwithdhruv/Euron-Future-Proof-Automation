# AI_Support_Ticket_System — Rules

> Inherits from `../CLAUDE.md`.

---

## Project

- **Name:** AI_Support_Ticket_System
- **Objective:** Email in → AI classify + route + draft reply → human approve → auto-send
- **Phase:** 4 — AI-Powered Autonomous Systems (Week 8)
- **Status:** In Progress
- **Owner:** Atlas

---

## Agentic Loop

1. **Sense:** New email (IMAP poll)
2. **Think:** Classify intent + priority + sentiment
3. **Decide:** Route + pick template + draft
4. **Act:** Ticket + Slack notify + approval queue → on approval send
5. **Learn:** Approval edits feed back to draft prompt

---

## Tech

| Layer | Choice |
|-------|--------|
| Language | Python |
| AI Model | euri/gpt-4o-mini (classify), euri/gpt-4o (draft) |
| Inbox | IMAP (Gmail App Password) |
| Ticket Store | Airtable (MVP) → Supabase (prod) |
| Email Out | Resend |
| Notify | Slack |
| Deploy (later) | n8n (scheduled poll every 2-5 min) |

---

## Project-Specific Rules

- **Human-in-the-loop mandatory v1.** No auto-send.
- **Guardrail every draft** — no PII, no pricing, no binding commitments.
- **IMAP password = Gmail App Password**, not real password.
- **Knowledge base pluggable** — `knowledge/` folder or RAG later.
