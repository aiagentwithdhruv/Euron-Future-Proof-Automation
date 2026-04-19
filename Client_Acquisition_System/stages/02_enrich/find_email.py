#!/usr/bin/env python3
"""Stage 02 — Find verified email for a prospect.

Order:
  1. If prospect already has email -> keep it
  2. Try Hunter.io domain + first/last name search
  3. Fall back to Apollo people lookup (people_match API)
  4. Cache results per domain in state/enrich_cache.json
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
from shared.sanitize import safe_domain, validate_email  # noqa: E402

logger = get_logger(__name__)


def _hunter(domain: str, first: str = "", last: str = "") -> dict:
    key = env.get("HUNTER_API_KEY")
    if not key:
        return {}
    import requests

    params = {"domain": domain, "api_key": key}
    if first and last:
        params.update({"first_name": first, "last_name": last})
        url = "https://api.hunter.io/v2/email-finder"
    else:
        url = "https://api.hunter.io/v2/domain-search"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Hunter error for {domain}: {e}")
        return {}
    data = resp.json().get("data", {})
    if "email" in data:
        return {"email": data.get("email", ""), "confidence": data.get("score", 0), "source": "hunter:finder"}
    emails = data.get("emails") or []
    if emails:
        top = emails[0]
        return {"email": top.get("value", ""), "confidence": top.get("confidence", 0), "source": "hunter:domain"}
    return {}


def _apollo(domain: str, name: str) -> dict:
    key = env.get("APOLLO_API_KEY")
    if not key or not name:
        return {}
    import requests

    first, *rest = name.split()
    last = " ".join(rest) or ""
    payload = {
        "api_key": key,
        "first_name": first,
        "last_name": last,
        "domain": domain,
        "reveal_personal_emails": False,
    }
    try:
        resp = requests.post("https://api.apollo.io/v1/people/match", json=payload, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Apollo error: {e}")
        return {}
    data = resp.json().get("person") or {}
    email = data.get("email") or ""
    if not email:
        return {}
    return {"email": email, "confidence": 80, "source": "apollo:match"}


def run(prospect: dict, dry_run: bool = False) -> dict:
    """Enrich a single prospect with email. Mutates state. Returns updated record."""
    pid = prospect["prospect_id"]
    if prospect.get("email"):
        return state.upsert_prospect({**prospect, "email_confidence": prospect.get("email_confidence", 90)})

    domain = safe_domain(prospect.get("website", ""))
    if not domain:
        logger.info(f"no domain for {pid}, cannot enrich email", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "email_confidence": 0})

    cached = state.cache_get(domain)
    if cached and cached.get("email"):
        return state.upsert_prospect({
            **prospect,
            "email": cached["email"],
            "email_confidence": cached.get("confidence", 0),
            "email_source": cached.get("source"),
        })

    if dry_run:
        # Deterministic stub — e.g., first.last@domain
        first, *rest = (prospect.get("contact_name") or "test contact").split()
        last = rest[-1] if rest else "lead"
        fake_email = f"{first.lower()}.{last.lower()}@{domain}".replace(" ", "")
        enriched = {"email": fake_email, "confidence": 75, "source": "dry_run:stub"}
    else:
        first, *rest = (prospect.get("contact_name") or "").split()
        last = rest[-1] if rest else ""
        enriched = _hunter(domain, first, last)
        if not enriched.get("email"):
            enriched = _apollo(domain, prospect.get("contact_name", ""))

    if enriched.get("email"):
        try:
            email = validate_email(enriched["email"])
        except ValueError:
            email = ""
        if email:
            state.cache_set(domain, enriched)
            return state.upsert_prospect({
                **prospect,
                "email": email,
                "email_confidence": enriched.get("confidence", 0),
                "email_source": enriched.get("source", ""),
            })

    return state.upsert_prospect({**prospect, "email_confidence": 0})


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 02: find email")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-pending", action="store_true", help="Process every pending_enrich prospect")
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

    out = [run(p, dry_run=dry) for p in todo]
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "enriched": len([p for p in out if p.get("email")]),
        "total": len(out),
    }, indent=2))


if __name__ == "__main__":
    main()
