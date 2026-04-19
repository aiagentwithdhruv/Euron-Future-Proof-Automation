#!/usr/bin/env python3
"""Stage 01 — LinkedIn prospect search.

NOTE: LinkedIn's ToS forbids unauthorized scraping. In production this wraps a
licensed data provider (Apollo Search, Lusha, LinkedIn Sales Navigator via
legitimate SDK, etc.). Here we implement:
  - Apollo People Search (preferred; uses API)
  - Fallback: fake prospects for dry-run / testing

Usage:
  python stages/01_scrape/linkedin_search.py --role Founder --industry SaaS --location "United States" --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import safe_domain  # noqa: E402

logger = get_logger(__name__)

APOLLO_SEARCH_URL = "https://api.apollo.io/v1/mixed_people/search"


def _fake(role: str, industry: str, location: str, limit: int) -> list[dict]:
    base = [
        {"company": "Finch SaaS", "website": "https://finch.example", "contact_name": "Priya Rao", "contact_role": "Founder", "linkedin_url": "https://linkedin.com/in/priyarao"},
        {"company": "Lattice Ops", "website": "https://latticeops.example", "contact_name": "Marcus Chen", "contact_role": "CEO", "linkedin_url": "https://linkedin.com/in/marcuschen"},
        {"company": "Nimbus Retail", "website": "https://nimbusretail.example", "contact_name": "Sana Khan", "contact_role": "Head of Marketing", "linkedin_url": "https://linkedin.com/in/sanakhan"},
        {"company": "Quill Agency", "website": "https://quill.example", "contact_name": "David Park", "contact_role": "Managing Director", "linkedin_url": "https://linkedin.com/in/davidpark"},
        {"company": "Helios Legal", "website": "https://helioslaw.example", "contact_name": "Ava Rossi", "contact_role": "Partner", "linkedin_url": "https://linkedin.com/in/avarossi"},
    ]
    out = []
    for b in base[:limit]:
        out.append({
            **b,
            "city": location,
            "country": location,
            "source": "linkedin_search:fake",
            "source_query": f"{role} | {industry} | {location}",
            "is_fake": True,
        })
    return out


def _apollo_search(role: str, industry: str, location: str, limit: int) -> list[dict]:
    key = env.get("APOLLO_API_KEY")
    if not key:
        return []
    import requests

    payload = {
        "api_key": key,
        "q_organization_domains": None,
        "person_titles": [role],
        "person_locations": [location],
        "organization_industry_tag_ids": None,  # Apollo uses tag IDs; simpler to rely on keywords
        "q_keywords": industry,
        "page": 1,
        "per_page": min(limit, 25),
    }
    try:
        resp = requests.post(APOLLO_SEARCH_URL, json=payload, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Apollo search failed: {e}")
        return []
    data = resp.json()
    people = data.get("people", []) or data.get("contacts", [])
    out = []
    for p in people[:limit]:
        org = p.get("organization") or {}
        out.append({
            "company": org.get("name", ""),
            "website": org.get("website_url", ""),
            "contact_name": p.get("name") or f'{p.get("first_name","")} {p.get("last_name","")}'.strip(),
            "contact_role": p.get("title", ""),
            "linkedin_url": p.get("linkedin_url", ""),
            "email": p.get("email") or "",
            "city": p.get("city", ""),
            "country": p.get("country", ""),
            "source": "linkedin_search:apollo",
            "source_query": f"{role} | {industry} | {location}",
        })
    return out


def run(role: str, industry: str, location: str, limit: int = 25, dry_run: bool = False) -> list[dict]:
    if dry_run:
        prospects = _fake(role, industry, location, limit)
    else:
        prospects = _apollo_search(role, industry, location, limit)
        if not prospects:
            logger.warning("No Apollo key or empty results; using fake prospects.")
            prospects = _fake(role, industry, location, limit)

    existing = state.load_pipeline()
    existing_domains = {safe_domain(p.get("website", "")) for p in existing.values() if p.get("website")}

    inserted = []
    for p in prospects:
        domain = safe_domain(p.get("website", ""))
        if domain and domain in existing_domains:
            continue
        saved = state.upsert_prospect({**p, "stage": "scraped", "status": "pending_enrich"})
        inserted.append(saved)
        if domain:
            existing_domains.add(domain)

    logger.info(f"inserted {len(inserted)} prospects from linkedin_search", extra={"stage": "01_scrape"})
    return inserted


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 01: LinkedIn / Apollo people search")
    ap.add_argument("--role", required=True)
    ap.add_argument("--industry", required=True)
    ap.add_argument("--location", required=True)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)
    out = run(args.role, args.industry, args.location, args.limit, dry_run=dry)
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "inserted": len(out),
        "prospect_ids": [p["prospect_id"] for p in out],
    }, indent=2))


if __name__ == "__main__":
    main()
