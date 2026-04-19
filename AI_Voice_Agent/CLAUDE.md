# AI_Voice_Agent — Rules

> Inherits from `../CLAUDE.md`.

---

## Project

- **Name:** AI_Voice_Agent
- **Objective:** Inbound receptionist + outbound follow-up caller (AI voice)
- **Phase:** 4 — AI-Powered Autonomous Systems (Week 10)
- **Status:** In Progress
- **Owner:** Atlas

---

## Agentic Loop

1. **Sense:** Call in OR outbound task trigger
2. **Think:** Identify intent + branch
3. **Decide:** Book / capture / escalate
4. **Act:** Calendar + CRM + confirmations
5. **Learn:** Post-call transcript + tags

---

## Tech

| Layer | Choice |
|-------|--------|
| Voice Platform | Vapi (or Bland / Retell) |
| LLM | euri/gpt-4o (if platform supports custom) |
| Calendar | Google Calendar API |
| SMS | Twilio |
| Email | Resend |
| Store | Supabase |
| Backend | FastAPI (tool endpoints) |
| Deploy (later) | Koyeb |

---

## Project-Specific Rules

- **Consent mandatory** for outbound calls.
- **Recording disclosure** on every call if recording.
- **"Talk to human" always works** — escalation path never blocked.
- **Never expose tool endpoints without API key** — Vapi config uses shared secret.
- **Transcript + summary logged for every call** — never skip.
