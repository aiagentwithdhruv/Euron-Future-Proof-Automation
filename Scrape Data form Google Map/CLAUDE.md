# Google Maps Lead Scraper — AI Agent Automation

## Project Overview
An AI-powered lead scraping automation that extracts business data from Google Maps for any industry (construction, dental, interior design, security, etc.) across US and Middle East regions. The agent takes a simple command like "Find 100 dentists in Dubai" and returns a clean, enriched lead list.

## Architecture

```
User Command (industry + city)
        |
        v
Query Builder (Claude generates optimized search strings)
        |
        v
Scraper Engine (Apify primary, Outscraper fallback)
        |
        v
Email Enrichment (Apify contact scraper OR Hunter.io)
        |
        v
Deduplication & Cleaning (pandas)
        |
        v
Output: Excel + CSV + Google Sheets
```

## Tech Stack
- **Language:** Python 3.11+
- **Primary Scraper:** Apify (`compass/crawler-google-places`) — faster, 50+ data fields, monthly free credits
- **Fallback Scraper:** Outscraper API — simpler SDK, good for quick one-off exports
- **Email Enrichment:** Apify contact scraper add-on + Hunter.io as fallback
- **Output:** Excel (.xlsx) + CSV files + Google Sheets (via gspread)
- **Config:** `.env` file for all API keys
- **Agent Logic:** Claude Code as the orchestrator

## Scraper Comparison (Why Apify is Primary)

| Factor | Apify (Primary) | Outscraper (Fallback) |
|--------|-----------------|----------------------|
| Free tier | $5/mo credits (~1,000 results), renews monthly | 500 results one-time |
| Cost per 1,000 leads | ~$4 base | ~$3 base |
| With email enrichment | ~$6 per 1,000 | ~$6 per 1,000 |
| Data fields | 50+ (popular times, price bracket, etc.) | ~25-30 |
| Speed | Fast (parallel, cloud-scaled) | Slow (~25 min per 400 results) |
| Best for | Recurring automation pipelines | Quick one-off exports |

## Key Dependencies
```
apify-client        # Primary Google Maps scraper
outscraper          # Fallback scraper
pyhunter            # Email enrichment fallback
gspread             # Google Sheets export
google-auth         # Google Sheets authentication
pandas              # Data cleaning & dedup
python-dotenv       # API key management
openpyxl            # Professional Excel export
```

## File Structure
```
Scrape Data form Google Map/
├── CLAUDE.md                  # This file — project rules & context
├── main.py                    # CLI entry point (run this)
├── requirements.txt           # Python dependencies
├── .env                       # Your API keys (gitignored)
│
├── src/                       # Source code
│   ├── __init__.py
│   ├── config.py              # Load env vars + constants
│   ├── scraper.py             # Apify + Outscraper + Hunter.io
│   ├���─ query_builder.py       # Smart search query generation
│   └── exporter.py            # Excel + CSV + Google Sheets export + cleaning
│
├── docs/                      # Documentation
│   ├── prompt.md              # Master prompt for the agent
│   └── .env.example           # Template for API keys
│
├── leads/                     # Output CSV/Excel files (gitignored)
└── credentials/               # Google Sheets service account JSON (gitignored)
```

## How It Works

### Step 1: Query Building
The agent generates Google Maps search queries based on user input:
- Input: `"dentists in Dubai"`
- Generated queries: `["dental clinics Dubai UAE", "dentist Dubai UAE", "dental care Dubai UAE"]`

### Step 2: Scraping
**Apify (primary)** — runs `compass/crawler-google-places` actor:
- 50+ fields per business: name, phone, website, full address, rating, reviews, hours, popular times, price bracket, coordinates, place ID, Google Maps URL, category
- Enable `scrapeContacts: True` for built-in email/social extraction (+$0.002/place)
- Parallel execution — handles hundreds of results in minutes

**Outscraper (fallback)** — use when Apify is unavailable or for quick tests:
- 25-30 fields per business
- Simpler API, fewer config options
- Async queue model (slower on large batches)

### Step 3: Email Enrichment
For businesses with a website but no email:
1. Apify's contact details add-on crawls the website automatically
2. Fallback: Hunter.io domain search for the website domain

### Step 4: Cleaning & Export
- Deduplicate by phone number + website
- Remove entries with no phone AND no email
- Export to professional Excel (.xlsx) with formatted headers, alternating rows, auto-filters
- Also export to CSV in `leads/` folder
- Optionally push to Google Sheets

## API Pricing Reference

| Service | Free Tier | Paid Rate |
|---------|-----------|-----------|
| Apify Maps Scraper | $5/mo credits (~1,000 results) | ~$4 per 1,000 results |
| Apify Contact Enrichment | included in credits | +$2 per 1,000 results |
| Outscraper Maps | 500 records (one-time) | ~$3 per 1,000 records |
| Outscraper Email | included in enrichment | ~$3 per 1,000 extra |
| Hunter.io | 25 searches/month | $34/mo for 500 searches |
| Google Sheets API | Free (with service account) | Free |

## Commands for Claude Code

When working on this project, follow these rules:

1. **Always use `.env` for secrets** — never hardcode API keys
2. **Use Apify as primary scraper** — fall back to Outscraper only if Apify key is missing or fails
3. **Test with small batches first** — use `limit=5` during development
4. **Handle async results** — Apify runs are async, poll `client.run()` for completion
5. **Log everything** — print progress (querying, enriching, exporting) so user sees status
6. **Output files to `leads/` folder** — filename format: `{industry}_{city}_{date}.xlsx`
7. **Keep functions modular** — each file does one thing
8. **Middle East support** — always include country name in queries (UAE, Saudi Arabia, Qatar, etc.)

## Supported Regions
- **US:** All states and cities
- **Middle East:** UAE, Saudi Arabia, Qatar, Bahrain, Kuwait, Oman, Jordan, Egypt

## Supported Industries (Examples)
Construction, Interior Design, Dental/Dentist, Security Companies, Real Estate, HVAC, Plumbing, Electrical, Landscaping, Cleaning Services, Legal/Law Firms, Accounting, Restaurants, Salons/Spas, Auto Repair, Veterinary, Photography, Marketing Agencies, IT Services, Fitness/Gym
