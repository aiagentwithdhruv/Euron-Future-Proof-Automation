#!/usr/bin/env python3
"""Stage 03 — LLM fit-scoring against ICP + offer.

Input: prospect (must be stage='enriched', status='pending_qualify')
Output: fit_score, fit_reasoning, pain_hypothesis written to prospect.
Transitions: qualified (>=70) | nurture (50-69) | archived (<50)
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

logger = get_logger(__name__)

PROMPT_PATH = PROJECT_ROOT / "prompts" / "score_fit_v1.md"

SYSTEM_PROMPT = """You are a B2B sales qualification analyst. You score prospects against an Ideal
Customer Profile and a specific service offer. Be ruthless and calibrated — 60%
of real prospects score below 50. Only exceptional matches earn 80+.

Rubric (max 100):
- Industry match: 25
- Size match: 20
- Geography match: 10
- Role seniority: 20
- Signal strength: 25

Return JSON ONLY:
{
  "fit_score": <int 0-100>,
  "subscores": {"industry": int, "size": int, "geography": int, "role": int, "signal": int},
  "fit_reasoning": "<1-2 sentences>",
  "pain_hypothesis": "<1 sentence, specific>",
  "disqualified": <bool>,
  "disqualification_reason": "<string>"
}"""


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) if path.exists() else {}


def _build_user(prospect: dict, icp: dict, offer: dict) -> str:
    return (
        f"### ICP\n{yaml.safe_dump(icp, sort_keys=False)}\n"
        f"### Offer\n{yaml.safe_dump(offer, sort_keys=False)}\n"
        "### Prospect\n"
        f"- Company: {prospect.get('company','')}\n"
        f"- Website: {prospect.get('website','')}\n"
        f"- Contact: {prospect.get('contact_name','')} — {prospect.get('contact_role','')}\n"
        f"- City / Country: {prospect.get('city','')} / {prospect.get('country','')}\n"
        f"- Website summary: {prospect.get('website_summary','')}\n"
        f"- Tech stack: {prospect.get('tech_stack', [])}\n"
        f"- Signals: {prospect.get('signals', [])}\n"
        f"- LinkedIn bio: {prospect.get('bio_summary','')}\n\n"
        "Score the prospect against the ICP + offer. Output JSON only."
    )


def _bucket(score: int, disqualified: bool) -> tuple[str, str]:
    if disqualified:
        return "archived", "archived"
    if score >= 70:
        return "qualified", "qualified"
    if score >= 50:
        return "qualified", "nurture"
    return "qualified", "archived"


def run(prospect: dict, icp_path: str | None = None, offer_path: str | None = None, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    icp = _load_yaml(Path(icp_path or env.get("ICP_CONFIG", "config/icp.yaml")))
    offer = _load_yaml(Path(offer_path or env.get("OFFER_CONFIG", "config/offer.yaml")))

    if dry_run:
        result = llm.stub_response("score_fit")
    else:
        if not llm.has_llm():
            logger.warning("No LLM key; using stub for score_fit")
            result = llm.stub_response("score_fit")
        else:
            try:
                result = llm.chat_json(
                    system=SYSTEM_PROMPT,
                    user=_build_user(prospect, icp, offer),
                    model=env.get("EURI_MODEL_QUALIFY", "gpt-4o-mini"),
                    temperature=0.2,
                )
            except Exception as e:
                logger.error(f"LLM qualify failed for {pid}: {e}")
                result = {"fit_score": 0, "fit_reasoning": f"LLM failure: {e}", "pain_hypothesis": "", "disqualified": True, "disqualification_reason": "llm_error"}

    score = int(result.get("fit_score", 0))
    disqualified = bool(result.get("disqualified", False))
    new_stage, new_status = _bucket(score, disqualified)

    merged = state.upsert_prospect({
        **prospect,
        "fit_score": score,
        "fit_subscores": result.get("subscores", {}),
        "fit_reasoning": result.get("fit_reasoning", ""),
        "pain_hypothesis": result.get("pain_hypothesis", ""),
        "disqualified": disqualified,
        "disqualification_reason": result.get("disqualification_reason", ""),
    })
    transitioned = state.transition(pid, new_stage, new_status, reason=f"score={score}")
    logger.info(f"qualified {pid}: score={score} status={new_status}", extra={"prospect_id": pid, "stage": "03_qualify"})
    return transitioned


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 03: qualify prospects")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-pending", action="store_true")
    ap.add_argument("--icp", default=None)
    ap.add_argument("--offer", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_pending:
        todo = state.prospects_where(status="pending_qualify")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-pending")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    results = [run(p, args.icp, args.offer, dry_run=dry) for p in todo]
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "processed": len(results),
        "qualified": len([r for r in results if r.get("status") == "qualified"]),
        "nurture": len([r for r in results if r.get("status") == "nurture"]),
        "archived": len([r for r in results if r.get("status") == "archived"]),
    }, indent=2))


if __name__ == "__main__":
    main()
