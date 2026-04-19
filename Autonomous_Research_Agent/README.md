# Autonomous Research Agent

> Weekly AI agent that tracks your competitors, news, and industry signals — delivers a written report every Monday. No human trigger.

---

## What It Does

Watches a list of competitors + industry keywords. Every week: scrapes sites, pulls news, fetches social posts, diffs against last week, identifies meaningful changes (pricing / launch / hire / partnership / press), ranks by business relevance, writes an executive summary, delivers via Slack + Email + Telegram.

## Agentic Loop

- **Sense:** Cron weekly
- **Think:** Diff + classify changes
- **Decide:** Rank findings
- **Act:** Report + deliver
- **Learn:** Feedback tunes relevance

## Setup

```bash
cp .env.example .env
# Edit config/competitors.yaml with your competitor list
```

## Run

```bash
python tools/run_research.py --competitors config/competitors.yaml --dry-run
python tools/run_research.py --competitors config/competitors.yaml
```

## Deploy (later)

GitHub Actions cron (`0 3 * * 1` = Monday 3 AM UTC = 8:30 AM IST). See root `DEPLOY.md`.

---

**Phase:** 4
**Owner:** Atlas
