#!/usr/bin/env python3
"""Stage 04 — Schedule follow-ups (day 3, 7, 14) for a contacted prospect.

This tool DOES NOT send; it writes a schedule entry to state/followups.json
that `tools/run_pipeline.py --stage followups` processes on subsequent runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state, llm  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

SCHEDULE_PATH = PROJECT_ROOT / "state" / "followups.json"
SCHEDULE_PATH.parent.mkdir(exist_ok=True)

DAY_OFFSETS = [3, 7, 14]

FOLLOWUP_SYSTEM = """You write short B2B follow-ups that feel human. Each one has a distinct tone.
No "just checking in." Ever.

Variants:
- Day 3: "bumping this up" (40-60 words, new angle)
- Day 7: value-add (70-100 words, one specific insight)
- Day 14: break-up email (30-50 words, permission-to-close)

Return JSON: {"subject": "...", "body": "..."}"""


def _load_schedule() -> list[dict]:
    if not SCHEDULE_PATH.exists():
        return []
    return json.loads(SCHEDULE_PATH.read_text())


def _save_schedule(data: list[dict]) -> None:
    tmp = SCHEDULE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(SCHEDULE_PATH)


def _build_user(prospect: dict, prior_subject: str, prior_body: str, days_since: int) -> str:
    return (
        "### Prior email\n"
        f"Subject: {prior_subject}\nBody: {prior_body}\n\n"
        "### Prospect\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Pain hypothesis: {prospect.get('pain_hypothesis','')}\n"
        f"- Signals: {prospect.get('signals', [])}\n\n"
        f"### Days since first touch\n{days_since}\n\n"
        "Return JSON."
    )


def run(prospect: dict, dry_run: bool = False) -> list[dict]:
    pid = prospect["prospect_id"]
    if prospect.get("stage") != "contacted":
        logger.info(f"skip scheduling followups: {pid} not contacted", extra={"prospect_id": pid})
        return []

    prior_subject = prospect.get("email_draft_subject", "")
    prior_body = prospect.get("email_draft_body", "")
    if not prior_subject or not prior_body:
        return []

    schedule = _load_schedule()
    now = datetime.now(timezone.utc)
    existing_days = {e["day_offset"] for e in schedule if e["prospect_id"] == pid}

    new_entries: list[dict] = []
    for d in DAY_OFFSETS:
        if d in existing_days:
            continue
        if dry_run or not llm.has_llm():
            subject = f"[DRY-RUN] Day {d} follow-up for {prospect.get('company','')}"
            body = f"[DRY-RUN] Follow-up body — day {d} variant."
        else:
            try:
                result = llm.chat_json(
                    system=FOLLOWUP_SYSTEM,
                    user=_build_user(prospect, prior_subject, prior_body, d),
                    model=env.get("EURI_MODEL_QUALIFY", "gpt-4o-mini"),
                    temperature=0.5,
                )
                subject = result.get("subject", "")
                body = result.get("body", "")
            except Exception as e:
                logger.warning(f"followup LLM failed for {pid} day {d}: {e}")
                continue

        entry = {
            "prospect_id": pid,
            "day_offset": d,
            "send_at": (now + timedelta(days=d)).isoformat(),
            "subject": subject,
            "body": body,
            "status": "scheduled",
            "created_at": now.isoformat(),
        }
        new_entries.append(entry)

    if new_entries:
        schedule.extend(new_entries)
        _save_schedule(schedule)
        logger.info(f"scheduled {len(new_entries)} followups for {pid}", extra={"prospect_id": pid})

    return new_entries


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 04: schedule followups")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-contacted", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_contacted:
        todo = state.prospects_where(status="contacted")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-contacted")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    total = 0
    for p in todo:
        total += len(run(p, dry_run=dry))
    print(json.dumps({"status": "success", "dry_run": dry, "scheduled": total, "prospects": len(todo)}, indent=2))


if __name__ == "__main__":
    main()
