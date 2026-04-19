"""Reviews module — auto_reply.

Positive reviews: thank the reviewer immediately.
Neutral reviews : draft a polite follow-up for human approval, don't send.
Negative reviews: escalate to the CX team via Slack + draft for approval.

We never publish replies onto third-party review platforms from this module
— that would need platform-specific OAuth (Trustpilot/Google). Instead, we
email the reviewer directly when we have their address, which is the
highest-leverage action regardless of platform.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from modules.reviews import classify_sentiment
from tools import llm
from tools._bootstrap import tmp_dir
from tools.airtable_client import AirtableStore, table_name
from tools.senders import send_email, send_slack

logger = get_logger(__name__)


def _compose(review: dict, sentiment: str) -> dict:
    name = (review.get("author") or "there").split()[0]
    prompt_name = "review_reply_positive" if sentiment == "positive" else "review_reply_negative"

    try:
        data = llm.generate_json(
            prompt_name,
            {
                "review_text": (review.get("text") or "")[:600],
                "customer_name": name,
                "rating": review.get("rating"),
            },
            temperature=0.4,
            max_tokens=300,
        )
        subject = data.get("subject") or ("Thanks for the review" if sentiment == "positive" else "Sorry we fell short")
        body = data.get("body") or ""
        if not body:
            raise ValueError("empty body")
        return {"subject": subject, "body": body}
    except (llm.LLMUnavailable, json.JSONDecodeError, ValueError):
        if sentiment == "positive":
            subject = "Thank you for the review!"
            body = (
                f"Hi {name},\n\n"
                f"Thank you so much for taking the time to share that — it genuinely helps other "
                f"shoppers, and it makes our day.\n\n"
                f"If there's anything else we can do for you, just reply.\n\n"
                f"— The Team"
            )
        else:
            subject = "We'd like to make this right"
            body = (
                f"Hi {name},\n\n"
                f"We're really sorry your experience wasn't what we hoped. "
                f"I'd like to understand what happened and see how we can make it right — "
                f"would you reply with your order number?\n\n"
                f"— CX Team"
            )
        return {"subject": subject, "body": body}


def handle_one(review: dict, *, dry_run: bool = True) -> dict:
    classification = classify_sentiment.classify(review)
    sentiment = classification["sentiment"]
    copy = _compose(review, sentiment)

    record = {
        "ReviewID": review.get("review_id"),
        "Platform": review.get("platform"),
        "Rating": review.get("rating"),
        "Sentiment": sentiment,
        "Author": review.get("author"),
        "Status": "processed",
    }
    AirtableStore().create(table_name("reviews"), record)

    result: dict = {
        "status": "success",
        "review_id": review.get("review_id"),
        "sentiment": sentiment,
        "classifier": classification.get("classifier"),
    }

    if sentiment == "positive" and review.get("author_email"):
        # Auto-reply to positive reviews — low risk.
        result["reply"] = send_email(
            to=review["author_email"],
            subject=copy["subject"],
            body=copy["body"],
            dry_run=dry_run,
        )

    if sentiment == "negative":
        # Always escalate to Slack. Draft sits for human approval.
        draft_path = tmp_dir() / "review_drafts" / f"{review.get('review_id') or 'unknown'}.json"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(
            json.dumps({"review": review, "draft": copy, "sentiment": sentiment}, indent=2, ensure_ascii=False)
        )
        alert = (
            f":rotating_light: *Negative review* — {review.get('rating')}\u2605 "
            f"from {review.get('author') or 'anon'} on {review.get('platform')}. "
            f"Draft reply queued at `{draft_path.name}`."
        )
        result["escalation"] = send_slack(message=alert, dry_run=dry_run)
        result["draft_path"] = str(draft_path)

    if sentiment == "neutral":
        # Neutral: draft for approval, no send, no escalation.
        draft_path = tmp_dir() / "review_drafts" / f"{review.get('review_id') or 'unknown'}.json"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(
            json.dumps({"review": review, "draft": copy, "sentiment": sentiment}, indent=2, ensure_ascii=False)
        )
        result["draft_path"] = str(draft_path)

    return result


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Reply / escalate for reviews")
    parser.add_argument("--review-file", required=True, help="JSONL of reviews")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    outs = []
    with open(args.review_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            outs.append(handle_one(json.loads(line), dry_run=args.dry_run))
    print(json.dumps({"processed": len(outs), "results": outs}, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
