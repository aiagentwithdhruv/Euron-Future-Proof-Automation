#!/usr/bin/env python3
"""Stage 04 — Generate a personalized email draft (subject + body) for a prospect.

Calls LLM with `personalize_email_v1` prompt. Rejects generic output. Appends
the compliance footer. Writes draft to state (email_draft_subject/email_draft_body).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state, llm, compliance  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

SYSTEM_PROMPT = """You write hyper-personalized B2B cold emails. Short. Specific. Grounded in the
prospect's website and signals. You refuse to send generic copy.

Rules:
1. Body: 60-120 words. No fluff. No "hope this finds you well."
2. Open with a specific, observable hook about the prospect's company.
3. One offer line. Optional case study line. One clear CTA.
4. Subject: 3-8 words. Reference the hook. Honest (no fake Re: / Fwd:).
5. Plain text only. No signature or unsubscribe footer (system appends).
6. If no specific hook is available, return {"abort": true, "reason": "..."}.

Return JSON: {"subject": "...", "body": "...", "hook": "...", "abort": false, "reason": ""}"""


def _load_offer() -> dict:
    p = Path(env.get("OFFER_CONFIG", "config/offer.yaml"))
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return yaml.safe_load(p.read_text()) if p.exists() else {}


def _build_user(prospect: dict, offer: dict) -> str:
    band = offer.get("price_band", {}) or {}
    return (
        "### Offer\n"
        f"{offer.get('one_liner','')}\n"
        f"Deliverable: {', '.join(offer.get('deliverables', [])[:3])}\n"
        f"Price band: ${band.get('low_usd',0)}-${band.get('high_usd',0)}\n"
        f"Hero case: {(offer.get('case_studies') or [{}])[0].get('result','')}\n\n"
        "### Prospect\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Contact: {prospect.get('contact_name','')} — {prospect.get('contact_role','')}\n"
        f"- Website summary: {prospect.get('website_summary','')}\n"
        f"- Signals: {prospect.get('signals', [])}\n"
        f"- Tech stack: {prospect.get('tech_stack', [])}\n"
        f"- Pain hypothesis: {prospect.get('pain_hypothesis','')}\n\n"
        "Generate a personalized cold email. Return JSON only."
    )


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    offer = _load_offer()

    if dry_run or not llm.has_llm():
        stub = llm.stub_response("personalize_email", company=prospect.get("company",""), name=prospect.get("contact_name",""), signal=(prospect.get("signals") or ["growth"])[0])
        result = {"subject": stub["subject"], "body": stub["body"], "hook": stub["hook"], "abort": False, "reason": ""}
    else:
        try:
            result = llm.chat_json(
                system=SYSTEM_PROMPT,
                user=_build_user(prospect, offer),
                model=env.get("EURI_MODEL_PERSONALIZE", "gpt-4o"),
                temperature=0.5,
            )
        except Exception as e:
            logger.error(f"personalize_email LLM failed: {e}")
            return state.upsert_prospect({**prospect, "email_draft_error": str(e)})

    if result.get("abort"):
        logger.info(f"personalize aborted for {pid}: {result.get('reason')}", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "email_draft_abort": True, "email_draft_abort_reason": result.get("reason","")})

    # Compliance check (adds footer + validates)
    verdict = compliance.build_compliant_email(
        subject=result["subject"],
        body=result["body"],
        company=prospect.get("company", ""),
        prospect_name=prospect.get("contact_name", ""),
        prospect_email=prospect.get("email", ""),
    )
    if not verdict["compliant"]:
        logger.warning(f"non-compliant draft for {pid}: {verdict['reason']}", extra={"prospect_id": pid})
        return state.upsert_prospect({
            **prospect,
            "email_draft_subject": result["subject"],
            "email_draft_body": result["body"],
            "email_draft_compliance_error": verdict["reason"],
        })

    return state.upsert_prospect({
        **prospect,
        "email_draft_subject": verdict["subject"],
        "email_draft_body": verdict["body"],
        "email_draft_hook": result.get("hook", ""),
        "email_draft_compliant": True,
        "email_draft_compliance_error": "",
    })


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 04: personalize email")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-qualified", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_qualified:
        todo = state.prospects_where(status="qualified")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-qualified")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    for p in todo:
        run(p, dry_run=dry)
    print(json.dumps({"status": "success", "dry_run": dry, "processed": len(todo)}, indent=2))


if __name__ == "__main__":
    main()
