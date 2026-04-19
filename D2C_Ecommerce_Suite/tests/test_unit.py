"""Unit tests for the suite — run with `python -m unittest -v` from the project dir."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

# Make the project importable.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# Make `shared/*` from the engine importable.
ENGINE = ROOT.parent / "Agentic Workflow for Students"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

FIX = ROOT / "tests" / "fixtures"


def _read_raw(path: Path) -> bytes:
    return path.read_bytes()


class HmacTests(unittest.TestCase):
    def test_shopify_hmac_matches(self):
        from tools.hmac_verify import compute_shopify_hmac, verify_shopify_hmac

        body = b'{"id":1}'
        secret = "supersecret"
        sig = compute_shopify_hmac(secret, body)
        self.assertTrue(verify_shopify_hmac(secret, body, sig))

    def test_shopify_hmac_mismatch(self):
        from tools.hmac_verify import verify_shopify_hmac

        self.assertFalse(verify_shopify_hmac("s", b'{"id":1}', "not-a-real-hmac"))

    def test_woo_hmac_alias(self):
        from tools.hmac_verify import compute_shopify_hmac, verify_woocommerce_hmac

        body = b'{"id":1}'
        sig = compute_shopify_hmac("s", body)
        self.assertTrue(verify_woocommerce_hmac("s", body, sig))


class IdempotencyTests(unittest.TestCase):
    def setUp(self):
        from tools import idempotency

        idempotency.reset()

    def test_first_seen_returns_true_duplicate_false(self):
        from tools import idempotency

        self.assertTrue(idempotency.mark("shopify", "evt-123", "orders/create"))
        self.assertFalse(idempotency.mark("shopify", "evt-123", "orders/create"))

    def test_body_hash_stable(self):
        from tools import idempotency

        h1 = idempotency.body_hash(b'{"id":1}')
        h2 = idempotency.body_hash(b'{"id":1}')
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


class EventNormalizationTests(unittest.TestCase):
    def test_shopify_order_created(self):
        from tools import events

        raw = json.loads((FIX / "shopify_order_created.json").read_text())
        evt = events.normalize(source="shopify", topic="orders/create", raw=raw, event_id="evt-1")
        self.assertEqual(evt["topic"], "order.created")
        self.assertEqual(evt["order"]["email"], "alex.doe@example.com")
        self.assertEqual(evt["order"]["customer_name"], "Alex Doe")
        self.assertEqual(len(evt["order"]["line_items"]), 2)

    def test_shopify_order_fulfilled_has_tracking(self):
        from tools import events

        raw = json.loads((FIX / "shopify_order_fulfilled.json").read_text())
        evt = events.normalize(source="shopify", topic="orders/fulfilled", raw=raw, event_id="evt-2")
        self.assertEqual(evt["order"]["tracking_number"], "TRK-ABC-9900")
        self.assertIn("example-carrier.com", evt["order"]["tracking_url"])

    def test_shopify_cart_abandoned(self):
        from tools import events

        raw = json.loads((FIX / "shopify_cart_abandoned.json").read_text())
        evt = events.normalize(source="shopify", topic="checkouts/update", raw=raw, event_id="evt-3")
        self.assertEqual(evt["topic"], "cart.abandoned_candidate")
        self.assertEqual(evt["cart"]["email"], "bea.smith@example.com")
        self.assertIn("abandoned_checkout_url", evt["cart"])


class SendersDryRunTests(unittest.TestCase):
    def test_email_dry_run(self):
        from tools.senders.email import send_email

        r = send_email(to="x@example.com", subject="hi", body="yo", dry_run=True)
        self.assertTrue(r["dry_run"])
        self.assertEqual(r["channel"], "email")

    def test_whatsapp_dry_run(self):
        from tools.senders.whatsapp import send_whatsapp

        r = send_whatsapp(to="+919876543210", message="hello", dry_run=True)
        self.assertTrue(r["dry_run"])
        self.assertEqual(r["channel"], "whatsapp")

    def test_slack_dry_run(self):
        from tools.senders.slack import send_slack

        r = send_slack(message="ping", dry_run=True)
        self.assertTrue(r["dry_run"])
        self.assertEqual(r["channel"], "slack")


class OrdersModuleTests(unittest.TestCase):
    def test_send_confirmation_skips_without_contact(self):
        from modules.orders import send_confirmation
        from tools import events

        raw = json.loads((FIX / "shopify_order_created.json").read_text())
        raw["email"] = None
        raw["phone"] = None
        raw["customer"]["email"] = None
        evt = events.normalize(source="shopify", topic="orders/create", raw=raw, event_id="t1")
        r = send_confirmation.run(evt, dry_run=True)
        self.assertEqual(r["status"], "skipped")

    def test_send_confirmation_fires_both_channels(self):
        from modules.orders import send_confirmation
        from tools import events

        raw = json.loads((FIX / "shopify_order_created.json").read_text())
        evt = events.normalize(source="shopify", topic="orders/create", raw=raw, event_id="t2")
        r = send_confirmation.run(evt, dry_run=True)
        self.assertEqual(r["status"], "success")
        # email + whatsapp both attempted
        kinds = [c.get("channel") for c in r["channels"]]
        self.assertIn("email", kinds)
        self.assertIn("whatsapp", kinds)

    def test_tracking_update_requires_tracking_info(self):
        from modules.orders import tracking_update
        from tools import events

        raw = json.loads((FIX / "shopify_order_fulfilled.json").read_text())
        evt = events.normalize(source="shopify", topic="orders/fulfilled", raw=raw, event_id="t3")
        r = tracking_update.run(evt, dry_run=True)
        self.assertEqual(r["status"], "success")


class SupportClassifyTests(unittest.TestCase):
    def test_rule_classifier_picks_shipping(self):
        from modules.support.classify_email import rule_classify

        r = rule_classify("Where is my order?", "It's been 5 days, tracking hasn't updated. Delayed?")
        self.assertEqual(r["intent"], "shipping")
        self.assertEqual(r["team"], "logistics")

    def test_rule_classifier_spam(self):
        from modules.support.classify_email import rule_classify

        r = rule_classify("Win a free loan!", "Click here for bitcoin. Click here.")
        self.assertEqual(r["intent"], "spam")
        self.assertEqual(r["priority"], "P4")

    def test_rule_classifier_p1_on_legal(self):
        from modules.support.classify_email import rule_classify

        r = rule_classify("Chargeback filed", "I am initiating a chargeback immediately.")
        self.assertEqual(r["priority"], "P1")


class SupportGuardrailTests(unittest.TestCase):
    def test_strip_prices_redacts_usd_and_inr(self):
        from modules.support.draft_reply import strip_prices

        text = "We will refund $25.00 or ₹ 1,250 — your choice."
        out = strip_prices(text)
        self.assertNotIn("$25", out)
        self.assertNotIn("1,250", out)
        self.assertIn("[price redacted]", out)


class CartRecoveryTests(unittest.TestCase):
    def setUp(self):
        # Point the cart store at a fresh file.
        from modules.cart_recovery import detect_abandoned

        self.store_path = detect_abandoned.CART_STORE
        if self.store_path.exists():
            self.store_path.unlink()

    def test_record_candidate_saves_row(self):
        from modules.cart_recovery import detect_abandoned
        from tools import events

        raw = json.loads((FIX / "shopify_cart_abandoned.json").read_text())
        evt = events.normalize(source="shopify", topic="checkouts/update", raw=raw, event_id="e1")
        r = detect_abandoned.record_candidate(evt)
        self.assertEqual(r["status"], "recorded")
        self.assertTrue(self.store_path.exists())
        store = json.loads(self.store_path.read_text())
        self.assertIn("ck_abandoned_123", store["carts"])

    def test_recovery_email_step2_contains_discount(self):
        from modules.cart_recovery.send_recovery_email import _template

        row = {"customer_name": "Bea Smith", "line_items": [{"quantity": 1, "title": "Hoodie"}], "abandoned_checkout_url": "http://x"}
        copy = _template(row, step=2, discount_code="COMEBACK10", discount_pct=10)
        self.assertIn("COMEBACK10", copy["body"])
        self.assertIn("10%", copy["body"])


class ReviewsTests(unittest.TestCase):
    def test_sentiment_rule_positive(self):
        from modules.reviews.classify_sentiment import _rule

        r = _rule({"rating": 5, "text": "Love it, fantastic!"})
        self.assertEqual(r["sentiment"], "positive")

    def test_sentiment_rule_negative(self):
        from modules.reviews.classify_sentiment import _rule

        r = _rule({"rating": 2, "text": "Arrived damaged, disappointed."})
        self.assertEqual(r["sentiment"], "negative")

    def test_sentiment_rule_ambiguous_3star(self):
        from modules.reviews.classify_sentiment import _rule

        r = _rule({"rating": 3, "text": "It was okay I guess."})
        self.assertEqual(r["sentiment"], "neutral")
        self.assertTrue(r["ambiguous"])


class InventoryTests(unittest.TestCase):
    def test_suggest_returns_positive_qty_on_thin_stock(self):
        from modules.inventory.suggest_reorder import suggest

        r = suggest(sku="A", product_title="Hat", last_30d_sales=60, current_stock=5, target_cover_days=30)
        self.assertGreater(r["suggested_qty"], 0)
        self.assertFalse(r["auto_order_enabled"])

    def test_check_stock_returns_empty_when_unconfigured(self):
        # No Shopify/Woo creds => empty list.
        os.environ.pop("SHOPIFY_ACCESS_TOKEN", None)
        os.environ.pop("WOO_CONSUMER_KEY", None)
        from modules.inventory.check_stock_levels import poll

        self.assertEqual(poll(), [])


if __name__ == "__main__":
    unittest.main()
