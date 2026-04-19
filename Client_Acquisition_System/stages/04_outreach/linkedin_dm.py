#!/usr/bin/env python3
"""Stage 04 — LinkedIn DM DRAFT generator.

LinkedIn's ToS forbids DM automation. This tool ONLY generates drafts and writes
them to `.tmp/drafts/linkedin/{prospect_id}.md`. A human reads, edits, and sends.

We never call LinkedIn's API to send.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state, llm  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import slugify  # noqa: E402

logger = get_logger(__name__)

DRAFT_DIR = PROJECT_ROOT / ".tmp" / "drafts" / "linkedin"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You write LinkedIn DMs that founders actually reply to. Conversational, specific,
short (40-80 words). You never sound like a sales rep. No links in the first DM.

Return JSON: {"dm": "...", "hook": "..."}"""


def _load_offer_one_liner() -> str:
    p = Path(env.get("OFFER_CONFIG", "config/offer.yaml"))
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if p.exists():
        return yaml.safe_load(p.read_text()).get("one_liner", "")
    return ""


def _build_user(prospect: dict, offer_line: str) -> str:
    return (
        f"### Offer\n{offer_line}\n\n"
        "### Prospect\n"
        f"- Name: {prospect.get('contact_name','')}\n"
        f"- Role: {prospect.get('contact_role','')}\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Bio: {prospect.get('bio_summary','')}\n"
        f"- Signals: {prospect.get('signals', [])}\n"
        f"- Pain hypothesis: {prospect.get('pain_hypothesis','')}\n\n"
        "Write a LinkedIn DM draft. Return JSON."
    )


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    if not prospect.get("linkedin_url"):
        return state.upsert_prospect({**prospect, "linkedin_draft_skipped": "no linkedin url"})

    if dry_run or not llm.has_llm():
        stub = llm.stub_response("linkedin_dm", name=prospect.get("contact_name",""), company=prospect.get("company",""), topic=(prospect.get("signals") or ["growth"])[0])
        result = {"dm": stub["dm"], "hook": "[dry-run]"}
    else:
        try:
            result = llm.chat_json(
                system=SYSTEM_PROMPT,
                user=_build_user(prospect, _load_offer_one_liner()),
                model=env.get("EURI_MODEL_PERSONALIZE", "gpt-4o"),
                temperature=0.5,
            )
        except Exception as e:
            logger.error(f"linkedin DM LLM failed: {e}")
            return state.upsert_prospect({**prospect, "linkedin_draft_error": str(e)})

    slug = slugify(prospect.get("company", pid))
    draft_path = DRAFT_DIR / f"{pid}-{slug}.md"
    draft_md = (
        f"# LinkedIn DM draft — {prospect.get('contact_name','')} ({prospect.get('company','')})\n\n"
        f"**Send to:** {prospect.get('linkedin_url','')}\n"
        f"**Hook used:** {result.get('hook','')}\n"
        f"**Prospect ID:** {pid}\n\n"
        "---\n\n"
        f"{result['dm']}\n\n"
        "---\n\n"
        "> **MANUAL SEND.** Review, edit tone, copy-paste into LinkedIn. Do NOT automate.\n"
        "> After sending, run: `python tools/mark_sent.py --prospect-id "
        f"{pid} --channel linkedin`\n"
    )
    draft_path.write_text(draft_md)
    logger.info(f"linkedin draft saved: {draft_path.relative_to(PROJECT_ROOT)}", extra={"prospect_id": pid})

    return state.upsert_prospect({
        **prospect,
        "linkedin_draft_path": str(draft_path.relative_to(PROJECT_ROOT)),
        "linkedin_draft_hook": result.get("hook", ""),
    })


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 04: LinkedIn DM draft (manual-send)")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-qualified", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_qualified:
        todo = [p for p in state.prospects_where(status="qualified") if p.get("linkedin_url")]
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-qualified")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    for p in todo:
        run(p, dry_run=dry)
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "drafts": len([p for p in todo if state.get_prospect(p['prospect_id']).get('linkedin_draft_path')]),
        "total": len(todo),
        "note": "LinkedIn DMs are HUMAN-SEND only. See .tmp/drafts/linkedin/",
    }, indent=2))


if __name__ == "__main__":
    main()
