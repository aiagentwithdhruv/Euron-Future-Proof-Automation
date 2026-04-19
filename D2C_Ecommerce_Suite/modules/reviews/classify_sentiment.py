"""Reviews module — classify_sentiment.

Maps a normalised review into {positive, neutral, negative} + a short
reason. Rule-based baseline always runs first (star rating + keyword
scan), which we then *refine* with the LLM only when ambiguous
(3-star reviews, or 4-5 star with negative keywords).

Why 'always rule first': reviews are high-volume and the baseline gets
>90% right. We spend LLM tokens only on the cases that matter.
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

logger = get_logger(__name__)


NEG_KEYWORDS = [
    "broken", "damaged", "defect", "late", "never", "worst", "awful", "terrible",
    "horrible", "disappointed", "scam", "fraud", "refund", "return", "wrong size",
]
POS_KEYWORDS = ["love", "great", "excellent", "fantastic", "amazing", "perfect", "happy"]


def _rule(review: dict) -> dict:
    rating = int(review.get("rating") or 0)
    text = (review.get("text") or "").lower()
    has_neg = any(re.search(rf"\b{w}\b", text) for w in NEG_KEYWORDS)
    has_pos = any(re.search(rf"\b{w}\b", text) for w in POS_KEYWORDS)

    if rating >= 4 and not has_neg:
        return {"sentiment": "positive", "ambiguous": has_neg}
    if rating <= 2 or has_neg:
        return {"sentiment": "negative", "ambiguous": rating >= 4}
    if rating == 3:
        return {"sentiment": "neutral", "ambiguous": True}
    return {"sentiment": "positive" if has_pos else "neutral", "ambiguous": not (has_pos or has_neg)}


def classify(review: dict, *, use_llm: bool = True) -> dict:
    baseline = _rule(review)
    if not baseline["ambiguous"] or not use_llm:
        return {**baseline, "classifier": "rule"}

    try:
        data = llm.generate_json(
            "classify_sentiment",
            {"rating": review.get("rating"), "text": (review.get("text") or "")[:800]},
            temperature=0.1,
            max_tokens=120,
        )
        sentiment = data.get("sentiment")
        if sentiment not in ("positive", "neutral", "negative"):
            return {**baseline, "classifier": "rule", "llm_invalid": True}
        return {"sentiment": sentiment, "reason": data.get("reason"), "classifier": "llm"}
    except (llm.LLMUnavailable, json.JSONDecodeError):
        return {**baseline, "classifier": "rule"}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Classify sentiment for one or more reviews")
    parser.add_argument("--review-file", required=True, help="Path to reviews JSONL")
    args = parser.parse_args()
    out = []
    with open(args.review_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out.append({**r, "sentiment_classification": classify(r)})
    print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
