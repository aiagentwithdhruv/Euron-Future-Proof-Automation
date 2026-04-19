"""Support module — draft_reply.

Takes a support email plus the top-k KB chunks (from RAG_Knowledge_Chatbot
once wired, or from `knowledge/*.md` files locally) and produces a draft.

Guardrails: the drafter MUST NOT invent prices, SLAs, or make binding
commitments. We enforce this via:
  1. A strict prompt with explicit 'do not' rules.
  2. A post-filter that strips obvious price/refund-amount leaks before the
     draft is shown to the approver.

Nothing in this module auto-sends. It writes a draft + citations into
`.tmp/tickets/<id>.draft.md` — a human approver is in the loop.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools import llm
from tools._bootstrap import project_root, tmp_dir

logger = get_logger(__name__)


PRICE_PATTERNS = [
    r"\$\s*\d+(?:\.\d+)?",
    r"₹\s*\d+(?:,\d+)*(?:\.\d+)?",
    r"rs\.?\s*\d+",
    r"\bINR\s*\d+",
    r"\bUSD\s*\d+",
]


def _load_kb(knowledge_dir: Optional[Path] = None) -> list[dict]:
    base = knowledge_dir or (project_root() / "knowledge")
    if not base.exists():
        return []
    out = []
    for f in base.glob("*.md"):
        text = f.read_text()
        # Crude chunking — heading-delimited, capped at 800 chars per chunk.
        chunks = re.split(r"\n(?=#{1,3}\s)", text)
        for idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue
            out.append({"source": f.name, "chunk_id": f"{f.stem}#{idx}", "text": chunk[:800]})
    return out


def retrieve(query: str, knowledge_dir: Optional[Path] = None, k: int = 3) -> list[dict]:
    """Keyword-overlap retrieval. Cheap, deterministic, good enough for a
    product KB whose size is measured in dozens of pages."""
    kb = _load_kb(knowledge_dir)
    q_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for chunk in kb:
        c_words = set(re.findall(r"\w+", chunk["text"].lower()))
        score = len(q_words & c_words)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:k]]


def strip_prices(text: str) -> str:
    cleaned = text
    for pat in PRICE_PATTERNS:
        cleaned = re.sub(pat, "[price redacted]", cleaned, flags=re.IGNORECASE)
    return cleaned


def draft(
    *,
    subject: str,
    body: str,
    classification: dict,
    knowledge_dir: Optional[Path] = None,
) -> dict:
    chunks = retrieve(f"{subject} {body}", knowledge_dir=knowledge_dir)
    context = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)

    try:
        data = llm.generate_json(
            "draft_reply_v1",
            {
                "subject": subject[:200],
                "body": body[:2000],
                "intent": classification.get("intent"),
                "sentiment": classification.get("sentiment"),
                "context": context or "(no KB hit)",
            },
            temperature=0.3,
            max_tokens=500,
        )
        reply_subject = data.get("subject") or f"Re: {subject}"
        reply_body = data.get("body") or ""
    except (llm.LLMUnavailable, json.JSONDecodeError) as e:
        logger.info(f"draft fallback (no LLM): {e}")
        reply_subject = f"Re: {subject}"
        reply_body = (
            f"Hi,\n\n"
            f"Thanks for getting in touch. A team member will pick this up shortly — we usually "
            f"reply within 1 business day.\n\n"
            f"— Customer Support"
        )

    # Guardrails: strip prices / commitments. We never send the raw LLM body.
    reply_body = strip_prices(reply_body)
    reply_body = re.sub(r"(within|in)\s+\d+\s+(hours?|days?|minutes?)", "[timing varies]", reply_body, flags=re.IGNORECASE)

    return {
        "subject": reply_subject,
        "body": reply_body,
        "citations": [c["chunk_id"] for c in chunks],
        "guardrails_applied": ["price_redaction", "timing_neutralisation"],
    }


def persist(ticket_id: str, payload: dict) -> Path:
    out_dir = tmp_dir() / "tickets"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ticket_id}.draft.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return path


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Draft a support reply for a ticket")
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--intent", default="other")
    parser.add_argument("--sentiment", default="neutral")
    args = parser.parse_args()

    d = draft(
        subject=args.subject,
        body=args.body,
        classification={"intent": args.intent, "sentiment": args.sentiment},
    )
    path = persist(args.ticket_id, d)
    print(json.dumps({"draft_path": str(path), **d}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
