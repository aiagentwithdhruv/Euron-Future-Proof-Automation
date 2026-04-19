#!/usr/bin/env python3
"""Stage 01 — Apollo CSV export importer.

Apollo's free tier (50 credits) + large exports are the fastest way to get
firmographically-filtered B2B lists. Export from Apollo UI -> CSV -> pass to
this tool.

Usage:
  python stages/01_scrape/apollo_export.py --csv /path/to/apollo_export.csv
  python stages/01_scrape/apollo_export.py --csv ... --limit 10 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import safe_domain  # noqa: E402

logger = get_logger(__name__)

APOLLO_FIELD_MAP = {
    "company": ["Company", "Organization", "Company Name"],
    "website": ["Website", "Company Website", "Website URL"],
    "contact_name": ["Full Name", "Name", "Contact"],
    "contact_role": ["Title", "Job Title"],
    "email": ["Email", "Work Email", "Personal Email"],
    "linkedin_url": ["Person LinkedIn URL", "LinkedIn URL", "LinkedIn"],
    "city": ["City", "Person City"],
    "country": ["Country", "Person Country"],
    "phone": ["Mobile Phone", "Work Phone", "Phone"],
}


def _pick(row: dict, keys: list[str]) -> str:
    for k in keys:
        if row.get(k):
            return str(row[k]).strip()
    return ""


def run(csv_path: str, limit: int | None = None, dry_run: bool = False) -> list[dict]:
    path = Path(csv_path).expanduser().resolve()
    if not path.exists():
        if dry_run:
            logger.warning(f"CSV not found at {path}; emitting fake Apollo-like rows.")
            return _fake(limit or 5, dry_run)
        raise FileNotFoundError(f"No CSV at {path}")

    prospects: list[dict] = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            prospects.append({
                "company": _pick(row, APOLLO_FIELD_MAP["company"]),
                "website": _pick(row, APOLLO_FIELD_MAP["website"]),
                "contact_name": _pick(row, APOLLO_FIELD_MAP["contact_name"]),
                "contact_role": _pick(row, APOLLO_FIELD_MAP["contact_role"]),
                "email": _pick(row, APOLLO_FIELD_MAP["email"]),
                "linkedin_url": _pick(row, APOLLO_FIELD_MAP["linkedin_url"]),
                "city": _pick(row, APOLLO_FIELD_MAP["city"]),
                "country": _pick(row, APOLLO_FIELD_MAP["country"]),
                "phone": _pick(row, APOLLO_FIELD_MAP["phone"]),
                "source": "apollo_export",
                "source_query": str(path.name),
            })
            if limit and len(prospects) >= limit:
                break

    existing = state.load_pipeline()
    existing_domains = {safe_domain(p.get("website", "")) for p in existing.values() if p.get("website")}

    inserted = []
    for p in prospects:
        if not p.get("company"):
            continue
        domain = safe_domain(p.get("website", ""))
        if domain and domain in existing_domains:
            continue
        saved = state.upsert_prospect({**p, "stage": "scraped", "status": "pending_enrich"})
        inserted.append(saved)
        if domain:
            existing_domains.add(domain)

    logger.info(f"imported {len(inserted)} prospects from apollo_export", extra={"stage": "01_scrape"})
    return inserted


def _fake(limit: int, dry_run: bool) -> list[dict]:
    base = [
        {"company": "Mosaic Commerce", "website": "https://mosaic.example", "contact_name": "Rhea Iyer", "contact_role": "Head of Ops", "email": "", "linkedin_url": "https://linkedin.com/in/rheaiyer", "city": "Mumbai", "country": "India"},
        {"company": "Fable Legal", "website": "https://fablelegal.example", "contact_name": "Jon Weaver", "contact_role": "Partner", "email": "", "linkedin_url": "https://linkedin.com/in/jonweaver", "city": "New York", "country": "USA"},
    ]
    out = []
    existing = state.load_pipeline()
    existing_domains = {safe_domain(p.get("website", "")) for p in existing.values() if p.get("website")}
    for b in base[:limit]:
        domain = safe_domain(b["website"])
        if domain in existing_domains:
            continue
        saved = state.upsert_prospect({
            **b, "source": "apollo_export:fake", "stage": "scraped", "status": "pending_enrich", "is_fake": True,
        })
        out.append(saved)
        existing_domains.add(domain)
    return out


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 01: Apollo CSV import")
    ap.add_argument("--csv", required=False, default="")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)
    out = run(args.csv, args.limit, dry_run=dry)
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "inserted": len(out),
        "prospect_ids": [p["prospect_id"] for p in out],
    }, indent=2))


if __name__ == "__main__":
    main()
