#!/usr/bin/env python3
"""Stage 01 — Google Maps scraper.

Uses Apify primary, Outscraper fallback. Normalizes to prospect schema.

Usage:
  python stages/01_scrape/google_maps.py --query "dental clinics Dubai UAE" --limit 10
  python stages/01_scrape/google_maps.py --query "..." --limit 5 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Support running as `python stages/01_scrape/google_maps.py`
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import safe_domain  # noqa: E402

logger = get_logger(__name__)


def _fake_prospects(query: str, limit: int) -> list[dict]:
    base = [
        {"company": "Acme Dental", "website": "https://acmedental.example", "phone": "+971 4 111 1111", "city": "Dubai", "country": "UAE", "contact_name": "Dr. Ali Khan", "contact_role": "Owner"},
        {"company": "Brightsmile Studio", "website": "https://brightsmile.example", "phone": "+971 4 222 2222", "city": "Dubai", "country": "UAE", "contact_name": "Dr. Noor Ahmed", "contact_role": "Founder"},
        {"company": "Desert Pearl Clinic", "website": "https://desertpearl.example", "phone": "+971 4 333 3333", "city": "Dubai", "country": "UAE", "contact_name": "Dr. Hamid Said", "contact_role": "Director"},
        {"company": "Oasis Care Dental", "website": "https://oasiscare.example", "phone": "+971 4 444 4444", "city": "Dubai", "country": "UAE", "contact_name": "Dr. Mariam Qasim", "contact_role": "Principal"},
        {"company": "Skyline Dental Group", "website": "https://skylinedental.example", "phone": "+971 4 555 5555", "city": "Dubai", "country": "UAE", "contact_name": "Dr. Omar Farooq", "contact_role": "CEO"},
    ]
    out = []
    for i, b in enumerate(base[:limit]):
        out.append({
            **b,
            "source": "google_maps",
            "source_query": query,
            "is_fake": True,
        })
    return out


def _apify(query: str, limit: int) -> list[dict]:
    token = env.get("APIFY_API_TOKEN")
    if not token:
        return []
    try:
        from apify_client import ApifyClient
    except ImportError:
        logger.warning("apify-client not installed; skipping Apify")
        return []
    client = ApifyClient(token)
    run_input = {
        "searchStringsArray": [query],
        "maxCrawledPlacesPerSearch": limit,
        "language": "en",
        "scrapeContacts": True,
    }
    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    out = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        emails = item.get("emails") or ([item["email"]] if item.get("email") else [])
        out.append({
            "company": item.get("title", ""),
            "website": item.get("website", ""),
            "phone": item.get("phone", ""),
            "email": emails[0] if emails else "",
            "all_emails": emails,
            "city": item.get("city", ""),
            "country": item.get("countryCode", ""),
            "contact_name": "",
            "contact_role": "",
            "address": item.get("address", ""),
            "rating": item.get("totalScore"),
            "reviews_count": item.get("reviewsCount", 0),
            "category": item.get("categoryName", ""),
            "google_maps_url": item.get("url", ""),
            "place_id": item.get("placeId", ""),
            "source": "google_maps:apify",
            "source_query": query,
        })
    return out


def _outscraper(query: str, limit: int) -> list[dict]:
    key = env.get("OUTSCRAPER_API_KEY")
    if not key:
        return []
    try:
        from outscraper import ApiClient
    except ImportError:
        logger.warning("outscraper not installed; skipping Outscraper")
        return []
    client = ApiClient(api_key=key)
    results = client.google_maps_search([query], limit=limit, language="en")
    flat: list[dict] = []
    for r in results:
        if isinstance(r, list):
            flat.extend(r)
        elif isinstance(r, dict):
            flat.append(r)
    return [
        {
            "company": r.get("name", ""),
            "website": r.get("site") or r.get("website", ""),
            "phone": r.get("phone", ""),
            "email": r.get("email", "") or "",
            "city": r.get("city", ""),
            "country": r.get("country", ""),
            "contact_name": "",
            "contact_role": "",
            "address": r.get("full_address") or r.get("address", ""),
            "rating": r.get("rating"),
            "reviews_count": r.get("reviews", 0),
            "category": r.get("category") or r.get("type", ""),
            "google_maps_url": r.get("google_maps_url", ""),
            "place_id": r.get("place_id", ""),
            "source": "google_maps:outscraper",
            "source_query": query,
        }
        for r in flat
    ]


def run(query: str, limit: int = 25, dry_run: bool = False) -> list[dict]:
    """Scrape + dedupe + upsert to pipeline. Returns inserted prospects."""
    if dry_run:
        prospects = _fake_prospects(query, limit)
    else:
        prospects = _apify(query, limit) or _outscraper(query, limit)
        if not prospects:
            logger.warning("No scraper keys configured; falling back to fake prospects.")
            prospects = _fake_prospects(query, limit)

    # Dedupe by domain + phone against existing pipeline
    existing = state.load_pipeline()
    existing_domains = {
        safe_domain(p.get("website", "")) for p in existing.values() if p.get("website")
    }
    existing_phones = {p.get("phone") for p in existing.values() if p.get("phone")}

    inserted = []
    for p in prospects:
        domain = safe_domain(p.get("website", ""))
        if domain and domain in existing_domains:
            continue
        if p.get("phone") and p["phone"] in existing_phones:
            continue
        record = {
            **p,
            "stage": "scraped",
            "status": "pending_enrich",
        }
        saved = state.upsert_prospect(record)
        inserted.append(saved)
        if domain:
            existing_domains.add(domain)
        if p.get("phone"):
            existing_phones.add(p["phone"])

    logger.info(f"scraped {len(inserted)} new prospects from google_maps", extra={"stage": "01_scrape"})
    return inserted


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 01: scrape Google Maps")
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)
    out = run(args.query, args.limit, dry_run=dry)
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "inserted": len(out),
        "prospect_ids": [p["prospect_id"] for p in out],
    }, indent=2))


if __name__ == "__main__":
    main()
