"""Fetch a competitor's public pages (homepage + pricing + blog + about).

Respects robots.txt, rate-limits 3s between requests to the same domain,
strips PII from stored content, and emits a normalized JSON snapshot input.

Usage:
    python tools/fetch_competitor.py --name "n8n" \\
        --url "https://n8n.io" \\
        --url "https://n8n.io/pricing" \\
        --rate-limit 3

Output:
    .tmp/fetch/{name}_site.json  (list of page records)
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

from shared.logger import info, warn, error
from shared.retry import with_retry
from shared.sandbox import validate_write_path
from shared.sanitize import sanitize_url, strip_pii
from shared.robots_check import is_allowed, wait_for_rate_limit, safe_headers


MAX_BODY_CHARS = 20_000       # cap per page stored
MAX_LINK_COUNT = 40           # cap links extracted


@with_retry(max_attempts=2, base_delay=5.0)
def _http_get(url: str, timeout: int) -> requests.Response:
    resp = requests.get(url, headers=safe_headers(), timeout=timeout, allow_redirects=True)
    return resp


def _extract_signal(html: str) -> dict:
    """Pull the signal-bearing parts of a page: title, hero text, H1/H2, pricing hints, links."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = (soup.title.string or "").strip() if soup.title else ""
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md["content"].strip()

    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        text = h.get_text(strip=True)
        if text:
            headings.append({"level": h.name, "text": text[:200]})
        if len(headings) >= 60:
            break

    body_text = soup.get_text(" ", strip=True)
    body_text = re.sub(r"\s+", " ", body_text)[:MAX_BODY_CHARS]

    # Pricing hints: any line with $/€/£/₹ + number, or the word 'price' / 'plan'.
    pricing_hints = []
    for line in re.split(r"[.\n]", body_text):
        line = line.strip()
        if not line or len(line) > 240:
            continue
        if re.search(r"[$€£₹]\s?\d", line) or re.search(r"\bfree\b|\bper\s+(user|month|seat)\b", line, re.I):
            pricing_hints.append(line)
        if len(pricing_hints) >= 20:
            break

    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append({"text": a.get_text(strip=True)[:80], "href": href[:300]})
        if len(links) >= MAX_LINK_COUNT:
            break

    return {
        "title": strip_pii(title),
        "meta_description": strip_pii(meta_desc),
        "headings": [{"level": h["level"], "text": strip_pii(h["text"])} for h in headings],
        "body_excerpt": strip_pii(body_text[:4000]),  # excerpt for LLM, not full body
        "pricing_hints": [strip_pii(p) for p in pricing_hints],
        "links": links,
    }


def fetch_one(url: str, timeout: int, rate_limit: float) -> dict:
    """Fetch a single URL. Returns a page record dict (always — including skip reasons)."""
    record = {
        "url": url,
        "status": "pending",
        "http_status": None,
        "content_hash": None,
        "signal": None,
        "error": None,
    }

    try:
        sanitize_url(url)
    except ValueError as e:
        record["status"] = "skipped"
        record["error"] = f"url-rejected: {e}"
        warn(f"URL sanitize failed: {url}", error=str(e))
        return record

    if not is_allowed(url):
        record["status"] = "skipped"
        record["error"] = "robots-disallow"
        return record

    wait_for_rate_limit(url, min_interval_sec=rate_limit)

    try:
        resp = _http_get(url, timeout=timeout)
    except Exception as e:
        record["status"] = "error"
        record["error"] = f"http-error: {e}"
        error(f"HTTP request failed: {url}", error=str(e))
        return record

    record["http_status"] = resp.status_code

    if resp.status_code == 429:
        record["status"] = "rate_limited"
        record["error"] = "http-429"
        warn(f"429 rate limit: {url}")
        return record
    if resp.status_code in (401, 403):
        record["status"] = "blocked"
        record["error"] = f"http-{resp.status_code}"
        warn(f"Access blocked: {url} ({resp.status_code})")
        return record
    if resp.status_code >= 400:
        record["status"] = "error"
        record["error"] = f"http-{resp.status_code}"
        warn(f"HTTP error: {url} ({resp.status_code})")
        return record

    html = resp.text or ""
    signal = _extract_signal(html)
    record["status"] = "ok"
    record["content_hash"] = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()
    record["signal"] = signal
    info(f"fetched OK: {url} ({len(html)} chars, status={resp.status_code})")
    return record


def main():
    parser = argparse.ArgumentParser(description="Fetch a competitor's public pages")
    parser.add_argument("--name", required=True, help="Competitor name (used in output filename)")
    parser.add_argument("--url", action="append", required=True, help="URL to fetch (repeat for multiple)")
    parser.add_argument("--rate-limit", type=float, default=3.0, help="Seconds between requests per domain")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP timeout per request")
    parser.add_argument("--output", default=None, help="Output file (default .tmp/fetch/{name}_site.json)")
    args = parser.parse_args()

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", args.name)
    out_path = args.output or f".tmp/fetch/{safe_name}_site.json"

    info(f"fetch_competitor start: name={args.name} urls={len(args.url)}")

    pages = [fetch_one(u, timeout=args.timeout, rate_limit=args.rate_limit) for u in args.url]

    output_path = validate_write_path(str(Path(__file__).parent.parent / out_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "competitor": args.name,
        "source": "site",
        "pages": pages,
        "counts": {
            "total": len(pages),
            "ok": sum(1 for p in pages if p["status"] == "ok"),
            "skipped": sum(1 for p in pages if p["status"] in ("skipped", "blocked", "rate_limited")),
            "error": sum(1 for p in pages if p["status"] == "error"),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(json.dumps({
        "status": "success",
        "output_path": str(output_path),
        "counts": payload["counts"],
    }))


if __name__ == "__main__":
    main()
