"""Build current snapshot from fetched JSON files and diff vs previous snapshot.

A "snapshot" is a compact JSON capturing what's important about a competitor
this week: page hashes, title, pricing hints, top headings, news URLs, social
post URLs. The raw scraped body is NOT stored — snapshot diff is the source
of truth for the analyzer (per CLAUDE.md).

Usage:
    python tools/snapshot_diff.py --name "n8n" \\
        --current-files .tmp/fetch/n8n_site.json,.tmp/fetch/n8n_news.json,.tmp/fetch/n8n_social.json \\
        --previous-snapshot data/snapshots/n8n.json

Output:
    .tmp/diff/{name}.json  — diff JSON (changes only)
    (Optionally) data/snapshots/{name}.json — new baseline if --save is set.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logger import info, warn
from shared.sandbox import validate_write_path
from shared.sanitize import strip_pii


def build_site_snapshot(site_json: dict) -> dict:
    pages = {}
    for p in site_json.get("pages", []):
        url = p.get("url") or ""
        if not url:
            continue
        signal = p.get("signal") or {}
        pages[url] = {
            "http_status": p.get("http_status"),
            "content_hash": p.get("content_hash"),
            "title": signal.get("title", ""),
            "meta_description": signal.get("meta_description", ""),
            "headings": [h["text"] for h in (signal.get("headings") or [])][:20],
            "pricing_hints": (signal.get("pricing_hints") or [])[:20],
            "status": p.get("status"),
        }
    return pages


def build_news_snapshot(news_json: dict) -> dict:
    by_url = {}
    for a in news_json.get("articles", []):
        url = (a.get("url") or "").strip()
        if not url:
            continue
        by_url[url] = {
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "published": a.get("published", ""),
            "description": (a.get("description") or "")[:300],
        }
    return by_url


def build_social_snapshot(social_json: dict) -> dict:
    by_url = {}
    for plat, posts in (social_json.get("posts") or {}).items():
        for post in posts:
            url = (post.get("url") or "").strip()
            if not url:
                continue
            by_url[url] = {
                "platform": plat,
                "title": post.get("title", ""),
                "published": post.get("published", ""),
                "content": (post.get("content") or "")[:300],
            }
    return by_url


def diff_dicts(previous: dict, current: dict, kind: str) -> list:
    """Return a list of change records for the given map (keyed by URL)."""
    changes = []
    prev_keys = set(previous.keys())
    curr_keys = set(current.keys())

    for url in curr_keys - prev_keys:
        rec = current[url]
        changes.append({
            "change_id": f"{kind}:{url}:added",
            "kind": kind,
            "type": "added",
            "url": url,
            "before": None,
            "after": rec,
        })

    for url in prev_keys - curr_keys:
        changes.append({
            "change_id": f"{kind}:{url}:removed",
            "kind": kind,
            "type": "removed",
            "url": url,
            "before": previous[url],
            "after": None,
        })

    for url in curr_keys & prev_keys:
        before, after = previous[url], current[url]
        field_diff = {}
        for field in ("content_hash", "title", "meta_description", "pricing_hints", "headings",
                      "description", "content", "published"):
            b = before.get(field) if isinstance(before, dict) else None
            a = after.get(field) if isinstance(after, dict) else None
            if b != a:
                field_diff[field] = {"before": b, "after": a}
        if field_diff:
            changes.append({
                "change_id": f"{kind}:{url}:modified",
                "kind": kind,
                "type": "modified",
                "url": url,
                "fields": field_diff,
            })
    return changes


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        warn(f"failed to parse {path}: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Diff current fetches vs previous snapshot")
    parser.add_argument("--name", required=True)
    parser.add_argument("--current-files", required=True,
                        help="Comma-separated list of .tmp/fetch/*.json (site,news,social)")
    parser.add_argument("--previous-snapshot", default=None,
                        help="data/snapshots/{name}.json (optional; first run has none)")
    parser.add_argument("--output", default=None)
    parser.add_argument("--save", action="store_true",
                        help="Write the new snapshot to data/snapshots/{name}.json")
    args = parser.parse_args()

    safe_name = re.sub(r"[^A-Za-z0-9_\-]", "_", args.name)
    project_root = Path(__file__).parent.parent

    # Load current inputs.
    files = [Path(project_root / f.strip()) for f in args.current_files.split(",") if f.strip()]
    current_snapshot = {"site": {}, "news": {}, "social": {}}
    for f in files:
        data = load_json(f)
        src = data.get("source")
        if src == "site":
            current_snapshot["site"] = build_site_snapshot(data)
        elif src == "news":
            current_snapshot["news"] = build_news_snapshot(data)
        elif src == "social":
            current_snapshot["social"] = build_social_snapshot(data)
        else:
            warn(f"unknown source in {f}: {src}")

    # Load previous snapshot.
    prev_snapshot_path = None
    if args.previous_snapshot:
        prev_snapshot_path = project_root / args.previous_snapshot
    previous_snapshot = load_json(prev_snapshot_path) if prev_snapshot_path else {}
    prev = {
        "site": previous_snapshot.get("site") or {},
        "news": previous_snapshot.get("news") or {},
        "social": previous_snapshot.get("social") or {},
    }
    first_run = not previous_snapshot

    changes = []
    for kind in ("site", "news", "social"):
        changes.extend(diff_dicts(prev[kind], current_snapshot[kind], kind))

    # PII-scrub anything that might have slipped in.
    def scrub(rec):
        if isinstance(rec, dict):
            return {k: scrub(v) for k, v in rec.items()}
        if isinstance(rec, list):
            return [scrub(x) for x in rec]
        if isinstance(rec, str):
            return strip_pii(rec)
        return rec

    changes = [scrub(c) for c in changes]

    summary = {
        "competitor": args.name,
        "first_run": first_run,
        "counts": {
            "added": sum(1 for c in changes if c["type"] == "added"),
            "removed": sum(1 for c in changes if c["type"] == "removed"),
            "modified": sum(1 for c in changes if c["type"] == "modified"),
            "total": len(changes),
        },
        "changes": changes,
    }

    diff_out = args.output or f".tmp/diff/{safe_name}.json"
    diff_path = validate_write_path(str(project_root / diff_out))
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    diff_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    info(f"diff written: {diff_path} (changes={summary['counts']['total']}, first_run={first_run})")

    if args.save:
        snap_path = validate_write_path(str(project_root / f"data/snapshots/{safe_name}.json"))
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        new_snapshot = {
            "competitor": args.name,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "site": current_snapshot["site"],
            "news": current_snapshot["news"],
            "social": current_snapshot["social"],
        }
        snap_path.write_text(json.dumps(new_snapshot, indent=2, ensure_ascii=False))
        info(f"snapshot saved: {snap_path}")

    print(json.dumps({
        "status": "success",
        "output_path": str(diff_path),
        "counts": summary["counts"],
        "first_run": first_run,
    }))


if __name__ == "__main__":
    main()
