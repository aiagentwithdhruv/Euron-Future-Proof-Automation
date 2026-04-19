"""Reviews module — collect_reviews.

Pluggable fetchers — each platform has its own function and its own
creds. MVP ships with:

  - `from_shopify_json(path)`  — loads a JSON dump exported from a Shopify
                                 app (e.g. Judge.me, Yotpo). This is the
                                 portable path until/unless we wire a
                                 native API.
  - `from_local(path)`         — reads a local JSONL for dev fixtures.

Google + Trustpilot stubs intentionally raise `NotImplementedError` so the
contract is explicit: the call exists; production creds don't yet.

Each record is normalised into the Review shape used by the rest of the
module:
    { review_id, platform, product_id, rating (1-5), text, author,
      author_email, created_at }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools._bootstrap import tmp_dir

logger = get_logger(__name__)


def _normalize_shopify_review(raw: dict) -> dict:
    return {
        "review_id": str(raw.get("id") or raw.get("review_id") or ""),
        "platform": "shopify",
        "product_id": str(raw.get("product_id") or ""),
        "rating": int(raw.get("rating") or raw.get("stars") or 0),
        "text": raw.get("body") or raw.get("review") or "",
        "author": raw.get("author") or raw.get("reviewer") or "",
        "author_email": raw.get("email"),
        "created_at": raw.get("created_at"),
    }


def from_shopify_json(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text())
    items = data if isinstance(data, list) else data.get("reviews") or []
    return [_normalize_shopify_review(r) for r in items if r]


def from_local(path: Path) -> list[dict]:
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def from_google(place_id: str) -> list[dict]:
    raise NotImplementedError(
        "Google Places reviews require a Places API key + paid plan. "
        "Wire it in `from_google` after Angelina confirms the API key + budget."
    )


def from_trustpilot(business_unit_id: str) -> list[dict]:
    raise NotImplementedError(
        "Trustpilot requires their Business API. Wire after creds are issued."
    )


def save(reviews: Iterable[dict]) -> Path:
    sink = tmp_dir() / "reviews.jsonl"
    with sink.open("a") as f:
        for r in reviews:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return sink


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Collect reviews from a source")
    parser.add_argument("--shopify-json", help="Path to a Shopify-shaped reviews JSON file")
    parser.add_argument("--local", help="Path to a reviews.jsonl fixture")
    args = parser.parse_args()

    if args.shopify_json:
        reviews = from_shopify_json(Path(args.shopify_json))
    elif args.local:
        reviews = from_local(Path(args.local))
    else:
        parser.error("Use --shopify-json or --local")
        return 2

    path = save(reviews)
    print(json.dumps({"status": "success", "collected": len(reviews), "path": str(path)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
