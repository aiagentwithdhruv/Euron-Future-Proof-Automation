#!/usr/bin/env python3
"""Stage 02 — Pull company context from the prospect's website.

Extracts:
  - <title> + meta description
  - About / hero section text (first 2-3 paragraphs)
  - Detected tech signals (from meta, script src, and known patterns)
  - Buying signals (keywords: "hiring", "we're growing", funding round, etc.)

Final output written to prospect:
  - website_summary (str)
  - tech_stack (list[str])
  - signals (list[str])

After Stage 02, prospect transitions to 'enriched' (ready for qualify).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from shared import env, state  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import safe_domain, validate_url  # noqa: E402

logger = get_logger(__name__)

TECH_SIGNALS = {
    "hubspot": r"(hs-scripts\.com|hubspot)",
    "salesforce": r"(force\.com|salesforce)",
    "intercom": r"intercom",
    "shopify": r"(cdn\.shopify\.com|myshopify)",
    "stripe": r"stripe",
    "segment": r"segment\.com",
    "mixpanel": r"mixpanel",
    "wordpress": r"(wp-content|wordpress)",
    "webflow": r"webflow",
    "zapier": r"zapier",
    "notion": r"notion\.so",
    "slack": r"slack\.com",
}

BUYING_PATTERNS = [
    (r"we['’]re hiring|join us|careers?", "hiring"),
    (r"series [abc]|raised\s*\$", "recent funding"),
    (r"scale|grow(th|ing)|expand", "growth language"),
    (r"backlog|overwhelmed|manual", "pain: overwhelmed"),
    (r"ai|automation|agents?", "AI curious"),
]


def _fetch(url: str, timeout: int = 12) -> str:
    import requests

    headers = {"User-Agent": "Mozilla/5.0 ClientAcq/1.0"}
    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp.text[:250_000]


def _extract(html: str) -> dict:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("bs4 not installed; falling back to regex")
        return _extract_regex(html)
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    meta_desc = ""
    tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if tag and tag.get("content"):
        meta_desc = tag["content"].strip()

    paragraphs = []
    for p in soup.find_all(["p", "h1", "h2"])[:15]:
        text = p.get_text(separator=" ", strip=True)
        if 30 <= len(text) <= 400:
            paragraphs.append(text)
    hero = " ".join(paragraphs[:3])

    full = f"{title} | {meta_desc} | {hero}"[:1500]

    low = html.lower()
    tech = [name for name, pat in TECH_SIGNALS.items() if re.search(pat, low)]
    signals = []
    text_for_signals = (title + " " + meta_desc + " " + hero).lower()
    for pat, label in BUYING_PATTERNS:
        if re.search(pat, text_for_signals):
            signals.append(label)

    return {
        "website_summary": full,
        "tech_stack": tech,
        "signals": signals,
    }


def _extract_regex(html: str) -> dict:
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    title = m.group(1).strip() if m else ""
    m = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html, re.I)
    desc = m.group(1).strip() if m else ""
    low = html.lower()
    tech = [name for name, pat in TECH_SIGNALS.items() if re.search(pat, low)]
    return {
        "website_summary": f"{title} | {desc}"[:1500],
        "tech_stack": tech,
        "signals": [],
    }


def run(prospect: dict, dry_run: bool = False) -> dict:
    pid = prospect["prospect_id"]
    if prospect.get("website_summary") and prospect.get("tech_stack") is not None:
        new_status = _status_after_enrich(prospect)
        return state.transition(pid, "enriched", new_status, reason="cached-context") if prospect.get("stage") != "enriched" else prospect

    website = prospect.get("website", "")
    domain = safe_domain(website)
    if not domain:
        merged = state.upsert_prospect({**prospect, "website_summary": "", "tech_stack": [], "signals": []})
        return state.transition(pid, "enriched", _status_after_enrich(merged), reason="no-website")

    if dry_run:
        fake = {
            "website_summary": f"[DRY-RUN] {prospect.get('company','Company')} — {prospect.get('contact_role','role')} in {prospect.get('city','')}. Website mentions hiring, growth, and customer support.",
            "tech_stack": ["hubspot", "notion"],
            "signals": ["hiring", "growth language"],
        }
        merged = state.upsert_prospect({**prospect, **fake})
        return state.transition(pid, "enriched", _status_after_enrich(merged), reason="dry-run-context")

    try:
        url = validate_url(website if website.startswith("http") else f"https://{domain}")
        html = _fetch(url)
        extracted = _extract(html)
    except Exception as e:
        logger.warning(f"fetch failed for {domain}: {e}", extra={"prospect_id": pid})
        extracted = {"website_summary": "", "tech_stack": [], "signals": []}

    merged = state.upsert_prospect({**prospect, **extracted})
    return state.transition(pid, "enriched", _status_after_enrich(merged), reason="website-fetched")


def _status_after_enrich(prospect: dict) -> str:
    """After enrich, decide if prospect is reachable or not."""
    has_email = bool(prospect.get("email"))
    has_li = bool(prospect.get("linkedin_url"))
    if not has_email and not has_li:
        return "unreachable"
    return "pending_qualify"


def main():
    env.load_env()
    ap = argparse.ArgumentParser(description="Stage 02: company context")
    ap.add_argument("--prospect-id")
    ap.add_argument("--all-pending", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    dry = env.is_dry_run(args.dry_run)

    if args.all_pending:
        todo = state.prospects_where(status="pending_enrich")
    else:
        if not args.prospect_id:
            ap.error("Provide --prospect-id or --all-pending")
        p = state.get_prospect(args.prospect_id)
        if not p:
            ap.error(f"No prospect {args.prospect_id}")
        todo = [p]

    for p in todo:
        run(p, dry_run=dry)
    print(json.dumps({"status": "success", "dry_run": dry, "processed": len(todo)}, indent=2))


if __name__ == "__main__":
    main()
