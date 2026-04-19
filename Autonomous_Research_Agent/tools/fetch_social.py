"""Fetch social signals for a competitor (best-effort, free tier only).

LinkedIn and Twitter/X have aggressive anti-scraping. Under the $1/run cost
cap, we use Tavily search with site: filters to pull recent posts/mentions.
If Tavily is unavailable we emit an empty payload — social is optional.

Usage:
    python tools/fetch_social.py --name "n8n" \\
        --handles "twitter:n8n_io,linkedin:n8n-io" --days 7

Output:
    .tmp/fetch/{name}_social.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from shared.env_loader import load_env, get_optional
from shared.logger import info, warn
from shared.retry import with_retry
from shared.sandbox import validate_write_path
from shared.sanitize import strip_pii


@with_retry(max_attempts=2, base_delay=3.0)
def tavily_site_search(api_key: str, query: str, limit: int) -> list:
    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": min(limit, 10),
            "search_depth": "basic",
            "include_answer": False,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    posts = []
    for r in data.get("results", []):
        posts.append({
            "title": strip_pii(r.get("title") or ""),
            "content": strip_pii((r.get("content") or "")[:400]),
            "url": r.get("url") or "",
            "published": r.get("published_date") or "",
            "origin": "tavily",
        })
    return posts


def parse_handles(handles_arg: str) -> list[dict]:
    """`twitter:name,linkedin:handle` → [{platform, handle}, ...]"""
    out = []
    for part in handles_arg.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        plat, handle = part.split(":", 1)
        plat = plat.strip().lower()
        handle = handle.strip()
        if plat and handle:
            out.append({"platform": plat, "handle": handle})
    return out


def main():
    parser = argparse.ArgumentParser(description="Fetch social signals for a competitor")
    parser.add_argument("--name", required=True)
    parser.add_argument("--handles", required=True, help='e.g. "twitter:n8n_io,linkedin:n8n-io"')
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    load_env()
    handles = parse_handles(args.handles)
    tavily_key = get_optional("TAVILY_API_KEY")

    posts_by_platform: dict = {}
    skipped: list = []

    if not tavily_key:
        warn("TAVILY_API_KEY not set — social fetch returns empty payload")
        for h in handles:
            skipped.append({**h, "reason": "tavily-missing"})
    else:
        for h in handles:
            plat = h["platform"]
            handle = h["handle"]
            if plat == "twitter":
                site = f"site:twitter.com/{handle} OR site:x.com/{handle}"
            elif plat == "linkedin":
                site = f"site:linkedin.com/company/{handle} OR site:linkedin.com/in/{handle}"
            else:
                skipped.append({**h, "reason": "unsupported-platform"})
                continue

            query = f"{site} {args.name}"
            try:
                results = tavily_site_search(tavily_key, query, args.limit)
                posts_by_platform[plat] = results
                info(f"social {plat}@{handle}: {len(results)} results")
            except Exception as e:
                warn(f"social fetch failed {plat}@{handle}: {e}")
                skipped.append({**h, "reason": f"fetch-error: {e}"})

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", args.name)
    out = args.output or f".tmp/fetch/{safe_name}_social.json"
    output_path = validate_write_path(str(Path(__file__).parent.parent / out))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "competitor": args.name,
        "source": "social",
        "handles": handles,
        "posts": posts_by_platform,
        "skipped": skipped,
        "counts": {p: len(v) for p, v in posts_by_platform.items()},
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({"status": "success", "output_path": str(output_path), "counts": payload["counts"]}))


if __name__ == "__main__":
    main()
