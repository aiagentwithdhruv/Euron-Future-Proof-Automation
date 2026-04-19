"""Integration tests for the FastAPI webhook receiver.

Covers the golden path: HMAC OK + topic allowed -> 200 accepted,
dispatcher invoked. Plus: HMAC mismatch -> 401, duplicate event
-> 200 with status=duplicate, unsupported topic -> 200 ignored.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENGINE = ROOT.parent / "Agentic Workflow for Students"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))

FIX = ROOT / "tests" / "fixtures"


class WebhookIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SHOPIFY_WEBHOOK_SECRET"] = "itest-secret"
        from tools import idempotency

        idempotency.reset()

        from fastapi.testclient import TestClient

        from api.webhook import app

        cls.client = TestClient(app)

    def _sign(self, body: bytes) -> str:
        from tools.hmac_verify import compute_shopify_hmac

        return compute_shopify_hmac("itest-secret", body)

    def test_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_shopify_hmac_mismatch_returns_401(self):
        body = b'{"id":1}'
        resp = self.client.post(
            "/webhook/shopify",
            content=body,
            headers={
                "X-Shopify-Hmac-Sha256": "not-a-valid-hmac",
                "X-Shopify-Topic": "orders/create",
                "X-Shopify-Webhook-Id": "w-1",
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_shopify_happy_path_accepts_order(self):
        payload = json.loads((FIX / "shopify_order_created.json").read_text())
        body = json.dumps(payload).encode("utf-8")
        resp = self.client.post(
            "/webhook/shopify",
            content=body,
            headers={
                "X-Shopify-Hmac-Sha256": self._sign(body),
                "X-Shopify-Topic": "orders/create",
                "X-Shopify-Webhook-Id": "w-happy-1",
                "X-Shopify-Shop-Domain": "demo.myshopify.com",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["topic"], "order.created")

    def test_shopify_duplicate_event_short_circuits(self):
        payload = {"id": 99, "email": "x@example.com"}
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "X-Shopify-Hmac-Sha256": self._sign(body),
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Webhook-Id": "w-dup-1",
        }
        r1 = self.client.post("/webhook/shopify", content=body, headers=headers)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "accepted")
        r2 = self.client.post("/webhook/shopify", content=body, headers=headers)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "duplicate")

    def test_unsupported_topic_is_ignored(self):
        body = b'{"ignored":true}'
        resp = self.client.post(
            "/webhook/shopify",
            content=body,
            headers={
                "X-Shopify-Hmac-Sha256": self._sign(body),
                "X-Shopify-Topic": "shop/redact",
                "X-Shopify-Webhook-Id": "w-ign-1",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ignored")


if __name__ == "__main__":
    unittest.main()
