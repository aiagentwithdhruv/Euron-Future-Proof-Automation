# Client_Acquisition_System — Rules

> Inherits from `../CLAUDE.md`.

---

## Project

- **Name:** Client_Acquisition_System
- **Objective:** End-to-end outbound pipeline (scrape → enrich → qualify → outreach → discovery → proposal)
- **Phase:** 8 — Career, Clients & Building a Business (Week 19)
- **Status:** In Progress
- **Owner:** Atlas

---

## Agentic Loop

1. **Sense:** ICP query or prospect list
2. **Think:** Score fit + personalize
3. **Decide:** Channel + message + timing
4. **Act:** Outreach → book → proposal
5. **Learn:** Track reply/meeting/close rates per segment

---

## Tech

| Layer | Choice |
|-------|--------|
| Scraping | Apify / Outscraper / Apollo |
| Enrichment | Hunter.io + Apollo |
| LLM | euri/gpt-4o (personalize), gpt-4o-mini (qualify) |
| Email | Resend |
| LinkedIn | Manual-review draft only |
| Booking | Cal.com / Calendly |
| State | Airtable |
| Deploy (later) | n8n (primary) + GitHub Actions (weekly batch scrape) |

---

## Project-Specific Rules

- **Compliance mandatory** — CAN-SPAM + DPDP (India). Unsubscribe link in every email.
- **No auto-LinkedIn-DM** — LinkedIn ToS. Draft + human-send.
- **Rate limits:** 50 emails/day, 1 per prospect per 3 days.
- **Every message personalized** — company-specific hook required.
- **Never share prospect data** across clients.
