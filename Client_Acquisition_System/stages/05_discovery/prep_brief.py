#!/usr/bin/env python3
"""Stage 05 — Generate a 1-page pre-call prep brief for the human.

Writes to .tmp/briefs/{prospect_id}.md. The human reads before the call.
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

BRIEF_DIR = PROJECT_ROOT / ".tmp" / "briefs"
BRIEF_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You prep founders for discovery calls. Given a prospect + offer + pain hypothesis,
write a 1-page brief in markdown with sections:
1. # Who they are (3 bullets)
2. # Likely pain (2-3 bullets, specific)
3. # Discovery questions (exactly 3, tailored)
4. # If the call goes well
5. # Red flags to watch for

Return JSON: {"brief_md": "..."}"""


def _load_offer() -> dict:
    p = Path(env.get("OFFER_CONFIG", "config/offer.yaml"))
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def _build_user(prospect: dict, offer: dict) -> str:
    hero = (offer.get("case_studies") or [{}])[0].get("result", "")
    return (
        "### Prospect\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Contact: {prospect.get('contact_name','')} — {prospect.get('contact_role','')}\n"
        f"- Website summary: {prospect.get('website_summary','')}\n"
        f"- Signals: {prospect.get('signals', [])}\n"
        f"- Pain hypothesis: {prospect.get('pain_hypothesis','')}\n"
        f"- Fit score: {prospect.get('fit_score','')}\n"
        f"- Fit reasoning: {prospect.get('fit_reasoning','')}\n\n"
        "### Offer\n"
        f"{offer.get('one_liner','')}\n"
        f"Deliverable: {', '.join(offer.get('deliverables', [])[:3])}\n"
        f"Hero case: {hero}\n\n"
        "Write the brief. Return JSON only."
    )


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    offer = _load_offer()

    if dry_run or not llm.has_llm():
        stub = llm.stub_response("prep_brief")
        brief_md = stub["brief_md"]
    else:
        try:
            result = llm.chat_json(
                system=SYSTEM_PROMPT,
                user=_build_user(prospect, offer),
                model=env.get("EURI_MODEL_QUALIFY", "gpt-4o-mini"),
                temperature=0.3,
            )
            brief_md = result.get("brief_md", "")
        except Exception as e:
            logger.error(f"prep_brief LLM failed: {e}")
            return state.upsert_prospect({**prospect, "prep_brief_error": str(e)})

    # Prepend metadata header
    full = (
        f"# Discovery prep — {prospect.get('company','')}\n"
        f"- Prospect ID: {pid}\n"
        f"- Contact: {prospect.get('contact_name','')} ({prospect.get('contact_role','')})\n"
        f"- Email: {prospect.get('email','')}\n"
        f"- LinkedIn: {prospect.get('linkedin_url','')}\n"
        f"- Fit score: {prospect.get('fit_score','')}\n\n"
        "---\n\n"
        + brief_md
    )

    slug = slugify(prospect.get("company", pid))
    path = BRIEF_DIR / f"{pid}-{slug}.md"
    path.write_text(full)
    logger.info(f"prep brief saved: {path.relative_to(PROJECT_ROOT)}", extra={"prospect_id": pid})

    return state.upsert_prospect({**prospect, "prep_brief_path": str(path.relative_to(PROJECT_ROOT))})


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 05: prep brief")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-booked", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_booked:
        todo = state.prospects_where(status="booked")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-booked")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    for p in todo:
        run(p, dry_run=dry)
    print(json.dumps({"status": "success", "dry_run": dry, "processed": len(todo)}, indent=2))


if __name__ == "__main__":
    main()
