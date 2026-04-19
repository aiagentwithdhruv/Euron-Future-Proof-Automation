"""Rate-limit enforcement for outbound email.

Two limits, both mandatory:
  1) Daily limit per sender (default 50)
  2) Per-prospect cooldown (default 3 days)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from shared import env

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SENDS_LOG = PROJECT_ROOT / "state" / "sends.log"
SENDS_LOG.parent.mkdir(exist_ok=True)


def _load_sends() -> list[dict]:
    if not SENDS_LOG.exists():
        return []
    out = []
    for line in SENDS_LOG.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


class RateLimitError(Exception):
    pass


def check_and_record(prospect_id: str, sender: str) -> None:
    """Raise RateLimitError if limits hit; otherwise append the send."""
    daily_limit = int(env.get("EMAIL_DAILY_LIMIT", "50"))
    cooldown_days = int(env.get("EMAIL_PER_PROSPECT_COOLDOWN_DAYS", "3"))

    sends = _load_sends()
    now = _now()

    # Daily limit per sender
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = sum(
        1 for s in sends
        if s.get("sender") == sender and _parse(s["at"]) >= day_start
    )
    if today_count >= daily_limit:
        raise RateLimitError(
            f"Daily limit hit for {sender}: {today_count}/{daily_limit}. "
            "Resume tomorrow or lower volume."
        )

    # Per-prospect cooldown
    cutoff = now - timedelta(days=cooldown_days)
    recent = [s for s in sends if s.get("prospect_id") == prospect_id and _parse(s["at"]) >= cutoff]
    if recent:
        last = max(recent, key=lambda s: s["at"])
        raise RateLimitError(
            f"Cooldown active for {prospect_id}: last touch at {last['at']}. "
            f"Wait {cooldown_days} days between touches."
        )

    with SENDS_LOG.open("a") as f:
        f.write(json.dumps({
            "at": now.isoformat(),
            "prospect_id": prospect_id,
            "sender": sender,
        }) + "\n")


def sends_today(sender: str) -> int:
    sends = _load_sends()
    day_start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
    return sum(1 for s in sends if s.get("sender") == sender and _parse(s["at"]) >= day_start)
