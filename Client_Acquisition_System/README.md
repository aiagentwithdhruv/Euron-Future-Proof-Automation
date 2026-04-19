# Client Acquisition System

> End-to-end outbound: scrape → enrich → qualify → personalized outreach → booked discovery → proposal draft → close tracking.

---

## What It Does

Takes an ICP definition. Scrapes matching prospects from Google Maps / LinkedIn / Apollo. Enriches with email + LinkedIn + company context. LLM scores fit (0-100). High-scorers get hyper-personalized outreach emails (company-specific hooks). Replies route to booking link. Booked prospects get a pre-call brief. Post-call, a proposal draft is generated automatically.

## Agentic Loop

- **Sense:** ICP query / prospect list
- **Think:** Enrich + score
- **Decide:** Channel + message
- **Act:** Outreach → book → proposal
- **Learn:** Reply/meeting/close rates tune messages

## Setup

```bash
cp .env.example .env
# Edit config/icp.yaml with your ICP (industry, location, role, size)
```

## Run

```bash
# Dry-run with 5 prospects
python tools/run_pipeline.py --icp config/icp.yaml --limit 5 --dry-run

# Real
python tools/run_pipeline.py --icp config/icp.yaml --limit 50
```

## Deploy (later)

**n8n** (webhook for replies + scheduled scrape) OR **GitHub Actions** (weekly batch scrape). See root `DEPLOY.md`.

---

**Phase:** 8
**Owner:** Atlas
