#!/usr/bin/env python3
"""Tool: schedule_followup

Append a follow-up task to the JSON file-based queue at .tmp/followup_queue.json.
The queue is consumed by a separate worker (n8n / cron / GitHub Actions) at deploy time.

Input: --user-id, --delay-days, --message, optional --channel (default email), --variant
Output: JSON receipt with the generated task id
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

QUEUE_PATH = PROJECT_ROOT / ".tmp" / "followup_queue.json"


def load_queue() -> list:
    if not QUEUE_PATH.exists():
        return []
    try:
        return json.loads(QUEUE_PATH.read_text())
    except json.JSONDecodeError:
        logger.warning("followup queue corrupted — starting fresh copy alongside backup")
        backup = QUEUE_PATH.with_suffix(".json.broken")
        QUEUE_PATH.rename(backup)
        return []


def save_queue(queue: list) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Schedule a follow-up task (file-based queue)")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--delay-days", type=int, required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--channel", default="email", choices=["email", "whatsapp", "slack"])
    parser.add_argument("--variant", default="nudge", help="Tag: nudge | deep-value | winback | ...")
    parser.add_argument("--to", default="", help="Recipient (email or phone) for the worker")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    if args.delay_days < 0 or args.delay_days > 90:
        print(json.dumps({"status": "error", "code": "invalid_delay"}), file=sys.stderr)
        sys.exit(2)

    now = datetime.now(timezone.utc)
    due_at = now + timedelta(days=args.delay_days)

    task = {
        "task_id": f"fu_{uuid.uuid4().hex[:10]}",
        "user_id": args.user_id,
        "channel": args.channel,
        "variant": args.variant,
        "to": args.to,
        "message": args.message,
        "scheduled_at": now.isoformat(),
        "due_at": due_at.isoformat(),
        "status": "pending",
    }

    queue = load_queue()
    queue.append(task)

    try:
        save_queue(queue)
    except Exception as e:
        logger.error(f"queue write failed: {e}")
        print(json.dumps({"status": "error", "code": "queue_write_failed", "detail": str(e)}), file=sys.stderr)
        sys.exit(1)

    result = {
        "status": "success",
        "task_id": task["task_id"],
        "due_at": task["due_at"],
        "channel": task["channel"],
        "variant": task["variant"],
    }
    logger.info("followup_scheduled", extra={"outputs": result})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
