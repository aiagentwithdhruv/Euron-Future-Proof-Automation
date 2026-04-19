"""Autonomous Research Agent — orchestrator.

Runs the weekly cycle end-to-end per workflows/research-cycle.md:
  1) Load competitors from YAML
  2) Per-competitor: fetch site + news + social
  3) Diff vs previous snapshot
  4) Classify + rank changes (analyze_changes)
  5) Write report (write_report)
  6) Deliver report (deliver_report) — skipped on --dry-run
  7) Save new snapshots
  8) Log run

Usage:
    python tools/run_research.py --competitors config/competitors.yaml --dry-run
    python tools/run_research.py --competitors config/competitors.yaml
"""

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from shared.env_loader import load_env
from shared.logger import info, warn, error
from shared.cost_tracker import check_budget, get_run_spend, BudgetExceededError, RUN_LIMIT
from shared.sandbox import validate_write_path


PROJECT_ROOT = Path(__file__).parent.parent


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "_", name)


def run_tool(cmd: list[str], timeout: int = 240) -> dict:
    """Run a tool as a subprocess. Captures stdout for structured output."""
    info(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        [sys.executable, *cmd],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    # Stream tool stderr up (tool logs go there).
    if stderr:
        for line in stderr.splitlines():
            print(line)
    parsed = None
    if stdout:
        # Tool's final line is always a JSON object; grab the last line that parses.
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    parsed = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
    return {
        "exit_code": result.returncode,
        "stdout": stdout,
        "parsed": parsed,
    }


def build_competitor_urls(comp: dict) -> list[str]:
    urls = []
    for field in ("homepage", "pricing", "blog", "about"):
        v = comp.get(field)
        if v:
            urls.append(v)
    return urls


def build_handles_arg(comp: dict) -> str:
    social = comp.get("social") or {}
    parts = []
    for plat, handle in social.items():
        if handle:
            parts.append(f"{plat}:{handle}")
    return ",".join(parts)


def write_run_log(run_id: str, summary: dict):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = validate_write_path(str(PROJECT_ROOT / f"runs/{date_str}-research-cycle.md"))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Research Cycle — {date_str}",
        "",
        f"**Run ID:** `{run_id}`",
        f"**Start:** {summary.get('started_at')}",
        f"**End:** {summary.get('ended_at')}",
        f"**Dry run:** {summary.get('dry_run')}",
        f"**Total cost:** ${summary.get('total_cost', 0):.4f} (cap ${RUN_LIMIT:.2f})",
        "",
        "## Per-competitor",
        "",
    ]
    for c in summary.get("competitors", []):
        lines.append(f"### {c['name']}")
        for step, res in c.get("steps", {}).items():
            ok = res.get("exit_code", 1) == 0
            extra = ""
            if res.get("parsed"):
                p = res["parsed"]
                if "counts" in p:
                    extra = f" — {p['counts']}"
                elif "status" in p:
                    extra = f" — {p['status']}"
            lines.append(f"- **{step}:** {'OK' if ok else 'FAILED'}{extra}")
        lines.append("")

    lines.append("## Analyze / Report / Deliver")
    for step, res in summary.get("final_steps", {}).items():
        ok = res.get("exit_code", 1) == 0
        status_bits = ""
        if res.get("parsed"):
            status_bits = f" — {json.dumps(res['parsed'])[:300]}"
        lines.append(f"- **{step}:** {'OK' if ok else 'FAILED'}{status_bits}")

    lines.append("")
    lines.append("## Notes")
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    log_path.write_text("\n".join(lines))
    info(f"run log written: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Research Agent — orchestrator")
    parser.add_argument("--competitors", default="config/competitors.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Skip delivery, write preview only")
    parser.add_argument("--no-llm", action="store_true", help="Force rule-based classification")
    parser.add_argument("--rate-limit", type=float, default=3.0)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--channels", default="slack,email,telegram")
    args = parser.parse_args()

    load_env()

    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    started_at = datetime.now(timezone.utc).isoformat()
    summary: dict = {
        "run_id": run_id,
        "started_at": started_at,
        "dry_run": args.dry_run,
        "competitors": [],
        "final_steps": {},
        "notes": [],
    }

    # Pre-flight: budget check.
    try:
        check_budget(estimated_cost=0.0, run_id=run_id)
    except BudgetExceededError as e:
        error(f"pre-flight budget check failed: {e}")
        sys.exit(2)

    # Load competitors config.
    cfg_path = PROJECT_ROOT / args.competitors
    if not cfg_path.exists():
        error(f"competitors config not found: {cfg_path}")
        sys.exit(1)
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    business_context = cfg.get("business_context", "AI automation platforms")
    competitors = cfg.get("competitors") or []
    if not competitors:
        error("no competitors listed in config")
        sys.exit(1)

    info(f"cycle start: run_id={run_id} competitors={len(competitors)} dry_run={args.dry_run}")

    diff_paths: list[str] = []

    for comp in competitors:
        name = comp["name"]
        sname = safe_name(name)
        comp_summary = {"name": name, "steps": {}}

        # Step 2a — fetch competitor pages.
        urls = build_competitor_urls(comp)
        if urls:
            cmd = [str(PROJECT_ROOT / "tools/fetch_competitor.py"),
                   "--name", name, "--rate-limit", str(args.rate_limit)]
            for u in urls:
                cmd.extend(["--url", u])
            res = run_tool(cmd, timeout=300)
            comp_summary["steps"]["fetch_competitor"] = res
        else:
            comp_summary["steps"]["fetch_competitor"] = {"exit_code": 0, "skipped": True,
                                                          "reason": "no urls in config"}

        # Step 2b — fetch news.
        keywords = ",".join(comp.get("news_keywords") or [name])
        cmd = [str(PROJECT_ROOT / "tools/fetch_news.py"),
               "--name", name, "--keywords", keywords, "--days", "7", "--limit", "15"]
        res = run_tool(cmd, timeout=120)
        comp_summary["steps"]["fetch_news"] = res

        # Step 2c — fetch social.
        handles = build_handles_arg(comp)
        if handles:
            cmd = [str(PROJECT_ROOT / "tools/fetch_social.py"),
                   "--name", name, "--handles", handles, "--days", "7", "--limit", "8"]
            res = run_tool(cmd, timeout=120)
            comp_summary["steps"]["fetch_social"] = res
        else:
            comp_summary["steps"]["fetch_social"] = {"exit_code": 0, "skipped": True,
                                                     "reason": "no handles in config"}

        # Step 3 — diff vs previous snapshot (save new snapshot after diff).
        current_files = [
            f".tmp/fetch/{sname}_site.json",
            f".tmp/fetch/{sname}_news.json",
            f".tmp/fetch/{sname}_social.json",
        ]
        prev_snap_rel = f"data/snapshots/{sname}.json"
        prev_snap_abs = PROJECT_ROOT / prev_snap_rel
        cmd = [str(PROJECT_ROOT / "tools/snapshot_diff.py"),
               "--name", name,
               "--current-files", ",".join(current_files),
               "--save"]
        if prev_snap_abs.exists():
            cmd.extend(["--previous-snapshot", prev_snap_rel])
        res = run_tool(cmd, timeout=60)
        comp_summary["steps"]["snapshot_diff"] = res
        diff_paths.append(f".tmp/diff/{sname}.json")

        # Abort early if per-run budget already breached.
        spent = get_run_spend(run_id)
        if spent > RUN_LIMIT:
            summary["notes"].append(f"budget breach after {name} — ${spent:.4f}")
            error(f"budget breach — aborting cycle. spent=${spent:.4f}")
            summary["competitors"].append(comp_summary)
            break

        summary["competitors"].append(comp_summary)

    # Step 4 — analyze changes.
    cmd = [str(PROJECT_ROOT / "tools/analyze_changes.py"),
           "--diffs", ",".join(diff_paths),
           "--business-context", business_context,
           "--top", str(args.top),
           "--run-id", run_id]
    if args.no_llm:
        cmd.append("--no-llm")
    summary["final_steps"]["analyze_changes"] = run_tool(cmd, timeout=240)

    # Step 5 — write report.
    cmd = [str(PROJECT_ROOT / "tools/write_report.py"),
           "--insights", ".tmp/insights.json",
           "--output", ".tmp/report.md",
           "--business-context", business_context,
           "--run-id", run_id]
    if args.no_llm:
        cmd.append("--no-llm")
    summary["final_steps"]["write_report"] = run_tool(cmd, timeout=120)

    # Step 6 — deliver report (unless dry-run).
    cmd = [str(PROJECT_ROOT / "tools/deliver_report.py"),
           "--report", ".tmp/report.md",
           "--channels", args.channels]
    if args.dry_run:
        cmd.append("--dry-run")
    summary["final_steps"]["deliver_report"] = run_tool(cmd, timeout=120)

    # Finalize.
    summary["ended_at"] = datetime.now(timezone.utc).isoformat()
    summary["total_cost"] = get_run_spend(run_id)
    write_run_log(run_id, summary)

    # If dry-run, surface the report preview.
    report_path = PROJECT_ROOT / ".tmp/report.md"
    if args.dry_run and report_path.exists():
        print("\n--- REPORT PREVIEW ---\n")
        print(report_path.read_text()[:4000])
        print("\n--- END PREVIEW ---\n")

    print(json.dumps({
        "status": "success",
        "run_id": run_id,
        "competitors": [c["name"] for c in summary["competitors"]],
        "total_cost": summary["total_cost"],
        "dry_run": args.dry_run,
    }))


if __name__ == "__main__":
    main()
