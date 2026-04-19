"""Fetch news mentions for a competitor (NewsAPI + Tavily).

Adapts the pattern from AI_News_Telegram_Bot/tools/fetch_news.py — keyword-
targeted queries, dedup by URL/title, PII stripped. RSS isn't competitor-
specific so it's omitted here.

Usage:
    python tools/fetch_news.py --name "n8n" --keywords "n8n,n8n.io" --days 7 --limit 15

Output:
    .tmp/fetch/{name}_news.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

from shared.env_loader import load_env, get_optional
from shared.logger import info, warn, error
from shared.retry import with_retry
from shared.sandbox import validate_write_path
from shared.sanitize import strip_pii


@with_retry(max_attempts=2, base_delay=3.0)
def fetch_newsapi(api_key: str, query: str, days: int, limit: int) -> list:
    from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "from": from_date,
            "pageSize": min(limit, 50),
            "apiKey": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for a in data.get("articles", []):
        title = a.get("title") or ""
        if not title or "[Removed]" in title:
            continue
        articles.append({
            "title": strip_pii(title),
            "description": strip_pii((a.get("description") or "")[:400]),
            "url": a.get("url") or "",
            "source": (a.get("source") or {}).get("name", "Unknown"),
            "published": a.get("publishedAt") or "",
            "origin": "newsapi",
        })
    info(f"newsapi: {len(articles)} articles for query='{query}'")
    return articles


@with_retry(max_attempts=2, base_delay=3.0)
def fetch_tavily(api_key: str, query: str, limit: int) -> list:
    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": query,
            "max_results": min(limit, 10),
            "search_depth": "basic",
            "include_answer": False,
            "topic": "news",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for r in data.get("results", []):
        articles.append({
            "title": strip_pii(r.get("title") or ""),
            "description": strip_pii((r.get("content") or "")[:400]),
            "url": r.get("url") or "",
            "source": "Tavily",
            "published": r.get("published_date") or "",
            "origin": "tavily",
        })
    info(f"tavily: {len(articles)} articles for query='{query}'")
    return articles


def dedupe(articles: list) -> list:
    seen_urls, seen_titles, unique = set(), set(), []
    for a in articles:
        url = (a.get("url") or "").rstrip("/")
        title = (a.get("title") or "").lower().strip()[:80]
        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(a)
    return unique


def build_query(keywords: list[str]) -> str:
    cleaned = [k.strip() for k in keywords if k.strip()]
    if not cleaned:
        return ""
    # Quote multi-word terms, OR them together.
    parts = [f'"{k}"' if " " in k else k for k in cleaned]
    return " OR ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Fetch news for a competitor")
    parser.add_argument("--name", required=True)
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    load_env()
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    query = build_query(keywords)
    if not query:
        error("No keywords provided")
        sys.exit(1)

    all_articles: list = []

    newsapi_key = get_optional("NEWSAPI_KEY")
    if newsapi_key:
        try:
            all_articles.extend(fetch_newsapi(newsapi_key, query, args.days, args.limit))
        except Exception as e:
            warn(f"newsapi failed: {e}")
    else:
        warn("NEWSAPI_KEY not set — skipping NewsAPI")

    tavily_key = get_optional("TAVILY_API_KEY")
    if tavily_key:
        try:
            all_articles.extend(fetch_tavily(tavily_key, query, args.limit))
        except Exception as e:
            warn(f"tavily failed: {e}")
    else:
        warn("TAVILY_API_KEY not set — skipping Tavily")

    unique = dedupe(all_articles)
    info(f"news total: {len(all_articles)} fetched, {len(unique)} after dedup")

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", args.name)
    out = args.output or f".tmp/fetch/{safe_name}_news.json"
    output_path = validate_write_path(str(Path(__file__).parent.parent / out))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "competitor": args.name,
        "source": "news",
        "query": query,
        "articles": unique,
        "counts": {"fetched": len(all_articles), "unique": len(unique)},
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({"status": "success", "output_path": str(output_path), "counts": payload["counts"]}))


if __name__ == "__main__":
    main()
