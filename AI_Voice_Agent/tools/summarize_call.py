#!/usr/bin/env python3
"""Summarize a call transcript offline (for testing the prompt or batch backfill).

Usage:
    python tools/summarize_call.py --transcript path/to/transcript.txt
    python tools/summarize_call.py --transcript -  # reads stdin
    python tools/summarize_call.py --transcript file.txt --direction outbound --duration 180
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.services.llm_service import LLMError, LLMService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline call-transcript summarizer")
    parser.add_argument("--transcript", required=True, help="Path to transcript file, or '-' for stdin")
    parser.add_argument("--direction", default="inbound", choices=["inbound", "outbound"])
    parser.add_argument("--duration", type=float, default=0, help="Call duration in seconds")
    parser.add_argument("--phone", default=None)
    parser.add_argument("--output", default=None, help="Write result to this JSON file")
    args = parser.parse_args()

    if args.transcript == "-":
        transcript = sys.stdin.read()
    else:
        p = Path(args.transcript)
        if not p.exists():
            print(f"ERROR: transcript not found: {p}", file=sys.stderr)
            return 2
        transcript = p.read_text(encoding="utf-8")

    try:
        llm = LLMService()
        summary = llm.summarize_call(
            transcript=transcript,
            call_direction=args.direction,
            duration_s=args.duration,
            caller_phone=args.phone,
        )
    except LLMError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    text = json.dumps(summary, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote summary → {args.output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
