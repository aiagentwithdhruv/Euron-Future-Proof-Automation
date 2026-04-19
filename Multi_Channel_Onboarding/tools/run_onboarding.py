#!/usr/bin/env python3
"""Tool: run_onboarding

Orchestrates the Multi-Channel Onboarding pipeline by chaining atomic tools.
See workflows/onboarding-flow.md for the SOP.

Input: --signup <path to signup JSON>, --dry-run (skip external network calls)
Output: Final orchestration receipt JSON on stdout + runs/<date>-<user_id>.md log
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)
TOOLS_DIR = PROJECT_ROOT / "tools"


def run_tool(script: str, args: list, capture: bool = True) -> dict:
    """Run a child tool and parse its JSON stdout. Returns parsed dict + meta."""
    cmd = [sys.executable, str(TOOLS_DIR / script)] + args
    start = time.time()
    proc = subprocess.run(cmd, capture_output=capture, text=True, timeout=120)
    duration_ms = int((time.time() - start) * 1000)

    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
        except json.JSONDecodeError:
            parsed = {"raw_stdout": proc.stdout.strip()[:400]}

    return {
        "script": script,
        "exit_code": proc.returncode,
        "duration_ms": duration_ms,
        "stdout": parsed,
        "stderr": proc.stderr.strip()[:400] if proc.stderr else "",
    }


def write_run_log(user_id: str, steps: list, summary: dict) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = PROJECT_ROOT / "runs" / f"{today}-{user_id}.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Onboarding Run — {user_id}",
        "",
        f"- **Date:** {today}",
        f"- **Started:** {summary.get('started_at')}",
        f"- **Finished:** {summary.get('finished_at')}",
        f"- **Dry run:** {summary.get('dry_run')}",
        f"- **Status:** {summary.get('status')}",
        f"- **Channels sent:** {', '.join(summary.get('channels_sent', [])) or '-'}",
        f"- **Channels failed:** {', '.join(summary.get('channels_failed', [])) or '-'}",
        f"- **Scheduled:** {', '.join(summary.get('scheduled', [])) or '-'}",
        "",
        "## Steps",
        "",
    ]
    for i, step in enumerate(steps, 1):
        status = "OK" if step["exit_code"] == 0 else "FAIL"
        lines.append(f"### {i}. {step['script']} — {status} ({step['duration_ms']} ms)")
        if step.get("stdout"):
            lines.append("```json")
            lines.append(json.dumps(step["stdout"], indent=2, ensure_ascii=False))
            lines.append("```")
        if step.get("stderr"):
            lines.append(f"_stderr:_ `{step['stderr']}`")
        lines.append("")

    log_path.write_text("\n".join(lines))
    return log_path


def main():
    parser = argparse.ArgumentParser(description="Orchestrate the multi-channel onboarding flow")
    parser.add_argument("--signup", required=True, help="Path to signup JSON")
    parser.add_argument("--dry-run", action="store_true", help="Skip external channel sends")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    started_at = datetime.now(timezone.utc).isoformat()
    steps = []
    channels_sent = []
    channels_failed = []
    scheduled = []

    # --- Step 1-2: Receive + validate + enrich ---
    r = run_tool("receive_signup.py", ["--signup", args.signup])
    steps.append(r)
    if r["exit_code"] != 0:
        summary = {
            "status": "error",
            "code": "signup_invalid",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": args.dry_run,
        }
        log = write_run_log("unknown", steps, summary)
        summary["log"] = str(log.relative_to(PROJECT_ROOT))
        print(json.dumps(summary))
        sys.exit(r["exit_code"])

    user_id = r["stdout"]["user_id"]
    user_path = PROJECT_ROOT / r["stdout"]["user_path"]
    user = json.loads(user_path.read_text())

    # --- Step 3: Personalize copy ---
    r = run_tool("personalize_copy.py", ["--user", str(user_path.relative_to(PROJECT_ROOT))])
    steps.append(r)
    if r["exit_code"] != 0:
        logger.error("copy generation failed — aborting pipeline")
        summary = {
            "status": "error",
            "code": "copy_failed",
            "user_id": user_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": args.dry_run,
        }
        log = write_run_log(user_id, steps, summary)
        summary["log"] = str(log.relative_to(PROJECT_ROOT))
        print(json.dumps(summary))
        sys.exit(1)

    copy = json.loads((PROJECT_ROOT / ".tmp" / user_id / "copy.json").read_text())

    # --- Step 4: Email ---
    email_args = [
        "--to", user["email"],
        "--subject", copy["email"]["subject"],
        "--body", copy["email"]["body"],
    ]
    if args.dry_run:
        email_args.append("--dry-run")
    r = run_tool("send_email.py", email_args)
    steps.append(r)
    (channels_sent if r["exit_code"] == 0 else channels_failed).append("email")

    # --- Step 5: WhatsApp (skip cleanly if no phone) ---
    if user.get("phone"):
        wa_args = ["--to", user["phone"], "--message", copy["whatsapp"]]
        if args.dry_run:
            wa_args.append("--dry-run")
        r = run_tool("send_whatsapp.py", wa_args)
        steps.append(r)
        (channels_sent if r["exit_code"] == 0 else channels_failed).append("whatsapp")
    else:
        logger.info("no phone on signup — skipping whatsapp")
        steps.append({"script": "send_whatsapp.py", "exit_code": 0, "duration_ms": 0,
                      "stdout": {"status": "skipped", "reason": "no_phone"}, "stderr": ""})

    # --- Step 6: Slack internal alert ---
    slack_args = ["--message", copy["slack"]]
    if args.dry_run:
        slack_args.append("--dry-run")
    r = run_tool("send_slack.py", slack_args)
    steps.append(r)
    (channels_sent if r["exit_code"] == 0 else channels_failed).append("slack")

    # --- Step 7: Day 2 nudge ---
    day2_msg = f"Hey {user['name'].split()[0]}, quick nudge — did you try the first step yet?"
    r = run_tool("schedule_followup.py", [
        "--user-id", user_id,
        "--delay-days", "2",
        "--message", day2_msg,
        "--channel", "email",
        "--variant", "nudge",
        "--to", user["email"],
    ])
    steps.append(r)
    if r["exit_code"] == 0:
        scheduled.append("day2-nudge")

    # --- Step 8: Day 5 deep-value email ---
    day5_msg = (
        f"Hi {user['name'].split()[0]}, here's the highest-leverage thing I've found for "
        f"{user.get('product_interest','this')} users in their first week."
    )
    r = run_tool("schedule_followup.py", [
        "--user-id", user_id,
        "--delay-days", "5",
        "--message", day5_msg,
        "--channel", "email",
        "--variant", "deep-value",
        "--to", user["email"],
    ])
    steps.append(r)
    if r["exit_code"] == 0:
        scheduled.append("day5-deep-value")

    # --- Step 9: Log + final output ---
    finished_at = datetime.now(timezone.utc).isoformat()
    overall_status = "success" if not channels_failed else "partial"

    summary = {
        "status": overall_status,
        "user_id": user_id,
        "channels_sent": channels_sent,
        "channels_failed": channels_failed,
        "scheduled": scheduled,
        "dry_run": args.dry_run,
        "started_at": started_at,
        "finished_at": finished_at,
    }

    log_path = write_run_log(user_id, steps, summary)
    summary["log"] = str(log_path.relative_to(PROJECT_ROOT))

    logger.info("onboarding_complete", extra={"outputs": summary})
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
