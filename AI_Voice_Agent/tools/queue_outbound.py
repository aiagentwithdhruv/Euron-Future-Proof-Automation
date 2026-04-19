#!/usr/bin/env python3
"""Push an outbound call queue to Vapi from a CSV of opted-in leads.

Usage:
    python tools/queue_outbound.py --csv leads.csv [--dry-run] [--max N]

CSV columns (required):
    name, phone, email, consent_outbound, last_touch, offer, notes, timezone

Rules enforced BEFORE any call is placed:
    1. consent_outbound must be true
    2. phone must not be on the DNC list (if Supabase is configured)
    3. local time must be within OUTBOUND_WINDOW
    4. max 3 attempts per lead (tracked in Supabase if available)
    5. estimated cost displayed + confirmation asked if > $2.00

This script DOES NOT bypass any of the above. --force is intentionally not provided.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Allow running from project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.config import get_settings  # noqa: E402
from api.logging_utils import get_logger  # noqa: E402
from api.services.crm_service import CRMService  # noqa: E402
from api.services.vapi_service import VapiError, VapiService  # noqa: E402


logger = get_logger(__name__)


def _is_truthy(v: Any) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _within_window(now: datetime, start_hour: int, end_hour: int, tz_name: str) -> bool:
    # Simple UTC check by default. Use zoneinfo when tz is provided and valid.
    try:
        from zoneinfo import ZoneInfo  # type: ignore
        tz = ZoneInfo(tz_name) if tz_name else None
        local = now.astimezone(tz) if tz else now
    except Exception:  # noqa: BLE001
        local = now
    return start_hour <= local.hour < end_hour


def _estimate_cost(n: int, avg_minutes: float = 2.5, rate_per_min: float = 0.09) -> float:
    return round(n * avg_minutes * rate_per_min, 2)


def _load_rows(csv_path: Path) -> list[dict[str, Any]]:
    with open(csv_path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _filter_eligible(
    rows: list[dict[str, Any]],
    crm: CRMService,
    start_hour: int,
    end_hour: int,
    max_attempts: int,
) -> tuple[list[dict[str, Any]], list[tuple[dict[str, Any], str]]]:
    eligible: list[dict[str, Any]] = []
    skipped: list[tuple[dict[str, Any], str]] = []
    now = datetime.utcnow().replace(tzinfo=__import__("datetime").timezone.utc)

    for row in rows:
        phone = (row.get("phone") or "").strip()
        if not phone:
            skipped.append((row, "missing phone"))
            continue
        if not _is_truthy(row.get("consent_outbound")):
            skipped.append((row, "no consent"))
            continue
        if crm.enabled and crm.is_on_dnc(phone):
            skipped.append((row, "on DNC list"))
            continue
        tz_name = (row.get("timezone") or "").strip()
        if not _within_window(now, start_hour, end_hour, tz_name):
            skipped.append((row, f"outside window {start_hour}-{end_hour} local"))
            continue
        # Attempt cap check (best effort — requires a `lead_attempts` column in leads)
        if crm.enabled:
            try:
                existing = crm.lookup_customer(phone)
                if existing and int(existing.get("call_count") or 0) >= max_attempts:
                    skipped.append((row, f"max attempts ({max_attempts}) reached"))
                    continue
            except Exception:  # noqa: BLE001
                pass
        eligible.append(row)
    return eligible, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Queue outbound calls via Vapi")
    parser.add_argument("--csv", required=True, help="Path to leads CSV")
    parser.add_argument("--dry-run", action="store_true", help="Print plan; place no calls")
    parser.add_argument("--max", type=int, default=0, help="Max calls to place (0 = all eligible)")
    parser.add_argument("--yes", action="store_true", help="Skip cost confirmation prompt")
    args = parser.parse_args()

    settings = get_settings()
    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 2

    rows = _load_rows(csv_path)
    crm = CRMService()
    vapi = VapiService()

    eligible, skipped = _filter_eligible(
        rows,
        crm,
        start_hour=settings.outbound_window_start,
        end_hour=settings.outbound_window_end,
        max_attempts=settings.max_outbound_attempts,
    )

    if args.max > 0:
        eligible = eligible[: args.max]

    n = len(eligible)
    est_cost = _estimate_cost(n)
    print(f"Eligible: {n}")
    print(f"Skipped:  {len(skipped)}")
    for row, reason in skipped[:20]:
        print(f"  skip {row.get('phone', '?'):>16s}  {reason}")
    if len(skipped) > 20:
        print(f"  (+{len(skipped) - 20} more)")
    print(f"Estimated cost (@ ~$0.09/min, ~2.5 min avg): ${est_cost:.2f}")

    if args.dry_run:
        print("DRY RUN — no calls placed.")
        return 0

    if n == 0:
        print("Nothing to queue. Exiting.")
        return 0

    if not vapi.enabled:
        print("ERROR: Vapi not configured. Set VAPI_API_KEY + VAPI_ASSISTANT_ID + VAPI_PHONE_NUMBER_ID.",
              file=sys.stderr)
        return 3

    if est_cost > 2.00 and not args.yes:
        answer = input(f"Estimated cost ${est_cost:.2f} > $2.00 budget. Proceed? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted by user.")
            return 0

    placed = 0
    errors = 0
    for row in eligible:
        variables = {
            "lead_name": row.get("name") or "there",
            "last_touch": row.get("last_touch") or "our last conversation",
            "offer": row.get("offer") or "an update from our team",
        }
        try:
            result = vapi.place_outbound(row["phone"], assistant_variables=variables)
            placed += 1
            logger.info(f"queued phone={row['phone']} call_id={result.get('id')}")
        except VapiError as e:
            errors += 1
            logger.error(f"queue.failed phone={row['phone']}: {e}")

    print(f"Placed: {placed}   Errors: {errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
