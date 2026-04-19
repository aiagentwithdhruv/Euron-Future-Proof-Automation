#!/usr/bin/env python3
"""Stage 06 — Generate a proposal draft from call notes + offer.

Input: prospect + call notes (from --notes-file or --notes)
Output: .tmp/proposals/{prospect_id}-YYYY-MM-DD.md

This tool STOPS at draft. Never sends. Human reviews, edits, and delivers separately.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state, llm  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import slugify  # noqa: E402

logger = get_logger(__name__)

PROPOSAL_DIR = PROJECT_ROOT / ".tmp" / "proposals"
PROPOSAL_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You write B2B proposals that close. Short, specific, built around the client's
exact words. Every section ties back to something they said on the call.

Mandatory structure:
1. # Executive summary (1 paragraph)
2. # Your situation (quote their words)
3. # Proposed approach (3-step)
4. # Deliverables
5. # Timeline
6. # Investment
7. # Next steps (2 options)

Return JSON: {"proposal_md": "..."}"""


def _load_offer() -> dict:
    p = Path(env.get("OFFER_CONFIG", "config/offer.yaml"))
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def _build_user(prospect: dict, offer: dict, call_notes: str, confirmed_pain: str) -> str:
    return (
        "### Call notes (raw)\n"
        f"{call_notes}\n\n"
        "### Offer\n"
        f"{yaml.safe_dump(offer, sort_keys=False)}\n"
        "### Prospect\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Contact: {prospect.get('contact_name','')} — {prospect.get('contact_role','')}\n"
        f"- Pain hypothesis confirmed on call: {confirmed_pain or prospect.get('pain_hypothesis','')}\n\n"
        "Generate the proposal draft. Return JSON only."
    )


def run(prospect: dict, call_notes: str, confirmed_pain: str = "", dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    offer = _load_offer()

    if dry_run or not llm.has_llm():
        stub = llm.stub_response("proposal_draft", company=prospect.get("company",""))
        proposal_md = stub["proposal_md"] + f"\n\n_Call notes considered:_\n{call_notes[:500]}\n"
    else:
        try:
            result = llm.chat_json(
                system=SYSTEM_PROMPT,
                user=_build_user(prospect, offer, call_notes, confirmed_pain),
                model=env.get("EURI_MODEL_PERSONALIZE", "gpt-4o"),
                temperature=0.4,
            )
            proposal_md = result.get("proposal_md", "")
        except Exception as e:
            logger.error(f"proposal LLM failed: {e}")
            return state.upsert_prospect({**prospect, "proposal_error": str(e)})

    slug = slugify(prospect.get("company", pid))
    path = PROPOSAL_DIR / f"{pid}-{slug}-{date.today().isoformat()}.md"
    full = (
        f"# Proposal — {prospect.get('company','')}\n"
        f"Prepared for: {prospect.get('contact_name','')} ({prospect.get('contact_role','')})\n"
        f"Date: {date.today().isoformat()}\n"
        f"Prospect ID: {pid}\n\n"
        "---\n\n"
        + proposal_md
        + "\n\n---\n\n"
        "> **MANUAL SEND.** This is a DRAFT. Review, edit, deliver via Docs/Notion/PDF. Automation stops here.\n"
    )
    path.write_text(full)
    logger.info(f"proposal draft saved: {path.relative_to(PROJECT_ROOT)}", extra={"prospect_id": pid})

    merged = state.upsert_prospect({**prospect, "proposal_draft_path": str(path.relative_to(PROJECT_ROOT))})
    if prospect.get("stage") == "call_done":
        state.transition(pid, "call_done", "proposal_draft_ready", reason="draft generated")
    return merged


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 06: proposal draft")
    ap.add_argument("--prospect-id", required=True)
    ap.add_argument("--notes", help="Inline call notes")
    ap.add_argument("--notes-file", help="Path to a markdown file with call notes")
    ap.add_argument("--confirmed-pain", default="", help="Pain point confirmed during the call")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    p = state.get_prospect(args.prospect_id)
    if not p:
        ap.error(f"No prospect {args.prospect_id}")

    if args.notes_file:
        notes = Path(args.notes_file).read_text()
    elif args.notes:
        notes = args.notes
    else:
        notes = "[no notes provided — stub proposal]"

    out = run(p, notes, args.confirmed_pain, dry_run=dry)
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "proposal_path": out.get("proposal_draft_path", ""),
    }, indent=2))


if __name__ == "__main__":
    main()
