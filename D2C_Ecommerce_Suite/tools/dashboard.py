"""CLI dashboard — read runs/*.jsonl and .tmp/airtable/*.jsonl to print a
summary of the suite's activity.

Usage:

    python tools/dashboard.py
    python tools/dashboard.py --since 2026-04-19
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402
from tools._bootstrap import project_root, runs_dir  # noqa: E402


def _parse_iso(s: str) -> datetime | None:
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


def gather(since: datetime | None = None) -> dict:
    per_module: dict[str, Counter] = {}
    events_total = 0
    errors_total = 0
    for f in sorted(runs_dir().glob("*.jsonl")):
        module = f.stem.split("-", 3)[-1] if f.stem.count("-") >= 3 else f.stem
        per_module.setdefault(module, Counter())
        for line in f.read_text().splitlines():
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_iso(row.get("ts", ""))
            if since and ts and ts < since:
                continue
            per_module[module][row.get("event", "unknown")] += 1
            events_total += 1
            if row.get("event") == "error":
                errors_total += 1

    # Airtable local sink rowcounts (dev mode).
    airtable_rows = {}
    sink_dir = project_root() / ".tmp" / "airtable"
    if sink_dir.exists():
        for f in sink_dir.glob("*.jsonl"):
            airtable_rows[f.stem] = sum(1 for _ in f.open())

    return {
        "events_total": events_total,
        "errors_total": errors_total,
        "per_module": {k: dict(v) for k, v in per_module.items()},
        "airtable_rows_local": airtable_rows,
    }


def _format(summary: dict) -> str:
    lines = ["D2C Suite Dashboard", "=" * 40]
    lines.append(f"Total events logged : {summary['events_total']}")
    lines.append(f"Errors              : {summary['errors_total']}")
    lines.append("")
    lines.append("Per-module events:")
    for mod, counts in sorted(summary["per_module"].items()):
        counts_str = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
        lines.append(f"  - {mod:14s} {counts_str}")
    lines.append("")
    if summary["airtable_rows_local"]:
        lines.append("Local Airtable rows (.tmp/airtable/):")
        for table, n in sorted(summary["airtable_rows_local"].items()):
            lines.append(f"  - {table:14s} {n}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="D2C suite run dashboard")
    parser.add_argument("--since", help="ISO date (YYYY-MM-DD) to filter from")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    since = None
    if args.since:
        try:
            since = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Invalid --since: {args.since}")
            return 2

    summary = gather(since)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    else:
        print(_format(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
