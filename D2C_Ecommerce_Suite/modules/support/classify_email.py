"""Support module — classify_email.

Classifies a customer email into: intent, priority, sentiment, team.

Mirrors the AI_Support_Ticket_System contract so that project's classifier
can adopt this module wholesale (or vice-versa). When the LLM is unavailable
a rule-based fallback runs instead — the suite must never refuse a ticket
just because Euri is down.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools import llm

logger = get_logger(__name__)


INTENTS = ["order_status", "refund", "shipping", "product_question", "defect", "billing", "feedback", "spam", "other"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
TEAMS = ["logistics", "refunds", "cx", "tech", "growth"]

RULE_KEYWORDS = {
    "refund": [r"\brefund\b", r"\breturn\b", r"\bmoney back\b"],
    "shipping": [r"\btracking\b", r"\bship(ped|ping)?\b", r"\bwhere is\b", r"\bdelayed\b"],
    "order_status": [r"\border( status)?\b", r"\bwhen will\b", r"\betc\b"],
    "defect": [r"\bbroken\b", r"\bdamaged\b", r"\bdefect\b", r"\bwrong\b"],
    "billing": [r"\bcharg(e|ed)\b", r"\bcard\b", r"\binvoice\b", r"\bdouble charge\b"],
    "product_question": [r"\bsize\b", r"\bfit\b", r"\bmaterial\b", r"\bingredient\b", r"\binstruction\b"],
    "feedback": [r"\blov(e|ed)\b", r"\bgreat\b", r"\bawesome\b", r"\bamazing\b"],
    "spam": [r"\bclick here\b", r"\bviagra\b", r"\bloan\b", r"\bbitcoin\b"],
}

P1_KEYS = [r"\burgent\b", r"\bimmediately\b", r"\basap\b", r"\blegal\b", r"\bchargeback\b", r"\bchildren?\b"]


def rule_classify(subject: str, body: str) -> dict:
    text = f"{subject}\n{body}".lower()

    intent = "other"
    for name, patterns in RULE_KEYWORDS.items():
        if any(re.search(p, text) for p in patterns):
            intent = name
            break

    priority = "P3"
    if any(re.search(p, text) for p in P1_KEYS):
        priority = "P1"
    elif intent in ("defect", "billing", "refund"):
        priority = "P2"
    elif intent in ("feedback", "spam"):
        priority = "P4"

    sentiment = "neutral"
    if any(w in text for w in ["angry", "terrible", "worst", "awful", "hate"]):
        sentiment = "negative"
    elif any(w in text for w in ["love", "great", "thank", "awesome"]):
        sentiment = "positive"

    team = {
        "order_status": "logistics",
        "shipping": "logistics",
        "refund": "refunds",
        "billing": "refunds",
        "defect": "cx",
        "product_question": "cx",
        "feedback": "growth",
        "spam": "cx",
        "other": "cx",
    }[intent]

    return {
        "intent": intent,
        "priority": priority,
        "sentiment": sentiment,
        "team": team,
        "classifier": "rule-based",
    }


def classify(subject: str, body: str) -> dict:
    # Clamp inputs to keep prompt small and prevent prompt-injection via long bodies.
    subject = (subject or "")[:200]
    body = (body or "")[:2000]

    try:
        data = llm.generate_json(
            "classify_ticket_v1",
            {"subject": subject, "body": body, "intents": ", ".join(INTENTS), "priorities": ", ".join(PRIORITIES), "teams": ", ".join(TEAMS)},
            temperature=0.1,
            max_tokens=200,
        )
    except llm.LLMUnavailable as e:
        logger.info(f"classify -> rule fallback: {e}")
        return rule_classify(subject, body)
    except json.JSONDecodeError:
        logger.warning("LLM returned unparseable JSON — rule fallback")
        return rule_classify(subject, body)

    # Normalise + validate against the known enums.
    intent = data.get("intent") if data.get("intent") in INTENTS else "other"
    priority = data.get("priority") if data.get("priority") in PRIORITIES else "P3"
    sentiment = data.get("sentiment") if data.get("sentiment") in ("positive", "negative", "neutral") else "neutral"
    team = data.get("team") if data.get("team") in TEAMS else "cx"
    return {
        "intent": intent,
        "priority": priority,
        "sentiment": sentiment,
        "team": team,
        "classifier": "llm",
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Classify a support email")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    args = parser.parse_args()
    print(json.dumps(classify(args.subject, args.body), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
