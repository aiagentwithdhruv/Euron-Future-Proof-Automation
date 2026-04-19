# Autonomous_Research_Agent — Rules

> Inherits from `../CLAUDE.md`.

---

## Project

- **Name:** Autonomous_Research_Agent
- **Objective:** Weekly autonomous competitor/market research → report → deliver (no human trigger)
- **Phase:** 4 — AI-Powered Autonomous Systems (Week 10)
- **Status:** In Progress
- **Owner:** Atlas

---

## Agentic Loop

1. **Sense:** Cron weekly trigger
2. **Think:** Diff sources, classify changes
3. **Decide:** What makes the report
4. **Act:** Write + deliver report
5. **Learn:** Feedback on findings tunes prompts

---

## Tech

| Layer | Choice |
|-------|--------|
| Language | Python |
| LLM | euri/gpt-4o |
| Scraping | Apify OR BS4 + requests |
| News | NewsAPI + Tavily |
| Delivery | Slack + Email + Telegram |
| Storage | JSON files in `data/snapshots/` |
| Deploy (later) | GitHub Actions cron |

---

## Project-Specific Rules

- **Respect robots.txt.** Skip disallowed URLs.
- **Rate-limit scraping** — 3 sec between requests per domain.
- **Snapshot diff = source of truth** — never re-analyze full content when diff exists.
- **Never store PII** scraped from external sites.
- **Cost cap per run: $1** — abort if exceeded.
