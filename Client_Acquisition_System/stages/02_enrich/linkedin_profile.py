#!/usr/bin/env python3
"""Stage 02 — Attach a LinkedIn URL + role/bio snippet to the prospect.

Policy: NEVER scrape LinkedIn directly (ToS). We rely on:
  1. linkedin_url already present on the prospect (from Apollo export / Sales Nav)
  2. Apollo people_match to resolve it from name + domain
  3. Otherwise, leave it blank — the copywriter falls back to website context.

Bio snippet: pulled from Apollo's `headline` field when available.
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


def _apollo_match(domain: str, name: str) -> dict:
    key = env.get("APOLLO_API_KEY")
    if not key or not name or not domain:
        return {}
    import requests

    first, *rest = name.split()
    last = " ".join(rest) or ""
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/people/match",
            json={"api_key": key, "first_name": first, "last_name": last, "domain": domain},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Apollo match error: {e}")
        return {}
    p = resp.json().get("person") or {}
    return {
        "linkedin_url": p.get("linkedin_url") or "",
        "headline": p.get("headline") or "",
        "title": p.get("title") or "",
    }


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    if prospect.get("linkedin_url") and prospect.get("bio_summary"):
        return prospect

    if dry_run:
        name_slug = (prospect.get("contact_name") or "prospect").lower().split()[0]
        merged = {
            **prospect,
            "linkedin_url": prospect.get("linkedin_url") or f"https://linkedin.com/in/{name_slug}-dryrun",
            "bio_summary": prospect.get("bio_summary") or f"[DRY-RUN] {prospect.get('contact_role','Leader')} at {prospect.get('company','Company')}",
        }
        return state.upsert_prospect(merged)

    domain = safe_domain(prospect.get("website", ""))
    info = _apollo_match(domain, prospect.get("contact_name", ""))
    merged = {
        **prospect,
        "linkedin_url": prospect.get("linkedin_url") or info.get("linkedin_url", ""),
        "bio_summary": prospect.get("bio_summary") or info.get("headline") or info.get("title", ""),
    }
    if merged["linkedin_url"]:
        logger.info(f"linkedin_url resolved for {pid}", extra={"prospect_id": pid})
    return state.upsert_prospect(merged)


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 02: linkedin profile")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-pending", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_pending:
        todo = state.prospects_where(status="pending_enrich")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-pending")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    for p in todo:
        run(p, dry_run=dry)
    print(json.dumps({"status": "success", "dry_run": dry, "processed": len(todo)}, indent=2))


if __name__ == "__main__":
    main()
