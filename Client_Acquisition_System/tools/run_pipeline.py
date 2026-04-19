#!/usr/bin/env python3
"""Orchestrator — run the full 6-stage Client Acquisition pipeline.

Usage:
  # Full cycle, dry-run, 5 prospects
  python tools/run_pipeline.py --icp config/icp.yaml --limit 5 --dry-run

  # Only scrape (google maps, 10 dental clinics Dubai)
  python tools/run_pipeline.py --stage 01_scrape --query "dental clinics Dubai UAE" --limit 10

  # Seed fakes + run end-to-end (no external calls)
  python tools/run_pipeline.py --seed-fakes 5 --dry-run

Writes runs/YYYY-MM-DD-pipeline.md summary at end.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from tools._load import load as load_stage  # noqa: E402

logger = get_logger(__name__)

RUNS_DIR = PROJECT_ROOT / "runs"
RUNS_DIR.mkdir(exist_ok=True)

STAGES = [
    "01_scrape",
    "02_enrich",
    "03_qualify",
    "04_outreach",
    "05_discovery",
    "06_proposal",
]


def _snapshot() -> dict:
    pipeline = state.load_pipeline()
    by_status: dict[str, int] = {}
    for p in pipeline.values():
        by_status[p.get("status", "unknown")] = by_status.get(p.get("status", "unknown"), 0) + 1
    return {"total": len(pipeline), "by_status": by_status}


def stage_01_scrape(query: str | None, limit: int, dry_run: bool) -> dict:
    if not query:
        logger.info("no --query provided; skipping 01_scrape (use --seed-fakes to inject)")
        return {"skipped": True}
    mod = load_stage("01_scrape/google_maps.py")
    inserted = mod.run(query, limit, dry_run=dry_run)
    return {"inserted": len(inserted)}


def stage_02_enrich(dry_run: bool) -> dict:
    find_email = load_stage("02_enrich/find_email.py")
    linkedin_profile = load_stage("02_enrich/linkedin_profile.py")
    context = load_stage("02_enrich/company_context.py")

    pending = state.prospects_where(status="pending_enrich")
    for p in pending:
        find_email.run(p, dry_run=dry_run)
        p2 = state.get_prospect(p["prospect_id"])
        linkedin_profile.run(p2, dry_run=dry_run)
        p3 = state.get_prospect(p["prospect_id"])
        context.run(p3, dry_run=dry_run)
    return {"processed": len(pending)}


def stage_03_qualify(dry_run: bool) -> dict:
    mod = load_stage("03_qualify/score_fit.py")
    pending = state.prospects_where(status="pending_qualify")
    for p in pending:
        mod.run(p, dry_run=dry_run)
    return {"processed": len(pending)}


def stage_04_outreach(dry_run: bool) -> dict:
    personalize = load_stage("04_outreach/personalize_email.py")
    send = load_stage("04_outreach/send_email.py")
    linkedin_dm = load_stage("04_outreach/linkedin_dm.py")
    followups = load_stage("04_outreach/followup_sequence.py")

    # Personalize every qualified prospect with an email
    qualified = state.prospects_where(status="qualified")
    personalized = 0
    for p in qualified:
        if not p.get("email"):
            continue
        personalize.run(p, dry_run=dry_run)
        personalized += 1

    # LinkedIn drafts for any qualified prospect that has a LinkedIn URL
    linkedin_drafted = 0
    for p in state.prospects_where(status="qualified"):
        if p.get("linkedin_url"):
            linkedin_dm.run(state.get_prospect(p["prospect_id"]), dry_run=dry_run)
            linkedin_drafted += 1

    # Send emails to compliant drafts
    sent = 0
    blocked = 0
    for p in state.prospects_where(status="qualified"):
        if not p.get("email_draft_compliant"):
            continue
        after = send.run(state.get_prospect(p["prospect_id"]), dry_run=dry_run)
        if after.get("send_blocked"):
            blocked += 1
        elif after.get("status") == "contacted":
            sent += 1

    # Schedule followups for contacted prospects
    for p in state.prospects_where(status="contacted"):
        followups.run(p, dry_run=dry_run)

    return {
        "qualified": len(qualified),
        "personalized": personalized,
        "linkedin_drafts": linkedin_drafted,
        "sent": sent,
        "blocked": blocked,
    }


def stage_05_discovery(dry_run: bool) -> dict:
    booking = load_stage("05_discovery/booking_link.py")
    brief = load_stage("05_discovery/prep_brief.py")

    # In the real flow: a prospect replies -> human transitions to booked.
    # For dry-run demo: auto-promote one contacted prospect to booked.
    if dry_run:
        contacted = state.prospects_where(status="contacted")
        if contacted:
            pid = contacted[0]["prospect_id"]
            state.transition(pid, "engaged", "booked", reason="[dry-run] auto-book")

    booked = state.prospects_where(status="booked")
    for p in booked:
        booking.run(p)
        brief.run(state.get_prospect(p["prospect_id"]), dry_run=dry_run)
    return {"booked": len(booked)}


def stage_06_proposal(dry_run: bool) -> dict:
    mod = load_stage("06_proposal/generate_draft.py")

    # Simulate post-call: promote the booked prospects to call_done with stub notes
    # (only in dry-run — never fabricate call notes in real runs)
    if dry_run:
        for p in state.prospects_where(status="booked"):
            state.transition(p["prospect_id"], "call_done", "call_done", reason="[dry-run] auto call_done")

    to_propose = state.prospects_where(status="call_done")
    for p in to_propose:
        notes = (
            "[DRY-RUN] Call notes:\n"
            "- They confirmed manual lead routing is slowing their sales cycle.\n"
            "- Currently spend 6 hrs/week on CRM data entry.\n"
            "- Budget is not fixed; they want to see a 30-day pilot first.\n"
            "- Decision by end of month."
        )
        mod.run(
            state.get_prospect(p["prospect_id"]),
            notes,
            confirmed_pain="Manual lead routing + CRM data entry",
            dry_run=dry_run,
        )
    return {"drafts": len(to_propose)}


STAGE_FNS = {
    "01_scrape": lambda a, d: stage_01_scrape(a.query, a.limit, d),
    "02_enrich": lambda a, d: stage_02_enrich(d),
    "03_qualify": lambda a, d: stage_03_qualify(d),
    "04_outreach": lambda a, d: stage_04_outreach(d),
    "05_discovery": lambda a, d: stage_05_discovery(d),
    "06_proposal": lambda a, d: stage_06_proposal(d),
}


def write_run_log(started_at: datetime, stage_results: dict, dry_run: bool, args) -> Path:
    today = date.today().isoformat()
    path = RUNS_DIR / f"{today}-pipeline.md"
    ended = datetime.now(timezone.utc)
    md = [
        f"# Pipeline run — {today}",
        "",
        f"- Started: {started_at.isoformat()}",
        f"- Ended:   {ended.isoformat()}",
        f"- Duration: {(ended - started_at).total_seconds():.1f}s",
        f"- Mode: {'DRY-RUN' if dry_run else 'LIVE'}",
        f"- CLI: `{' '.join(sys.argv)}`",
        "",
        "## Stage results",
        "",
    ]
    for stage, result in stage_results.items():
        md.append(f"### {stage}")
        md.append("```json")
        md.append(json.dumps(result, indent=2, default=str))
        md.append("```")
        md.append("")

    md.append("## Final pipeline snapshot")
    md.append("```json")
    md.append(json.dumps(_snapshot(), indent=2))
    md.append("```")
    md.append("")

    if dry_run:
        md.append("> ✅ No real emails sent. No LinkedIn DMs sent. All external calls stubbed.")
    else:
        md.append("> ⚠️  LIVE run — check state/sends.log for actual send receipts.")

    path.write_text("\n".join(md))
    return path


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Client Acquisition pipeline orchestrator")
    ap.add_argument("--icp", default=None, help="Path to ICP yaml (default: from env)")
    ap.add_argument("--limit", type=int, default=25, help="Max prospects per scrape call")
    ap.add_argument("--query", default=None, help="Google Maps search query (for 01_scrape)")
    ap.add_argument("--stage", default=None, help="Run only this stage (01_scrape..06_proposal)")
    ap.add_argument("--seed-fakes", type=int, default=0, help="Seed N fake prospects before running")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.icp:
        import os
        os.environ["ICP_CONFIG"] = args.icp

    started = datetime.now(timezone.utc)
    results: dict[str, dict] = {}

    if args.seed_fakes > 0:
        from tools import seed_fake_prospects
        results["seed"] = {"inserted": len(seed_fake_prospects.run(args.seed_fakes))}

    if args.stage:
        if args.stage not in STAGE_FNS:
            ap.error(f"Unknown stage: {args.stage}. Choose from {list(STAGE_FNS)}")
        logger.info(f"running single stage: {args.stage}")
        t0 = time.time()
        results[args.stage] = STAGE_FNS[args.stage](args, dry)
        results[args.stage]["duration_s"] = round(time.time() - t0, 2)
    else:
        for stage in STAGES:
            logger.info(f"stage {stage} start", extra={"stage": stage})
            t0 = time.time()
            try:
                results[stage] = STAGE_FNS[stage](args, dry)
            except Exception as e:
                logger.error(f"stage {stage} raised: {e}")
                results[stage] = {"error": str(e)}
                break
            results[stage]["duration_s"] = round(time.time() - t0, 2)

    log_path = write_run_log(started, results, dry, args)
    summary = {
        "status": "success",
        "dry_run": dry,
        "stages": results,
        "snapshot": _snapshot(),
        "run_log": str(log_path.relative_to(PROJECT_ROOT)),
    }
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
