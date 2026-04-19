"""
Orchestrator — the ONLY module allowed to combine retrieval + generation.
All three RAG layers (ingestion, retrieval, generation) stay independent;
this file wires retrieval -> confidence gate -> generation -> citation gate.

Gates:
  1. Confidence gate: if top similarity < CONFIDENCE_THRESHOLD, skip generation
     and return {status: "escalated"}.
  2. Citation gate: if the generator returns no valid citations, escalate.
     Rule: no cite = no send.

Usage:
    python tools/ask.py --query "What's your refund policy?"
    python tools/ask.py --query "..." --k 5 --channel web
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402
from tools.generation.answer import generate  # noqa: E402
from tools.retrieval.search import search  # noqa: E402

logger = get_logger(__name__)


def _escalated(query: str, reason: str, top_sim: float, channel: str) -> dict:
    return {
        "status": "escalated",
        "query": query,
        "answer": None,
        "citations": [],
        "confidence": top_sim,
        "reason": reason,
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def ask(query: str, k: int | None = None, channel: str = "cli") -> dict:
    threshold = config.get_float("CONFIDENCE_THRESHOLD", 0.6)
    top_k = k or config.get_int("TOP_K", 5)
    started = time.time()

    retrieval = search(query, k=top_k)
    top_sim = retrieval["top_similarity"]
    chunks = retrieval["results"]

    if not chunks or top_sim < threshold:
        result = _escalated(
            query,
            reason=f"low_confidence (top={top_sim:.2f} < {threshold})",
            top_sim=top_sim,
            channel=channel,
        )
        logger.info(f"escalated: {result['reason']}")
        result["duration_ms"] = int((time.time() - started) * 1000)
        return result

    gen = generate(query, chunks)
    if not gen.get("grounded") or not gen.get("citations"):
        result = _escalated(
            query,
            reason="no_citations_from_generator",
            top_sim=top_sim,
            channel=channel,
        )
        result["duration_ms"] = int((time.time() - started) * 1000)
        return result

    # Overall confidence = min(retrieval top_sim, generator self-reported conf).
    confidence = min(top_sim, gen.get("confidence") or top_sim)

    return {
        "status": "answered",
        "query": query,
        "answer": gen["answer"],
        "citations": gen["citations"],
        "confidence": confidence,
        "retrieval_top_similarity": top_sim,
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": int((time.time() - started) * 1000),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Ask the RAG chatbot a question.")
    p.add_argument("--query", required=True)
    p.add_argument("--k", type=int, default=None)
    p.add_argument("--channel", default="cli", help="cli | web | whatsapp")
    args = p.parse_args()

    out = ask(args.query, k=args.k, channel=args.channel)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["status"] == "answered" else 2


if __name__ == "__main__":
    raise SystemExit(main())
