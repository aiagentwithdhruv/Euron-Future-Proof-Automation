"""Classify each email into intent + priority + sentiment + team.

Usage:
    python tools/classify_ticket.py --input .tmp/new_emails.json --output .tmp/classified.json
    python tools/classify_ticket.py --input .tmp/new_emails.json --no-llm     # keyword fallback only

LLM route (default): euri/gpt-4o-mini via the Euri free tier.
Fallback: deterministic keyword rules (same pattern as AI_News_Telegram_Bot/rank_news.py).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_optional
from shared.logger import info, error, warn
from shared.cost_tracker import check_budget, record_cost
from shared.sandbox import validate_write_path


VALID_INTENTS = {"billing", "technical", "refund", "feedback", "spam", "other"}
VALID_PRIORITIES = {"P1", "P2", "P3", "P4"}
VALID_SENTIMENTS = {"positive", "neutral", "negative", "angry"}
VALID_TEAMS = {"billing", "engineering", "success", "trust-safety", "triage"}


# Keyword rules — the fallback classifier
INTENT_KEYWORDS = {
    "billing": ["invoice", "charge", "charged", "billing", "payment", "card declined", "subscription", "receipt"],
    "refund": ["refund", "money back", "cancel subscription", "return", "dispute", "chargeback"],
    "technical": ["bug", "error", "crash", "not working", "broken", "can't log", "cannot log", "login", "outage", "down", "api", "500", "403"],
    "feedback": ["thank", "thanks", "awesome", "love", "feedback", "suggestion", "feature request"],
    "spam": ["unsubscribe", "newsletter", "promo", "buy now", "limited offer", "click here to win"],
}

P1_PATTERN = r"\b(outage|down|broken|urgent|emergency|asap|can['’]?t login|cannot login|data loss|security|breach|blocked|stuck)\b"

SENTIMENT_RULES = [
    ("angry", r"\b(furious|angry|outraged|disgust|terrible|awful|worst|unacceptable|ridiculous|scam|fraud)\b"),
    ("negative", r"\b(not happy|disappointed|frustrat|annoy|broken|bug|problem|issue|wrong|fail)\b"),
    ("positive", r"\b(love|great|awesome|amazing|thank|excellent|happy|brilliant)\b"),
]

INTENT_TO_TEAM = {
    "billing": "billing",
    "refund": "billing",
    "technical": "engineering",
    "feedback": "success",
    "spam": "trust-safety",
    "other": "triage",
}


def classify_keyword(email_obj: dict) -> dict:
    """Deterministic fallback — works with zero API keys."""
    text = f"{email_obj.get('subject', '')} {email_obj.get('body', '')}".lower()

    # intent
    scored = {name: sum(1 for kw in kws if kw in text) for name, kws in INTENT_KEYWORDS.items()}
    best = max(scored, key=scored.get)
    intent = best if scored[best] > 0 else "other"

    # priority — derived from intent + P1 check (prompt spec:
    # P1 outage, P2 billing/refund/tech, P3 question-default, P4 pure feedback/spam)
    if re.search(P1_PATTERN, text, re.IGNORECASE):
        priority = "P1"
    elif intent in ("billing", "refund"):
        priority = "P2"
    elif intent == "technical":
        priority = "P2"
    elif intent in ("feedback", "spam"):
        priority = "P4"
    else:
        priority = "P3"

    # sentiment
    sentiment = "neutral"
    for label, pattern in SENTIMENT_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            sentiment = label
            break

    team = INTENT_TO_TEAM.get(intent, "triage")

    return {
        "intent": intent,
        "priority": priority,
        "sentiment": sentiment,
        "team": team,
        "reasoning": f"keyword: intent={intent} (score {scored[best]}), priority rule matched={priority}",
        "method": "keyword",
    }


def classify_llm(email_obj: dict, client, model: str, provider: str) -> dict:
    """LLM-backed classifier. Falls back to keywords on any failure."""
    subject = (email_obj.get("subject") or "")[:200]
    body = (email_obj.get("body") or "")[:2000]

    system = (
        "You are a strict support-ticket classifier. Return ONLY valid JSON matching this schema — "
        "no prose, no markdown, no code fences. "
        '{"intent":"billing|technical|refund|feedback|spam|other",'
        '"priority":"P1|P2|P3|P4",'
        '"sentiment":"positive|neutral|negative|angry",'
        '"team":"billing|engineering|success|trust-safety|triage",'
        '"reasoning":"one sentence, <=140 chars"}'
    )
    user = (
        "Priority: P1=outage/cannot-login/data-loss/security, P2=billing-error/bug, P3=question, P4=thanks/newsletter.\n"
        "Team: billing=billing/refund, engineering=technical, success=feedback/onboarding, trust-safety=spam/abuse, triage=unclear.\n\n"
        f"Email subject: {subject}\n"
        f"Email body:\n{body}\n\n"
        "Classify. Return ONLY the JSON object."
    )

    try:
        check_budget()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.1,
            max_tokens=220,
        )
        content = resp.choices[0].message.content.strip()
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            warn("Classifier returned no JSON, falling back to keywords")
            return classify_keyword(email_obj)
        data = json.loads(match.group())

        # validate enum values — any deviation → fallback (fail closed)
        if data.get("intent") not in VALID_INTENTS:
            data["intent"] = "other"
        if data.get("priority") not in VALID_PRIORITIES:
            data["priority"] = "P3"
        if data.get("sentiment") not in VALID_SENTIMENTS:
            data["sentiment"] = "neutral"
        if data.get("team") not in VALID_TEAMS:
            data["team"] = INTENT_TO_TEAM.get(data["intent"], "triage")

        data["method"] = f"llm:{provider}"
        record_cost("classify_ticket", 0.0001)
        return data
    except Exception as e:
        warn(f"LLM classification failed: {e} — falling back to keywords")
        return classify_keyword(email_obj)


def get_llm_client():
    """Return (client, model, provider) or (None, None, None) if no key configured."""
    euri_key = get_optional("EURI_API_KEY")
    openrouter_key = get_optional("OPENROUTER_API_KEY")
    openai_key = get_optional("OPENAI_API_KEY")

    try:
        from openai import OpenAI
    except ImportError:
        warn("openai SDK not installed — keyword mode only")
        return None, None, None

    if euri_key:
        return OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri_key), "gpt-4o-mini", "euri"
    if openrouter_key:
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key), "openai/gpt-4o-mini", "openrouter"
    if openai_key:
        return OpenAI(api_key=openai_key), "gpt-4o-mini", "openai"
    return None, None, None


def main():
    parser = argparse.ArgumentParser(description="Classify support emails")
    parser.add_argument("--input", default=".tmp/new_emails.json", help="Fetched emails JSON")
    parser.add_argument("--output", default=".tmp/classified.json", help="Classified tickets output")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM, keyword rules only")
    args = parser.parse_args()

    load_env()

    in_path = Path(__file__).parent.parent / args.input
    if not in_path.exists():
        error(f"Input file not found: {in_path}")
        sys.exit(1)

    emails = json.loads(in_path.read_text())
    info(f"Classifying {len(emails)} emails")

    client, model, provider = (None, None, None) if args.no_llm else get_llm_client()
    if args.no_llm:
        info("--no-llm: keyword mode")
    elif client is None:
        info("No LLM key configured — keyword mode")

    results = []
    for e in emails:
        if client is not None:
            label = classify_llm(e, client, model, provider)
        else:
            label = classify_keyword(e)
        results.append({**e, **label})

    out_path = validate_write_path(str(Path(__file__).parent.parent / args.output))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    summary = {"total": len(results)}
    for intent in VALID_INTENTS:
        n = sum(1 for r in results if r["intent"] == intent)
        if n:
            summary[intent] = n
    print(json.dumps({"status": "success", "output_path": str(out_path), **summary}))


if __name__ == "__main__":
    main()
