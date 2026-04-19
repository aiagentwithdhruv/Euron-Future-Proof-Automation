"""Draft a polite, non-committal reply for a ticket. Runs the guardrail before writing.

Usage:
    python tools/draft_reply.py --ticket-id TICKET-... --kb ./knowledge/
    python tools/draft_reply.py --all --kb ./knowledge/          # draft every ticket without a draft yet
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, error, warn
from shared.cost_tracker import check_budget, record_cost
from shared.sandbox import validate_write_path

from tools.guardrail import check as guardrail_check


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_STORE = PROJECT_ROOT / "output" / "tickets.json"


INTENT_TO_KB_FILE = {
    "billing": "billing.md",
    "refund": "refund.md",
    "technical": "technical.md",
    "feedback": "general.md",
    "other": "general.md",
    "spam": None,  # no reply for spam
}


TEMPLATE_REPLIES = {
    "billing": (
        "Hi {first_name},\n\n"
        "Thanks for reaching out about your billing question. I've logged this and routed it "
        "to our Billing team, who'll reply within one business day. If it helps, you can also "
        "see your invoices in the dashboard under Billing → Invoices.\n\n"
        "Best,\nSupport team"
    ),
    "refund": (
        "Hi {first_name},\n\n"
        "Thanks for reaching out. I've logged your refund request and passed it to our Billing "
        "team. They review each request case-by-case and will reply with next steps within one "
        "business day.\n\n"
        "Best,\nSupport team"
    ),
    "technical": (
        "Hi {first_name},\n\n"
        "Thanks for flagging this. I've filed a ticket with Engineering so they can take a look. "
        "If you can share the browser + operating system you're on, plus a screenshot, that'll "
        "help them move faster.\n\n"
        "Best,\nSupport team"
    ),
    "feedback": (
        "Hi {first_name},\n\n"
        "Thank you for the note — I've passed this along to our Product team, who review feedback "
        "every week. We really appreciate you taking the time to write.\n\n"
        "Best,\nSupport team"
    ),
    "other": (
        "Hi {first_name},\n\n"
        "Thanks for reaching out — I've captured your message and a teammate will follow up "
        "within one business day.\n\n"
        "Best,\nSupport team"
    ),
}


def load_kb(kb_dir: Path, intent: str) -> str:
    """Load the KB file matching the intent. Returns empty string if none/spam."""
    filename = INTENT_TO_KB_FILE.get(intent)
    if not filename:
        return ""
    path = kb_dir / filename
    if not path.exists():
        warn(f"KB file missing for intent '{intent}': {path}")
        return ""
    return path.read_text()


def _first_name(ticket: dict) -> str:
    name = ticket.get("from_name") or ""
    first = re.split(r"[\s.]+", name.strip())[0] if name else ""
    # Don't use obviously non-name tokens
    if first.lower() in {"", "no-reply", "support", "team", "info", "notifications", "hello", "noreply"}:
        return "there"
    return first[:40] or "there"


def draft_template(ticket: dict) -> str:
    """Zero-cost fallback when no LLM key is configured."""
    intent = ticket.get("intent", "other")
    tpl = TEMPLATE_REPLIES.get(intent, TEMPLATE_REPLIES["other"])
    return tpl.format(first_name=_first_name(ticket))


def draft_llm(ticket: dict, kb_text: str, client, model: str, provider: str) -> str:
    """LLM draft. Falls back to template on error."""
    subject = (ticket.get("subject") or "")[:200]
    body = (ticket.get("body") or "")[:1800]
    first = _first_name(ticket)

    system = (
        "You are Atlas, drafting a first-pass support reply for a human to approve. "
        "You are warm, concise, and NEVER: quote prices/fees/discounts, promise timelines shorter than "
        "'one business day', guarantee any outcome, include the words 'guarantee'/'promise'/'commit'/"
        "'definitely', include PII, or speak for Engineering about root cause or ETA. "
        "If unsure, say a team member will follow up within one business day. "
        "Plain text only, 60-180 words, greeting + acknowledgement + next step + sign off as 'Support team'."
    )
    user = (
        f"Customer intent: {ticket.get('intent')}\n"
        f"Routed team: {ticket.get('team')}\n"
        f"Customer first name: {first}\n"
        f"Subject: {subject}\n\n"
        f'Customer wrote:\n"""\n{body}\n"""\n\n'
        f"Knowledge base (use ONLY this for facts — do not invent):\n---\n{kb_text}\n---\n\n"
        f"Draft the reply now. Plain text only."
    )

    try:
        check_budget()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        record_cost("draft_reply", 0.0003)
        return text
    except Exception as e:
        warn(f"LLM draft failed: {e} — falling back to template")
        return draft_template(ticket)


def get_llm_client():
    euri_key = get_optional("EURI_API_KEY")
    openrouter_key = get_optional("OPENROUTER_API_KEY")
    openai_key = get_optional("OPENAI_API_KEY")

    try:
        from openai import OpenAI
    except ImportError:
        return None, None, None

    if euri_key:
        return OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri_key), "gpt-4o-mini", "euri"
    if openrouter_key:
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key), "openai/gpt-4o-mini", "openrouter"
    if openai_key:
        return OpenAI(api_key=openai_key), "gpt-4o-mini", "openai"
    return None, None, None


def save_store(path: Path, records: list):
    validated = validate_write_path(str(path))
    validated.parent.mkdir(parents=True, exist_ok=True)
    validated.write_text(json.dumps(records, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Draft replies for tickets")
    parser.add_argument("--ticket-id", help="Single ticket to draft for")
    parser.add_argument("--all", action="store_true", help="Draft every ticket without one")
    parser.add_argument("--kb", default="./knowledge/", help="Knowledge base directory")
    parser.add_argument("--store", default=str(DEFAULT_STORE))
    parser.add_argument("--no-llm", action="store_true", help="Use templates only (no LLM)")
    args = parser.parse_args()

    if not (args.ticket_id or args.all):
        error("Provide --ticket-id or --all")
        sys.exit(1)

    load_env()

    store_path = Path(args.store) if Path(args.store).is_absolute() else PROJECT_ROOT / args.store
    if not store_path.exists():
        error(f"Ticket store not found: {store_path}")
        sys.exit(1)

    tickets = json.loads(store_path.read_text())
    kb_dir = Path(args.kb) if Path(args.kb).is_absolute() else PROJECT_ROOT / args.kb

    client, model, provider = (None, None, None) if args.no_llm else get_llm_client()
    if args.no_llm:
        info("--no-llm: template mode")
    elif client is None:
        info("No LLM key configured — template mode")

    drafted_ids = []
    for t in tickets:
        if args.ticket_id and t["ticket_id"] != args.ticket_id:
            continue
        if t.get("status") in ("sent", "rejected", "spam"):
            continue
        if t.get("draft") and not args.ticket_id:
            continue  # keep existing draft unless explicitly re-drafting

        kb_text = load_kb(kb_dir, t.get("intent", "other"))
        if client is not None and kb_text:
            raw = draft_llm(t, kb_text, client, model, provider)
        else:
            raw = draft_template(t)

        guarded = guardrail_check(raw, ticket_id=t["ticket_id"])
        t["draft"] = guarded["safe_text"]
        t["draft_raw"] = raw
        t["guardrail_flags"] = guarded["flags"]
        t["guardrail_blocked"] = guarded["blocked"]
        t["draft_method"] = f"llm:{provider}" if (client is not None and kb_text) else "template"
        t["updated_at"] = datetime.now(timezone.utc).isoformat()
        if guarded["blocked"]:
            t["needs_human_answer"] = True
        drafted_ids.append(t["ticket_id"])

    save_store(store_path, tickets)

    print(json.dumps({
        "status": "success",
        "drafted": len(drafted_ids),
        "ticket_ids": drafted_ids,
        "store": str(store_path),
    }))


if __name__ == "__main__":
    main()
