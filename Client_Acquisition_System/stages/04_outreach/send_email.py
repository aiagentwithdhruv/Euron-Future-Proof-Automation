#!/usr/bin/env python3
"""Stage 04 — Send a compliance-checked, rate-limited email.

Gates (ALL must pass before send):
  1. Prospect email is valid
  2. Prospect not in suppression list
  3. email_draft_compliant == True (Stage 04 personalize produced compliant copy)
  4. Rate limits OK (daily cap + per-prospect cooldown)
  5. DRY_RUN off

Provider: Resend (primary). On dry-run, prints payload + transitions state as if sent.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state, rate_limit  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import validate_email  # noqa: E402

logger = get_logger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def _send_resend(api_key: str, from_addr: str, to: str, subject: str, body: str, reply_to: str = "") -> dict:
    import requests

    payload = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "text": body,
    }
    if reply_to:
        payload["reply_to"] = reply_to
    resp = requests.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Resend {resp.status_code}: {resp.text[:300]}")
    return {"provider": "resend", "message_id": resp.json().get("id", "")}


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]

    # Gate 1: valid email
    try:
        to_addr = validate_email(prospect.get("email", ""))
    except ValueError as e:
        logger.warning(f"invalid email for {pid}: {e}", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "send_blocked": "invalid_email"})

    # Gate 2: suppression
    if state.is_suppressed(to_addr):
        logger.info(f"suppressed: {to_addr}", extra={"prospect_id": pid})
        state.transition(pid, "qualified", "suppressed", reason="in suppression list")
        return state.get_prospect(pid)

    # Gate 3: compliance
    if not prospect.get("email_draft_compliant"):
        logger.warning(f"draft not compliant for {pid}", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "send_blocked": "draft_not_compliant"})

    subject = prospect.get("email_draft_subject", "")
    body = prospect.get("email_draft_body", "")

    sender = env.get("EMAIL_FROM", "")
    sender_name = env.get("EMAIL_FROM_NAME", "")
    from_addr = f'"{sender_name}" <{sender}>' if sender_name else sender

    # Gate 4: rate limits (always checked, even in dry-run, so caller sees limits)
    try:
        rate_limit.check_and_record(pid, sender)
    except rate_limit.RateLimitError as e:
        logger.warning(f"rate limit for {pid}: {e}", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "send_blocked": f"rate_limit:{e}"})

    # Gate 5: dry-run
    if dry_run:
        logger.info(f"[DRY-RUN] would send to {to_addr}", extra={"prospect_id": pid})
        state.transition(pid, "contacted", "contacted", reason="dry-run send")
        return state.upsert_prospect({
            **state.get_prospect(pid),
            "last_send_provider": "dry-run",
            "last_send_message_id": "dryrun-" + pid,
        })

    api_key = env.get("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY missing; cannot send outside dry-run")
        return state.upsert_prospect({**prospect, "send_blocked": "no_resend_key"})

    try:
        receipt = _send_resend(api_key, from_addr, to_addr, subject, body, env.get("EMAIL_REPLY_TO", ""))
    except Exception as e:
        logger.error(f"send failed for {pid}: {e}", extra={"prospect_id": pid})
        return state.upsert_prospect({**prospect, "send_blocked": f"send_error:{e}"})

    state.transition(pid, "contacted", "contacted", reason="email sent")
    return state.upsert_prospect({
        **state.get_prospect(pid),
        "last_send_provider": receipt["provider"],
        "last_send_message_id": receipt["message_id"],
    })


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 04: send email")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-ready", action="store_true", help="Send to all qualified prospects with compliant drafts")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_ready:
        todo = [p for p in state.prospects_where(status="qualified") if p.get("email_draft_compliant")]
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-ready")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    results = [run(p, dry_run=dry) for p in todo]
    print(json.dumps({
        "status": "success",
        "dry_run": dry,
        "sent": len([r for r in results if r and r.get("status") == "contacted"]),
        "blocked": len([r for r in results if r and r.get("send_blocked")]),
        "total": len(results),
    }, indent=2))


if __name__ == "__main__":
    main()
