"""Orchestrator — run one pass of the ticket flow.

Fetch → classify → create tickets → draft replies (with guardrail) → notify team.
Human approval + send are deliberately OUT OF SCOPE for this loop — operator runs
approval_queue.py when ready.

Usage:
    python tools/run_ticket_cycle.py --dry-run --fixtures .tmp/fake_emails.json
    python tools/run_ticket_cycle.py --since 15                     # real IMAP run (when configured)
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env
from shared.logger import info, warn, error


PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
RUNS_DIR = PROJECT_ROOT / "runs"
STORE_PATH = PROJECT_ROOT / "output" / "tickets.json"


def run_step(name: str, cmd: list) -> tuple[int, str, str]:
    """Run a sub-tool. Return (returncode, stdout, stderr)."""
    info(f"STEP {name}: {' '.join(cmd[1:])}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if r.returncode != 0:
        error(f"{name} failed (exit {r.returncode}): {r.stderr[:300]}")
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def write_run_log(run_log_path: Path, sections: dict):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Ticket Cycle Run — {sections['timestamp']}",
        "",
        f"- **Mode:** {sections['mode']}",
        f"- **Fixtures:** {sections.get('fixtures', 'n/a')}",
        f"- **Since (min):** {sections.get('since', 'n/a')}",
        f"- **Duration:** {sections['duration_s']:.2f}s",
        f"- **Emails fetched:** {sections['fetch_count']}",
        f"- **Tickets created:** {sections['created']}",
        f"- **Drafts generated:** {sections['drafted']}",
        f"- **Guardrail blocks:** {sections['guardrail_blocks']}",
        f"- **Slack notifications:** {sections['notified']} ({sections['slack_mode']})",
        "",
        "## Sub-tool output",
        "",
    ]
    for stage, out in sections["stage_outputs"].items():
        lines.append(f"### {stage}")
        lines.append("```")
        lines.append(out or "(empty)")
        lines.append("```")
        lines.append("")
    if sections.get("errors"):
        lines += ["## Errors", ""]
        for e in sections["errors"]:
            lines.append(f"- {e}")
        lines.append("")
    run_log_path.write_text("\n".join(lines))


def count_in_stdout(stdout: str, key: str) -> int:
    try:
        # stdout from our tools ends with a single-line JSON status object
        for line in reversed(stdout.splitlines()):
            if line.startswith("{"):
                return int(json.loads(line).get(key, 0))
    except Exception:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run one ticket cycle pass")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip real IMAP/Slack/Resend — use fixtures + local sinks")
    parser.add_argument("--fixtures", help="Path to fake emails JSON (forces dry-run fetch)")
    parser.add_argument("--since", type=int, default=15, help="IMAP lookback minutes")
    parser.add_argument("--limit", type=int, default=None, help="(Reserved — not yet honoured)")
    parser.add_argument("--no-llm", action="store_true", help="Force keyword+template mode")
    args = parser.parse_args()

    load_env()

    started = datetime.now(timezone.utc)
    mode = "dry-run" if (args.dry_run or args.fixtures) else "live"
    info(f"=== Ticket cycle START — mode={mode} ===")

    stage_outputs = {}
    errors = []

    # STEP 1 — fetch
    fetch_cmd = [sys.executable, str(PROJECT_ROOT / "tools" / "fetch_emails.py"),
                 "--output", ".tmp/new_emails.json"]
    if args.fixtures:
        fetch_cmd += ["--fixtures", args.fixtures]
    else:
        fetch_cmd += ["--since", str(args.since)]
    rc, out, err = run_step("fetch_emails", fetch_cmd)
    stage_outputs["fetch_emails"] = out or err
    if rc != 0:
        errors.append(f"fetch_emails exit {rc}")
        write_run_log(_run_log_path(started), _log_sections(started, mode, args,
                      0, 0, 0, 0, 0, "n/a", stage_outputs, errors))
        sys.exit(rc)
    fetch_count = count_in_stdout(out, "count")

    if fetch_count == 0:
        info("No emails to process — exiting cleanly")
        write_run_log(_run_log_path(started), _log_sections(started, mode, args,
                      0, 0, 0, 0, 0, "n/a", stage_outputs, errors))
        print(json.dumps({"status": "success", "fetch_count": 0, "ticket_cycle": "noop"}))
        return

    # STEP 2 — classify
    classify_cmd = [sys.executable, str(PROJECT_ROOT / "tools" / "classify_ticket.py"),
                    "--input", ".tmp/new_emails.json",
                    "--output", ".tmp/classified.json"]
    if args.no_llm:
        classify_cmd.append("--no-llm")
    rc, out, err = run_step("classify_ticket", classify_cmd)
    stage_outputs["classify_ticket"] = out or err
    if rc != 0:
        errors.append(f"classify_ticket exit {rc}")

    # STEP 3 — create tickets
    create_cmd = [sys.executable, str(PROJECT_ROOT / "tools" / "create_ticket.py"),
                  "--input", ".tmp/classified.json"]
    rc, out, err = run_step("create_ticket", create_cmd)
    stage_outputs["create_ticket"] = out or err
    created = count_in_stdout(out, "created")
    if rc != 0:
        errors.append(f"create_ticket exit {rc}")

    # STEP 4 — draft replies (guardrail runs inside draft_reply.py)
    draft_cmd = [sys.executable, str(PROJECT_ROOT / "tools" / "draft_reply.py"),
                 "--all", "--kb", "./knowledge/"]
    if args.no_llm:
        draft_cmd.append("--no-llm")
    rc, out, err = run_step("draft_reply", draft_cmd)
    stage_outputs["draft_reply"] = out or err
    drafted = count_in_stdout(out, "drafted")
    if rc != 0:
        errors.append(f"draft_reply exit {rc}")

    # STEP 5 — notify Slack (dry-run if in dry-run mode OR no webhook)
    notify_cmd = [sys.executable, str(PROJECT_ROOT / "tools" / "notify_team.py"), "--all"]
    if args.dry_run:
        notify_cmd.append("--dry-run")
    rc, out, err = run_step("notify_team", notify_cmd)
    stage_outputs["notify_team"] = out or err
    notified = count_in_stdout(out, "notified")
    slack_mode = "dry-run" if args.dry_run else "auto"
    if rc != 0:
        errors.append(f"notify_team exit {rc}")

    # Count guardrail blocks from the ticket store
    guardrail_blocks = 0
    try:
        if STORE_PATH.exists():
            all_tickets = json.loads(STORE_PATH.read_text())
            guardrail_blocks = sum(1 for t in all_tickets if t.get("guardrail_blocked"))
    except Exception:
        pass

    ended = datetime.now(timezone.utc)
    duration_s = (ended - started).total_seconds()

    sections = _log_sections(started, mode, args, fetch_count, created, drafted,
                             guardrail_blocks, notified, slack_mode, stage_outputs, errors)
    sections["duration_s"] = duration_s
    run_log_path = _run_log_path(started)
    write_run_log(run_log_path, sections)

    info(f"=== Ticket cycle END — {duration_s:.2f}s, created={created}, drafted={drafted}, "
         f"blocks={guardrail_blocks}, notified={notified} ===")
    print(json.dumps({
        "status": "success" if not errors else "partial",
        "mode": mode,
        "fetch_count": fetch_count,
        "created": created,
        "drafted": drafted,
        "guardrail_blocks": guardrail_blocks,
        "notified": notified,
        "run_log": str(run_log_path),
        "errors": errors,
    }))


def _run_log_path(started):
    return RUNS_DIR / f"{started.strftime('%Y-%m-%d-%H%M%S')}-ticket-cycle.md"


def _log_sections(started, mode, args, fetch_count, created, drafted,
                  guardrail_blocks, notified, slack_mode, stage_outputs, errors):
    return {
        "timestamp": started.isoformat(),
        "mode": mode,
        "fixtures": args.fixtures,
        "since": args.since if not args.fixtures else None,
        "duration_s": 0.0,
        "fetch_count": fetch_count,
        "created": created,
        "drafted": drafted,
        "guardrail_blocks": guardrail_blocks,
        "notified": notified,
        "slack_mode": slack_mode,
        "stage_outputs": stage_outputs,
        "errors": errors,
    }


if __name__ == "__main__":
    main()
