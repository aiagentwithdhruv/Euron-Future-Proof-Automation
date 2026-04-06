"""AI News Telegram Bot — Daily AI news digest to your Telegram.

Usage:
    python main.py                          # Full pipeline: fetch → rank → format → send
    python main.py --sources newsapi,rss    # Specific sources
    python main.py --top 3                  # Top 3 instead of 5
    python main.py --no-llm                 # Skip AI ranking, use keyword scoring
    python main.py --dry-run                # Fetch + rank + format, but don't send
    python main.py --plain                  # Send as plain text (no markdown)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from shared.env_loader import load_env
from shared.logger import info, error
from shared.sandbox import validate_write_path


def run_tool(tool_path: str, args: list) -> int:
    """Run a tool as a subprocess. Returns exit code."""
    import subprocess
    full_path = Path(__file__).parent / tool_path
    info(f"Running: {tool_path} {' '.join(args)}")

    result = subprocess.run(
        [sys.executable, str(full_path)] + args,
        cwd=str(Path(__file__).parent),
        capture_output=False,
        timeout=120,
    )
    return result.returncode


def write_run_log(results: dict):
    """Write a run log to runs/ directory."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = validate_write_path(str(Path(__file__).parent / f"runs/{today}-daily-ai-news.md"))
    log_path.parent.mkdir(exist_ok=True)

    lines = [
        f"# Run Log — {today}",
        "",
        f"**Workflow:** daily-ai-news",
        f"**Time:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Steps",
        "",
    ]
    for step, result in results.items():
        status = "OK" if result.get("exit_code", 1) == 0 else "FAILED"
        lines.append(f"- **{step}**: {status}")

    lines.append("")
    lines.append("---")
    log_path.write_text("\n".join(lines))
    info(f"Run log written to {log_path}")


def main():
    parser = argparse.ArgumentParser(description="AI News Telegram Bot")
    parser.add_argument("--sources", default="newsapi,rss", help="Comma-separated sources")
    parser.add_argument("--top", type=int, default=5, help="Number of top news items")
    parser.add_argument("--no-llm", action="store_true", help="Skip AI ranking")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Telegram")
    parser.add_argument("--plain", action="store_true", help="Send as plain text")
    args = parser.parse_args()

    load_env()
    results = {}
    info("Starting AI News Digest pipeline")

    # Step 1: Fetch
    exit_code = run_tool("tools/fetch_news.py", [
        "--sources", args.sources,
        "--limit", "20",
    ])
    results["fetch_news"] = {"exit_code": exit_code}
    if exit_code != 0:
        error("Fetch failed — aborting pipeline")
        sys.exit(1)

    # Step 2: Rank
    rank_args = ["--input", ".tmp/raw_news.json", "--top", str(args.top)]
    if args.no_llm:
        rank_args.append("--no-llm")
    exit_code = run_tool("tools/rank_news.py", rank_args)
    results["rank_news"] = {"exit_code": exit_code}
    if exit_code != 0:
        error("Ranking failed — aborting pipeline")
        sys.exit(1)

    # Step 3: Format
    fmt = "plain" if args.plain else "markdown"
    exit_code = run_tool("tools/format_message.py", [
        "--input", ".tmp/ranked_news.json",
        "--format", fmt,
    ])
    results["format_message"] = {"exit_code": exit_code}
    if exit_code != 0:
        error("Formatting failed — aborting pipeline")
        sys.exit(1)

    # Step 4: Send
    if args.dry_run:
        info("Dry run — skipping Telegram send")
        msg_path = Path(__file__).parent / ".tmp" / "telegram_message.txt"
        if msg_path.exists():
            print("\n--- MESSAGE PREVIEW ---")
            print(msg_path.read_text())
            print("--- END PREVIEW ---\n")
        results["send_telegram"] = {"exit_code": 0, "skipped": True}
    else:
        parse_mode = "plain" if args.plain else "MarkdownV2"
        exit_code = run_tool("tools/send_telegram.py", [
            "--input", ".tmp/telegram_message.txt",
            "--parse-mode", parse_mode,
        ])
        results["send_telegram"] = {"exit_code": exit_code}

    # Log the run
    write_run_log(results)
    info("Pipeline complete")


if __name__ == "__main__":
    main()
