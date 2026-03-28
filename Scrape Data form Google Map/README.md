# Google Maps Lead Scraper

An AI-powered automation that scrapes business leads from Google Maps for any industry across US and Middle East — built with Claude Code.

## What It Does

Give a simple command like **"Find me 50 dentists in Dubai"** and get a clean Excel file with:

| Business Name | Phone | Email | Website | Address | Rating | Reviews | Category |
|---|---|---|---|---|---|---|---|
| Bright Smile Dental | +971-4-xxx-xxxx | info@brightsmile.ae | brightsmile.ae | Sheikh Zayed Rd, Dubai | 4.7 | 312 | Dentist |
| Dubai Dental Clinic | +971-4-xxx-xxxx | contact@dubaidental.com | dubaidental.com | Al Wasl Rd, Dubai | 4.5 | 189 | Dental Clinic |

## Architecture

```
User Command (industry + city)
        │
        ▼
Query Builder (generates 2-3 search variations)
        │
        ▼
Scraper (Apify primary / Outscraper fallback)
        │
        ▼
Email Enrichment (Apify contacts / Hunter.io)
        │
        ▼
Clean & Deduplicate (pandas)
        │
        ▼
Export → Excel (.xlsx) / CSV / Google Sheets
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API keys
cp docs/.env.example .env
# Edit .env and add your Apify API token

# 3. Run
python main.py "dentists" "Dubai" --limit 50
python main.py "construction" "Houston, Texas" --limit 100
python main.py "security" "Riyadh" --limit 30
```

## Project Structure

```
├── main.py                 ← Run this
├── requirements.txt
├── .env                    ← Your API keys (not pushed to GitHub)
│
├── src/
│   ├── config.py           ← Loads environment variables
│   ├── scraper.py          ← Apify + Outscraper + Hunter.io
│   ├── query_builder.py    ← Smart search query generation
│   └── exporter.py         ← Excel + CSV + Google Sheets export
│
├── docs/
│   ├── prompt.md           ← Master prompt for the AI agent
│   └── .env.example        ← API key template (copy to .env)
│
├── leads/                  ← Output files go here
└── credentials/            ← Google Sheets JSON (optional)
```

## API Keys Required

| Service | Purpose | Free Tier | Sign Up |
|---------|---------|-----------|---------|
| **Apify** (primary) | Google Maps scraping | $5/mo (~1,000 results) | [apify.com](https://apify.com) |
| **Outscraper** (fallback) | Google Maps scraping | 500 records (one-time) | [outscraper.com](https://app.outscraper.com) |
| **Hunter.io** (optional) | Email enrichment | 25 searches/month | [hunter.io](https://hunter.io) |

> Your `.env` file with real API keys is **never pushed to GitHub** — it's listed in `.gitignore`. Students only see `docs/.env.example` with empty values.

## CLI Options

```bash
python main.py "industry" "location" [options]

Options:
  --limit N          Max leads per query (default: 50)
  --min-rating N     Filter by minimum Google rating (e.g. 4.0)
  --sheets           Also export to Google Sheets
  --sheet-name NAME  Google Sheets tab name
  --scraper TYPE     Force "apify" or "outscraper"
  --no-enrich        Skip Hunter.io email enrichment
```

## Supported Industries

Construction, Interior Design, Dental, Security, Real Estate, HVAC, Plumbing, Electrical, Landscaping, Cleaning, Law Firms, Accounting, Restaurants, Salons, Auto Repair, Veterinary, Photography, Marketing Agencies, IT Services, Gyms — and any custom industry.

## Supported Regions

- **US:** All states and cities
- **Middle East:** UAE, Saudi Arabia, Qatar, Bahrain, Kuwait, Oman, Jordan, Egypt

Middle East cities automatically get country names appended for better search results (e.g., "Dubai" becomes "Dubai, UAE").

## How API Keys Stay Safe

The `.gitignore` file tells Git to ignore sensitive files:

```
.env              ← real API keys — NEVER pushed
credentials/      ← Google service account JSON
leads/*.xlsx      ← scraped data files
leads/*.csv       ← scraped data files
```

Students clone the repo, copy `docs/.env.example` to `.env`, and add their own keys.

---

Built with [Claude Code](https://claude.ai/claude-code) as part of the **Future-Proof AI Automation Bootcamp**.
