"""Cart recovery — send_recovery_email.

Given a cart row (`detect_abandoned.promote()` output), draft + send the
step-appropriate recovery email.

Step 1 (1 hr):   No discount. Friendly 'did something break?' nudge.
Step 2 (24 hr):  Small discount (5-10%) — code reused from env
                 DISCOUNT_CODE_RECOVERY. Encourage completion.
Step 3 (3 days): Final nudge. Same code, last reminder copy. After step 3
                 we stop — pestering customers has a cost.

CRITICAL INVARIANT: recovery is DISCOUNT ONLY. This module will never place
an order, never charge a card, never "hold" a product. The only action is
an email/WhatsApp with a link back to the cart + (maybe) a discount code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_p = Path(__file__).resolve()
while _p.parent != _p and not (_p / "tools" / "_bootstrap.py").exists():
    _p = _p.parent
if str(_p) not in sys.path:
    sys.path.insert(0, str(_p))

import tools._bootstrap  # noqa: F401,E402

from shared.logger import get_logger  # noqa: E402

from tools import llm
from tools.airtable_client import AirtableStore, table_name
from tools.config import module_config
from tools.senders import send_email, send_whatsapp

logger = get_logger(__name__)


def _template(row: dict, step: int, discount_code: str, discount_pct: int) -> dict:
    name = (row.get("customer_name") or "there").split()[0] if row.get("customer_name") else "there"
    items = row.get("line_items") or []
    item_lines = "\n".join(f"  - {i.get('quantity')}x {i.get('title')}" for i in items) or "  - your selection"
    cart_url = row.get("abandoned_checkout_url") or "(cart link unavailable)"

    if step == 1:
        subject = f"{name.capitalize()}, you left something behind"
        body = (
            f"Hi {name},\n\n"
            f"We noticed you were looking at:\n{item_lines}\n\n"
            f"It's still there if you'd like to finish up:\n{cart_url}\n\n"
            f"If something didn't work or you had a question, just reply to this email."
        )
        whatsapp = f"Hey {name}! Your cart is still waiting: {cart_url}. Let us know if anything felt off."
    elif step == 2:
        subject = f"Your cart + {discount_pct}% off with {discount_code}"
        body = (
            f"Hi {name},\n\n"
            f"We saved your cart:\n{item_lines}\n\n"
            f"Use code *{discount_code}* for {discount_pct}% off when you check out:\n{cart_url}\n\n"
            f"Code expires in 48 hours."
        )
        whatsapp = f"{name}, code *{discount_code}* takes {discount_pct}% off your cart. Finish here: {cart_url}"
    else:  # step 3
        subject = "Last chance on your saved cart"
        body = (
            f"Hi {name},\n\n"
            f"This is the last nudge — your cart will drop off soon.\n\n"
            f"{item_lines}\n\n"
            f"Still {discount_pct}% off with *{discount_code}*:\n{cart_url}\n\n"
            f"If it's not the right time, no worries — thanks for considering us."
        )
        whatsapp = f"{name}, last nudge — cart + {discount_pct}% off with {discount_code}: {cart_url}"

    return {"subject": subject, "body": body, "whatsapp": whatsapp}


def compose(row: dict, step: int, discount_code: str, discount_pct: int) -> dict:
    """LLM-driven copy when available; template fallback otherwise."""
    try:
        data = llm.generate_json(
            "cart_recovery_v1",
            {
                "customer_name": row.get("customer_name") or "",
                "step": step,
                "items": ", ".join((i.get("title") or "") for i in (row.get("line_items") or [])),
                "discount_code": discount_code if step > 1 else "",
                "discount_pct": discount_pct if step > 1 else 0,
                "cart_url": row.get("abandoned_checkout_url") or "",
            },
            temperature=0.5,
            max_tokens=500,
        )
        subject = data.get("subject") or _template(row, step, discount_code, discount_pct)["subject"]
        body = data.get("body") or _template(row, step, discount_code, discount_pct)["body"]
        whatsapp = data.get("whatsapp") or _template(row, step, discount_code, discount_pct)["whatsapp"]
        return {"subject": subject, "body": body, "whatsapp": whatsapp}
    except (llm.LLMUnavailable, json.JSONDecodeError):
        return _template(row, step, discount_code, discount_pct)


def send_for_row(row: dict, *, discount_pct: int = 10, dry_run: bool = False) -> dict:
    step = row.get("recovery_step", 1)
    if step < 1 or step > 3:
        return {"status": "skipped", "reason": "invalid_step"}

    cfg = module_config()
    code = cfg.discount_code_recovery
    copy = compose(row, step, code, discount_pct)

    out = {"status": "success", "cart_id": row.get("cart_id"), "step": step, "channels": []}
    if row.get("email"):
        out["channels"].append(send_email(to=row["email"], subject=copy["subject"], body=copy["body"], dry_run=dry_run))
    if row.get("phone"):
        try:
            out["channels"].append(send_whatsapp(to=row["phone"], message=copy["whatsapp"], dry_run=dry_run))
        except ValueError as e:
            out["channels"].append({"status": "skipped", "channel": "whatsapp", "reason": str(e)})

    AirtableStore().create(
        table_name("carts"),
        {
            "CartID": row.get("cart_id"),
            "Stage": f"recovery_step_{step}",
            "DiscountCode": code if step > 1 else "",
            "Status": "abandoned",
        },
    )
    return out


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Send a recovery email for one cart row")
    parser.add_argument("--row-file", required=True, help="JSON file with cart row")
    parser.add_argument("--discount", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    row = json.loads(Path(args.row_file).read_text())
    print(json.dumps(send_for_row(row, discount_pct=args.discount, dry_run=args.dry_run), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
