"""Track API costs per run and enforce budget limits.

Project rule: $1.00 per run hard cap (CLAUDE.md). Daily default kept at $5.00.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from shared.logger import warn, info

COST_FILE = Path(__file__).parent.parent / ".tmp" / "costs.json"
DAILY_LIMIT = float(os.getenv("COST_DAILY_LIMIT_USD", "5.00"))
RUN_LIMIT = float(os.getenv("COST_CAP_USD", "1.00"))


class BudgetExceededError(Exception):
    pass


def _load_costs() -> dict:
    if COST_FILE.exists():
        try:
            return json.loads(COST_FILE.read_text())
        except Exception:
            return {"runs": []}
    return {"runs": []}


def _save_costs(data: dict):
    COST_FILE.parent.mkdir(exist_ok=True, parents=True)
    COST_FILE.write_text(json.dumps(data, indent=2))


def get_daily_spend() -> float:
    data = _load_costs()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return sum(r["cost"] for r in data["runs"] if r["date"] == today)


def get_run_spend(run_id: str) -> float:
    data = _load_costs()
    return sum(r["cost"] for r in data["runs"] if r.get("run_id") == run_id)


def check_budget(estimated_cost: float = 0.0, run_id: str | None = None):
    """Raise BudgetExceededError if daily OR per-run cap would be breached.

    Per-run cap is enforced when `run_id` is provided (orchestrator supplies it).
    """
    daily = get_daily_spend()
    if daily + estimated_cost > DAILY_LIMIT:
        raise BudgetExceededError(
            f"Daily budget exceeded: ${daily:.4f} spent + ${estimated_cost:.4f} requested > ${DAILY_LIMIT:.2f}"
        )
    if run_id:
        run_spent = get_run_spend(run_id)
        if run_spent + estimated_cost > RUN_LIMIT:
            raise BudgetExceededError(
                f"Run budget exceeded: ${run_spent:.4f} spent + ${estimated_cost:.4f} requested > ${RUN_LIMIT:.2f} (run_id={run_id})"
            )
    if estimated_cost > RUN_LIMIT:
        warn(f"Single call cost ${estimated_cost:.4f} exceeds per-run cap ${RUN_LIMIT:.2f}")


def record_cost(tool: str, cost: float, run_id: str | None = None):
    data = _load_costs()
    entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "cost": cost,
    }
    if run_id:
        entry["run_id"] = run_id
    data["runs"].append(entry)
    _save_costs(data)
    info(f"Cost recorded: {tool}=${cost:.4f} (run_id={run_id})")
