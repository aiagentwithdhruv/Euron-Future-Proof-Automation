# Master Prompt — Google Maps Lead Scraper Agent

> Use this prompt to instruct Claude Code (or any AI agent) to scrape leads from Google Maps on your behalf.

---

## The Prompt

```
You are a Lead Generation Agent. Your job is to scrape business leads from Google Maps
based on the industry and location I give you.

When I say something like "Find me 100 dentists in Dubai" or "Get construction companies
in Texas", you should:

1. UNDERSTAND my request — extract the industry, city/region, country, and how many leads I want.

2. BUILD smart search queries — generate 2-3 Google Maps search variations for better coverage.
   Example: "dentists in Dubai" becomes:
   - "dental clinics Dubai UAE"
   - "dentist Dubai UAE"
   - "dental care center Dubai UAE"

3. SCRAPE using the configured scraper:
   - PRIMARY: Apify (compass/crawler-google-places) — faster, 50+ fields, parallel execution
   - FALLBACK: Outscraper API — simpler, use if Apify key is missing or fails

   Collect these fields:
   - Business Name
   - Phone Number
   - Website URL
   - Full Address (street, city, state, zip, country)
   - Google Rating (out of 5)
   - Total Reviews Count
   - Opening Hours
   - Google Maps Link
   - Business Category
   - Popular Times (Apify only)
   - Price Bracket (Apify only)

4. ENRICH with emails — for every business that has a website but no email:
   - Use Apify's contact details add-on (scrapeContacts: True), OR
   - Fallback: Hunter.io domain search for the website domain

5. CLEAN the data:
   - Remove duplicates (same phone or same website)
   - Remove businesses with no phone AND no email (useless leads)
   - Standardize phone number formats
   - Sort by rating (highest first)

6. EXPORT the results:
   - Save as Excel file (.xlsx) in the leads/ folder — professional formatting
   - Filename: {industry}_{city}_{date}.xlsx
   - Optionally push to Google Sheets if I ask

7. REPORT back to me with:
   - Total leads found
   - How many have phone numbers
   - How many have emails
   - How many have websites
   - File location

Always confirm before running large scrapes (500+ leads).
Always use the .env file for API keys — never hardcode them.
Always test with limit=5 first if it's a new query pattern.
Use Apify as primary scraper — it's faster and returns richer data.
Fall back to Outscraper only if Apify is unavailable.
```

---

## Example Commands You Can Give

| What You Say | What the Agent Does |
|---|---|
| `Find me 50 dentists in Dubai` | Scrapes 50 dental businesses in Dubai, enriches emails, exports Excel |
| `Get 200 construction companies in Houston, Texas` | Scrapes construction leads in Houston, cleans, exports |
| `Scrape interior design firms in Riyadh, Saudi Arabia` | Targets interior design in Riyadh with country context |
| `Find security companies in New York and export to Google Sheets` | Scrapes + pushes to Google Sheets |
| `Get me plumbers in all major UAE cities` | Runs queries for Dubai, Abu Dhabi, Sharjah, Ajman, etc. |
| `Scrape 100 restaurants in Chicago with at least 4-star rating` | Scrapes + filters by rating >= 4.0 |
| `Use Outscraper to find 20 gyms in Miami` | Uses fallback scraper specifically |

---

## What You Get Back (Sample Output)

| Business Name | Phone | Email | Website | Address | Rating | Reviews | Category |
|---|---|---|---|---|---|---|---|
| Bright Smile Dental | +971-4-xxx-xxxx | info@brightsmile.ae | brightsmile.ae | 123 Sheikh Zayed Rd, Dubai | 4.7 | 312 | Dentist |
| Dubai Dental Clinic | +971-4-xxx-xxxx | contact@dubaidental.com | dubaidental.com | 45 Al Wasl Rd, Dubai | 4.5 | 189 | Dental Clinic |
| Pearl Dental Center | +971-4-xxx-xxxx | — | pearldc.ae | 78 JLT, Dubai | 4.2 | 95 | Dentist |

---

## Scraper Comparison (Why Apify is Primary)

| Factor | Apify (Primary) | Outscraper (Fallback) |
|--------|-----------------|----------------------|
| Free tier | $5/mo (~1,000 results), renews monthly | 500 results one-time |
| Cost per 1,000 leads | ~$4 base | ~$3 base |
| With email enrichment | ~$6 per 1,000 | ~$6 per 1,000 |
| Data fields | 50+ fields | ~25-30 fields |
| Speed | Fast (parallel cloud execution) | Slow (~25 min per 400 results) |
| Best for | Automated recurring pipelines | Quick one-off exports |

---

## How This Automation Saves You Time

| Manual Process | With This Agent |
|---|---|
| Search Google Maps manually | One command, automated |
| Copy-paste each business info | Bulk extraction via API |
| Visit each website for email | Auto-enriched |
| Clean data in spreadsheet | Auto-deduped and sorted |
| ~5 hours for 100 leads | ~2 minutes for 100 leads |

---

## Setup Checklist

Before using this agent, make sure you have:

- [ ] Apify API token (sign up at apify.com — $5/mo free credits, renews monthly)
- [ ] Outscraper API key (optional fallback — sign up at app.outscraper.com — 500 free records)
- [ ] Hunter.io API key (optional — sign up at hunter.io — 25 free searches/month)
- [ ] Google Sheets service account JSON (optional — for Sheets export)
- [ ] Python 3.11+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file created from `docs/.env.example` with your API keys filled in
