#!/usr/bin/env python3
"""Pipeline metrics CLI — reads state/ and prints conversion rates."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402


STATUS_ORDER = [
    "pending_enrich",
    "pending_qualify",
    "unreachable",
    "qualified",
    "nurture",
    "archived",
    "contacted",
    "booked",
    "call_done",
    "proposal_draft_ready",
    "won",
    "lost",
    "suppressed",
]


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{round(part / total * 100, 1)}%"


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Pipeline dashboard")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of table")
    args = ap.parse_args()

    pipeline = state.load_pipeline()
    total = len(pipeline)
    by_status = Counter(p.get("status", "unknown") for p in pipeline.values())
    by_source = Counter(p.get("source", "unknown") for p in pipeline.values())

    qualified = by_status["qualified"] + by_status["nurture"] + by_status["contacted"] + by_status["booked"] + by_status["call_done"] + by_status["proposal_draft_ready"] + by_status["won"]
    contacted = by_status["contacted"] + by_status["booked"] + by_status["call_done"] + by_status["proposal_draft_ready"] + by_status["won"]
    booked = by_status["booked"] + by_status["call_done"] + by_status["proposal_draft_ready"] + by_status["won"]
    proposals = by_status["proposal_draft_ready"] + by_status["won"]
    won = by_status["won"]

    funnel = {
        "total": total,
        "qualified": qualified,
        "contacted": contacted,
        "booked": booked,
        "proposal_ready": proposals,
        "won": won,
        "rates": {
            "scrape_to_qualified": _pct(qualified, total),
            "qualified_to_contacted": _pct(contacted, qualified),
            "contacted_to_booked": _pct(booked, contacted),
            "booked_to_proposal": _pct(proposals, booked),
            "proposal_to_won": _pct(won, proposals),
        },
    }

    if args.json:
        import json
        print(json.dumps({"funnel": funnel, "by_status": dict(by_status), "by_source": dict(by_source)}, indent=2))
        return

    print("=" * 56)
    print("  CLIENT ACQUISITION PIPELINE")
    print("=" * 56)
    print(f"  Total prospects: {total}")
    print()
    print("  By status:")
    for s in STATUS_ORDER:
        if by_status.get(s):
            print(f"    {s:<25} {by_status[s]:>4}")
    for s, n in by_status.items():
        if s not in STATUS_ORDER:
            print(f"    {s:<25} {n:>4}")
    print()
    print("  Funnel:")
    print(f"    scraped -> qualified:    {funnel['rates']['scrape_to_qualified']} ({qualified}/{total})")
    print(f"    qualified -> contacted:  {funnel['rates']['qualified_to_contacted']} ({contacted}/{qualified})")
    print(f"    contacted -> booked:     {funnel['rates']['contacted_to_booked']} ({booked}/{contacted})")
    print(f"    booked -> proposal:      {funnel['rates']['booked_to_proposal']} ({proposals}/{booked})")
    print(f"    proposal -> won:         {funnel['rates']['proposal_to_won']} ({won}/{proposals})")
    print()
    print("  By source:")
    for src, n in by_source.most_common():
        print(f"    {src:<30} {n:>4}")
    print("=" * 56)


if __name__ == "__main__":
    main()
