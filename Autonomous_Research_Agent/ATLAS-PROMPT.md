# Atlas — Autonomous Research Agent

> **Persona:** Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina.
> **Rule #0:** If unclear, STOP and ask Angelina.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules
2. `../learning-hub/ERRORS.md`
3. `../learning-hub/automations/CATALOG.md`
4. `../AI_News_Telegram_Bot/` — reuse news fetcher + LLM ranker + Telegram delivery
5. `../Agentic Workflow for Students/shared/` — shared modules
6. `../student-starter-kit/agents/researcher.md` — researcher agent patterns
7. `../student-starter-kit/skills/ghost-browser/SKILL.md` — stealth web browsing

---

## Objective (one sentence)

**Weekly autonomous agent that browses competitor sites, news, social posts → analyzes changes → writes a research report → delivers to Slack/Email/Telegram without any human trigger.**

---

## Agentic Loop

- **Sense:** Cron fires weekly (no human) → agent pulls competitor list + last snapshot
- **Think:** Browse each source → diff vs last snapshot → LLM identifies "what's new / what changed / what matters"
- **Decide:** Which findings make the report → priority ranking → write executive summary
- **Act:** Generate report (markdown + PDF) → deliver to Slack + Email + Telegram → save snapshot
- **Learn:** Track which findings Dhruv flags as valuable → tune relevance prompt

---

## Build Contract

1. `workflows/research-cycle.md` — weekly SOP
2. Tools atomic
3. Reuse news fetcher pattern from AI_News_Telegram_Bot
4. Snapshot storage in `data/snapshots/` (commitable, small JSON per competitor)
5. Test locally with 2 competitors → full run
6. DO NOT deploy (GitHub Actions cron is trivial later)

---

## Tools to Build

| Tool | Input | Output |
|------|-------|--------|
| `tools/fetch_competitor.py` | --url URL | scraped content + metadata |
| `tools/fetch_news.py` | --keywords "X" --days 7 | list of articles |
| `tools/fetch_social.py` | --handle @name --platform linkedin\|twitter | recent posts |
| `tools/snapshot_diff.py` | --current F1 --previous F2 | diff JSON |
| `tools/analyze_changes.py` | diffs JSON | "what's new + what matters" insights |
| `tools/write_report.py` | insights JSON | markdown report |
| `tools/deliver_report.py` | report.md | Slack + email + Telegram receipts |
| `tools/run_research.py` | --competitors config.yaml | full orchestration |

---

## Workflow SOP

`workflows/research-cycle.md`:

```
Step 1 — Load competitor list from config.yaml
Step 2 — For each competitor: fetch site, news, social
Step 3 — Compare vs previous snapshot (diff)
Step 4 — LLM: classify changes (pricing / launch / hire / partnership / press)
Step 5 — Rank findings by business relevance
Step 6 — Write executive summary + detailed findings
Step 7 — Deliver report
Step 8 — Save new snapshots
Step 9 — Log run
```

---

## APIs / Tools

| API | Free Tier | Used For |
|-----|-----------|----------|
| Euri | 200K tokens/day | LLM |
| NewsAPI / Tavily | Free | News |
| Apify / Outscraper | Free trial | Web scraping |
| Slack / Resend / Telegram | Free | Delivery |

---

## Env Vars

```
EURI_API_KEY=
NEWSAPI_KEY=
TAVILY_API_KEY=
APIFY_API_TOKEN=

SLACK_WEBHOOK_URL=
RESEND_API_KEY=
EMAIL_TO=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

COMPETITORS_CONFIG=./config/competitors.yaml
```

---

## Rules of Engagement

- **Doubt = STOP.** Questions:
  - "Who are the competitors? Dhruv provides list OR do I scrape industry leaders?"
  - "Which industry? AI automation, SaaS, D2C, or specific?"
  - "Delivery channels — all three (Slack + Email + Telegram) or pick one?"
  - "Cadence — weekly Monday 9 AM or other?"
- **Respect robots.txt** — never scrape what's disallowed.
- **Rate-limit scrapers** — 1 request per 3 sec baseline.
- **Never store PII** from scraped content.

---

## Test Command

```bash
cd Autonomous_Research_Agent
python tools/run_research.py --competitors config/competitors.yaml --dry-run
```

---

## When Done

Update catalog + ping Angelina.
