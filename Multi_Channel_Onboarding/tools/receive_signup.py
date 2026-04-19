#!/usr/bin/env python3
"""Tool: receive_signup

Validate + sanitize + enrich a signup JSON payload.
Input: path to signup JSON
Output: JSON on stdout + persisted cleaned user dict under .tmp/<user_id>/user.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENGINE_ROOT = PROJECT_ROOT.parent / "Agentic Workflow for Students"
sys.path.insert(0, str(ENGINE_ROOT))

from shared.env_loader import load_env  # noqa: E402
from shared.logger import get_logger  # noqa: E402
from shared.sanitize import sanitize_input, validate_email  # noqa: E402

logger = get_logger(__name__)

REQUIRED_FIELDS = ["user_id", "name", "email"]
DEFAULTS = {
    "language": "en",
    "segment": "student",
    "timezone": "UTC",
    "product_interest": "automation-bootcamp",
    "signup_source": "unknown",
}


def normalize_phone(raw: str) -> str:
    """Normalize phone to E.164-ish (`+` followed by digits)."""
    if not raw:
        return ""
    digits = re.sub(r"[^\d+]", "", raw)
    if digits and not digits.startswith("+"):
        digits = "+" + digits
    return digits


def validate_and_enrich(payload: dict) -> dict:
    missing = [f for f in REQUIRED_FIELDS if not payload.get(f)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    clean = {}
    clean["user_id"] = sanitize_input(str(payload["user_id"]), max_length=64)
    clean["name"] = sanitize_input(str(payload["name"]), max_length=120)
    clean["email"] = validate_email(str(payload["email"]))

    phone = normalize_phone(str(payload.get("phone", "")))
    clean["phone"] = phone

    for key, default in DEFAULTS.items():
        val = payload.get(key)
        clean[key] = sanitize_input(str(val), max_length=80) if val else default

    clean["signed_up_at"] = payload.get("signed_up_at") or datetime.now(timezone.utc).isoformat()
    clean["received_at"] = datetime.now(timezone.utc).isoformat()

    return clean


def main():
    parser = argparse.ArgumentParser(description="Receive + validate a signup JSON payload")
    parser.add_argument("--signup", required=True, help="Path to signup JSON file")
    args = parser.parse_args()

    load_env(env_path=str(PROJECT_ROOT / ".env"))

    signup_path = Path(args.signup)
    if not signup_path.is_absolute():
        signup_path = PROJECT_ROOT / signup_path

    if not signup_path.exists():
        err = {"status": "error", "code": "file_not_found", "path": str(signup_path)}
        print(json.dumps(err), file=sys.stderr)
        sys.exit(2)

    try:
        payload = json.loads(signup_path.read_text())
    except json.JSONDecodeError as e:
        err = {"status": "error", "code": "invalid_payload", "detail": str(e)}
        print(json.dumps(err), file=sys.stderr)
        sys.exit(2)

    try:
        user = validate_and_enrich(payload)
    except ValueError as e:
        err = {"status": "error", "code": "validation_failed", "detail": str(e)}
        logger.error(f"Validation failed: {e}")
        print(json.dumps(err), file=sys.stderr)
        sys.exit(2)

    out_dir = PROJECT_ROOT / ".tmp" / user["user_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "user.json").write_text(json.dumps(user, indent=2, ensure_ascii=False))

    result = {
        "status": "success",
        "user_id": user["user_id"],
        "user_path": str((out_dir / "user.json").relative_to(PROJECT_ROOT)),
    }
    logger.info("signup_received", extra={"outputs": {"user_id": user["user_id"]}})
    print(json.dumps(result))


if __name__ == "__main__":
    main()
