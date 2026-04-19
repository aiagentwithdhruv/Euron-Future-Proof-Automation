#!/usr/bin/env python3
"""Stage 05 — Generate a prefilled booking link for a prospect.

Primary: Cal.com prefill query params (name, email, notes).
Fallback: raw BOOKING_URL with no prefill.

No API call required to generate — the link itself is deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_url  # noqa: E402

logger = get_logger(__name__)


def run(prospect: dict) -> dict:
    base = env.get("BOOKING_URL", "").strip()
    if not base:
        logger.warning("BOOKING_URL missing; cannot generate link")
        return state.upsert_prospect({**prospect, "booking_link_error": "no_booking_url"})

    try:
        validate_url(base)
    except ValueError as e:
        logger.warning(f"invalid BOOKING_URL: {e}")
        return state.upsert_prospect({**prospect, "booking_link_error": str(e)})

    params = {
        "name": prospect.get("contact_name", ""),
        "email": prospect.get("email", ""),
        "notes": f"From: {prospect.get('source','direct')} | Company: {prospect.get('company','')}",
    }
    params = {k: v for k, v in params.items() if v}
    sep = "&" if "?" in base else "?"
    link = f"{base}{sep}{urlencode(params)}"

    return state.upsert_prospect({**prospect, "booking_link": link})


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 05: booking link")
    ap.add_argument("--prospect-id", required=True)
    args = ap.parse_args()
    p = state.get_prospect(args.prospect_id)
    if not p:
        ap.error(f"No prospect {args.prospect_id}")
    out = run(p)
    print(json.dumps({"status": "success", "booking_link": out.get("booking_link", "")}, indent=2))


if __name__ == "__main__":
    main()
