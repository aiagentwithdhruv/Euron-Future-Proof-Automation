"""6-layer guardrail for outbound drafts — PII, pricing, commitments.

Adapted from `student-starter-kit/skills/guardrail-pipeline/SKILL.md`.
Used as both a CLI tool and an importable module (by draft_reply.py and run_ticket_cycle.py).

Usage (CLI, rarely needed — normally called in-process):
    python tools/guardrail.py --text "Hi Alice, your refund of $50 is guaranteed." --ticket-id TEST-1
    # → prints {"safe_text": "...", "flags": [...], "blocked": true}
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


LOG_PATH = Path(__file__).parent.parent / ".tmp" / "guardrail_log.jsonl"

SAFE_FALLBACK = (
    "Hi there, thanks for reaching out — I've routed this to the right team and a teammate "
    "will reply personally within one business day.\n\nBest,\nSupport team"
)

MAX_DRAFT_CHARS = 2000

# --- Layer 5: PATTERNS ---
PII_STRIP_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"(?<!\d)(?:\+?\d{1,3}[\s\-]?)?(?:\(\d{3}\)\s*|\d{3}[\s\-])\d{3}[\s\-]\d{4}(?!\d)",
    "account_number": r"\baccount\s*(?:#|number|no\.?)?\s*[:\-]?\s*\d{6,}\b",
    "dob": r"\b(?:\d{1,2}[\/\-]){2}\d{2,4}\b",
    "cc_candidate": r"\b(?:\d[ \-]?){13,19}\b",  # Luhn-checked below
}

PRICING_BLOCK_PATTERNS = [
    r"\$\s?\d[\d,\.]*",
    r"₹\s?\d[\d,\.]*",
    r"\brs\.?\s*\d[\d,\.]*",
    r"€\s?\d[\d,\.]*",
    r"£\s?\d[\d,\.]*",
    r"\b\d+\s*(?:usd|eur|gbp|inr|rupees?|dollars?|euros?|pounds?)\b",
    r"\bwill\s+cost\b",
    r"\bpriced\s+at\b",
    r"\bcosts?\s+you\b",
    r"\bfee\s+is\b",
    r"\bcharge(?:d)?\s+\$",
    r"\b\d{1,3}\s*%\s*(?:off|discount)\b",
]

COMMITMENT_BLOCK_PATTERNS = [
    r"\bguarantee(?:d|s)?\b",
    r"\bpromise(?:d|s)?\b",
    r"\bi\s+commit\b",
    r"\bdefinitely\s+will\b",
    r"\bassure\s+you\b",
    r"\bwithin\s+(?:[1-9]|1[0-2])\s+hour[s]?\b",
    r"\bby\s+(?:tomorrow|end\s+of\s+day|eod)\b",
    r"\bwe\s+will\s+refund\b",
    r"\byou\s+will\s+(?:get|receive)\s+a\s+refund\b",
    r"\bapproved\s+for\s+a\s+refund\b",
]

EXECUTION_BLOCK_PATTERNS = [
    r"```",                           # code fences (escape, never send code)
    r"<\s*script",                    # HTML script injection
    r"\bSELECT\s+.*\s+FROM\b",        # raw SQL
    r"\bDROP\s+TABLE\b",
    r"^\s*\{.*\}\s*$",                # raw JSON body
]


def _luhn_check(digits: str) -> bool:
    """Return True if digits pass Luhn — i.e. look like a real credit-card number."""
    digits = re.sub(r"[\s\-]", "", digits)
    if not digits.isdigit() or not (13 <= len(digits) <= 19):
        return False
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _log_flag(ticket_id: str, layer: str, pattern: str, action: str, match: str = ""):
    """Append one flag entry to the monitoring log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "layer": layer,
        "pattern": pattern,
        "action": action,
        "match_preview": match[:80],
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check(draft_text: str, ticket_id: str = "unknown", approved_urls: list | None = None) -> dict:
    """Run all 6 layers on a draft.

    Returns:
        {
          "safe_text": str,          # text safe to send (may be fallback)
          "flags": list[dict],       # every flag raised
          "blocked": bool,           # True if draft had to be replaced
          "original": str,           # the input draft
        }
    """
    flags = []
    text = draft_text or ""
    blocked = False

    # --- Layer 1: Policy ---
    if len(text) > MAX_DRAFT_CHARS:
        flags.append({"layer": "policy", "issue": "length", "action": "block"})
        _log_flag(ticket_id, "policy", "length", "block", f"{len(text)} chars")
        blocked = True

    # External URLs (none allowed by default in v1 — approved_urls is empty)
    approved_urls = approved_urls or []
    for url_match in re.finditer(r"https?://([^\s/)\]]+)", text):
        host = url_match.group(1).lower()
        if not any(host == d or host.endswith("." + d) for d in approved_urls):
            flags.append({"layer": "policy", "issue": f"external_url:{host}", "action": "strip"})
            _log_flag(ticket_id, "policy", "external_url", "strip", host)
            text = text.replace(url_match.group(0), "[link removed]")

    # --- Layer 4: Execution (block tool/code leakage) ---
    for pattern in EXECUTION_BLOCK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            flags.append({"layer": "execution", "issue": pattern, "action": "block"})
            _log_flag(ticket_id, "execution", pattern, "block")
            blocked = True

    # --- Layer 5: Output — PII strip ---
    for name, pattern in PII_STRIP_PATTERNS.items():
        for m in list(re.finditer(pattern, text, re.IGNORECASE)):
            matched = m.group(0)
            if name == "cc_candidate" and not _luhn_check(matched):
                continue
            flags.append({"layer": "output", "issue": f"pii:{name}", "action": "strip", "match": matched[:40]})
            _log_flag(ticket_id, "output", f"pii:{name}", "strip", matched)
            text = text.replace(matched, f"[{name.upper()} REDACTED]")

    # --- Layer 5: Output — Pricing BLOCK ---
    for pattern in PRICING_BLOCK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({"layer": "output", "issue": f"pricing:{pattern}", "action": "block"})
            _log_flag(ticket_id, "output", f"pricing:{pattern}", "block")
            blocked = True

    # --- Layer 5: Output — Commitments BLOCK ---
    for pattern in COMMITMENT_BLOCK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append({"layer": "output", "issue": f"commitment:{pattern}", "action": "block"})
            _log_flag(ticket_id, "output", f"commitment:{pattern}", "block")
            blocked = True

    # --- Layer 6: Monitoring — summary entry for every call ---
    _log_flag(ticket_id, "monitor", "summary", "passed" if not blocked else "blocked",
              f"flags={len(flags)}")

    safe_text = SAFE_FALLBACK if blocked else text

    return {
        "safe_text": safe_text,
        "flags": flags,
        "blocked": blocked,
        "original": draft_text,
    }


def main():
    parser = argparse.ArgumentParser(description="Run guardrail on a draft reply")
    parser.add_argument("--text", help="Draft text to check (use --file for longer inputs)")
    parser.add_argument("--file", help="Read draft text from a file")
    parser.add_argument("--ticket-id", default="cli-test", help="Ticket ID for log attribution")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    result = check(text, args.ticket_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
