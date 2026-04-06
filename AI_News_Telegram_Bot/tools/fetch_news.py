"""Fetch AI news from multiple sources: NewsAPI + RSS feeds + Tavily (optional).

Usage:
    python tools/fetch_news.py --sources newsapi,rss --limit 20
    python tools/fetch_news.py --sources newsapi,rss,tavily --limit 30

Output:
    Writes JSON array to .tmp/raw_news.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import feedparser
from shared.env_loader import load_env, get_required, get_optional
from shared.logger import info, error
from shared.retry import with_retry
from shared.sandbox import validate_write_path


RSS_FEEDS = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
]


@with_retry(max_attempts=2, base_delay=3.0)
def fetch_newsapi(api_key: str, limit: int) -> list:
    """Fetch from NewsAPI — broad AI news from 80K+ sources."""
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    resp = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": "artificial intelligence OR AI deployment OR LLM OR machine learning",
            "language": "en",
            "sortBy": "publishedAt",
            "from": yesterday,
            "pageSize": min(limit, 100),
            "apiKey": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for a in data.get("articles", []):
        if a.get("title") and "[Removed]" not in a.get("title", ""):
            articles.append({
                "title": a["title"],
                "description": a.get("description", ""),
                "url": a.get("url", ""),
                "source": a.get("source", {}).get("name", "Unknown"),
                "published": a.get("publishedAt", ""),
                "origin": "newsapi",
            })
    info(f"NewsAPI: fetched {len(articles)} articles")
    return articles


def fetch_rss() -> list:
    """Fetch from RSS feeds — TechCrunch, The Verge, Ars, MIT Tech Review."""
    articles = []
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                articles.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", "")[:300],
                    "url": entry.get("link", ""),
                    "source": feed_info["name"],
                    "published": entry.get("published", ""),
                    "origin": "rss",
                })
        except Exception as e:
            error(f"RSS feed failed: {feed_info['name']}", error=str(e))
    info(f"RSS: fetched {len(articles)} articles from {len(RSS_FEEDS)} feeds")
    return articles


@with_retry(max_attempts=2, base_delay=3.0)
def fetch_tavily(api_key: str, limit: int) -> list:
    """Fetch from Tavily — AI-powered search for recent AI news."""
    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": "latest artificial intelligence news today",
            "max_results": min(limit, 10),
            "search_depth": "basic",
            "include_answer": False,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    articles = []
    for r in data.get("results", []):
        articles.append({
            "title": r.get("title", ""),
            "description": r.get("content", "")[:300],
            "url": r.get("url", ""),
            "source": "Tavily",
            "published": "",
            "origin": "tavily",
        })
    info(f"Tavily: fetched {len(articles)} articles")
    return articles


def deduplicate(articles: list) -> list:
    """Remove duplicate articles by URL and similar titles."""
    seen_urls = set()
    seen_titles = set()
    unique = []
    for a in articles:
        url = a.get("url", "").rstrip("/")
        title_key = a.get("title", "").lower().strip()[:60]
        if url and url in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title_key)
        unique.append(a)
    return unique


def main():
    parser = argparse.ArgumentParser(description="Fetch AI news from multiple sources")
    parser.add_argument("--sources", default="newsapi,rss", help="Comma-separated: newsapi,rss,tavily")
    parser.add_argument("--limit", type=int, default=20, help="Max articles per source")
    parser.add_argument("--output", default=".tmp/raw_news.json", help="Output file path")
    args = parser.parse_args()

    load_env()
    sources = [s.strip() for s in args.sources.split(",")]
    all_articles = []

    if "newsapi" in sources:
        api_key = get_optional("NEWSAPI_KEY")
        if api_key:
            all_articles.extend(fetch_newsapi(api_key, args.limit))
        else:
            error("NewsAPI key not set — skipping")

    if "rss" in sources:
        all_articles.extend(fetch_rss())

    if "tavily" in sources:
        api_key = get_optional("TAVILY_API_KEY")
        if api_key:
            all_articles.extend(fetch_tavily(api_key, args.limit))
        else:
            error("Tavily key not set — skipping")

    unique = deduplicate(all_articles)
    info(f"Total: {len(all_articles)} fetched, {len(unique)} after dedup")

    output_path = validate_write_path(str(Path(__file__).parent.parent / args.output))
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(unique, indent=2, ensure_ascii=False))
    print(json.dumps({"status": "success", "output_path": str(output_path), "articles": len(unique)}))


if __name__ == "__main__":
    main()
