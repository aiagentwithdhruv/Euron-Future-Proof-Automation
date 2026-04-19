#!/usr/bin/env python3
"""Seed the pipeline with N fake prospects for end-to-end testing.

Usage:
  python tools/seed_fake_prospects.py --count 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

FAKE_POOL = [
    {"company": "Finch SaaS", "website": "https://finch.example", "contact_name": "Priya Rao", "contact_role": "Founder", "city": "Bengaluru", "country": "India", "linkedin_url": "https://linkedin.com/in/priyarao-fake"},
    {"company": "Lattice Ops", "website": "https://latticeops.example", "contact_name": "Marcus Chen", "contact_role": "CEO", "city": "San Francisco", "country": "USA", "linkedin_url": "https://linkedin.com/in/marcuschen-fake"},
    {"company": "Nimbus Retail", "website": "https://nimbusretail.example", "contact_name": "Sana Khan", "contact_role": "Head of Marketing", "city": "Dubai", "country": "UAE", "linkedin_url": "https://linkedin.com/in/sanakhan-fake"},
    {"company": "Quill Agency", "website": "https://quill.example", "contact_name": "David Park", "contact_role": "Managing Director", "city": "London", "country": "UK", "linkedin_url": "https://linkedin.com/in/davidpark-fake"},
    {"company": "Helios Legal", "website": "https://helioslaw.example", "contact_name": "Ava Rossi", "contact_role": "Partner", "city": "New York", "country": "USA", "linkedin_url": "https://linkedin.com/in/avarossi-fake"},
    {"company": "Mosaic Commerce", "website": "https://mosaic.example", "contact_name": "Rhea Iyer", "contact_role": "Head of Ops", "city": "Mumbai", "country": "India", "linkedin_url": "https://linkedin.com/in/rheaiyer-fake"},
]


def run(count: int) -> list[dict]:
    inserted = []
    for p in FAKE_POOL[:count]:
        saved = state.upsert_prospect({
            **p,
            "source": "seed:fake",
            "source_query": "e2e-test",
            "stage": "scraped",
            "status": "pending_enrich",
            "is_fake": True,
        })
        inserted.append(saved)
    logger.info(f"seeded {len(inserted)} fake prospects")
    return inserted


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Seed fake prospects into the pipeline for testing.")
    ap.add_argument("--count", type=int, default=5)
    args = ap.parse_args()
    out = run(args.count)
    print(json.dumps({
        "status": "success",
        "inserted": len(out),
        "prospect_ids": [p["prospect_id"] for p in out],
    }, indent=2))


if __name__ == "__main__":
    main()
