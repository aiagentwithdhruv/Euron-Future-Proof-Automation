"""Blotato API Client — handles all HTTP communication with Blotato v2 API."""

import time
import requests

from src.config import (
    BLOTATO_API_KEY,
    BLOTATO_BASE_URL,
    EXTRACTION_TIMEOUT,
    VISUAL_TIMEOUT,
    PUBLISH_TIMEOUT,
    POLL_INTERVAL_EXTRACT,
    POLL_INTERVAL_VISUAL,
    POLL_INTERVAL_PUBLISH,
)


class BlotatoClient:
    def __init__(self):
        if not BLOTATO_API_KEY or BLOTATO_API_KEY == "your_api_key_here":
            raise ValueError(
                "BLOTATO_API_KEY not set. Add your key to .env file."
            )
        self.base = BLOTATO_BASE_URL
        self.headers = {
            "blotato-api-key": BLOTATO_API_KEY,
            "Content-Type": "application/json",
        }

    # ── Generic request helper ────────────────────────────────────────

    def _get(self, path: str) -> dict | list:
        resp = requests.get(f"{self.base}{path}", headers=self.headers)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict) -> dict:
        resp = requests.post(
            f"{self.base}{path}", headers=self.headers, json=payload
        )
        resp.raise_for_status()
        return resp.json()

    def _poll(self, path: str, done_key: str, done_val: str,
              fail_substring: str, interval: int, timeout: int,
              label: str = "") -> dict:
        start = time.time()
        while time.time() - start < timeout:
            data = self._get(path)
            status = data.get("status", "")
            if status == done_val:
                return data
            if fail_substring in status:
                raise RuntimeError(f"{label} failed: {data.get('error', status)}")
            print(f"  {label}... ({status})")
            time.sleep(interval)
        raise TimeoutError(f"{label} timed out after {timeout}s")

    # ── User & Accounts ───────────────────────────────────────────────

    def get_user(self) -> dict:
        return self._get("/users/me")

    def get_accounts(self) -> list:
        return self._get("/users/me/accounts")

    def get_subaccounts(self, account_id: str) -> list:
        return self._get(f"/users/me/accounts/{account_id}/subaccounts")

    def find_account(self, platform: str) -> dict | None:
        """Find the first connected account for a given platform."""
        accounts = self.get_accounts()
        target = platform.lower()
        for acc in accounts:
            acc_platform = acc.get("platform", "").lower()
            if target in ("x", "twitter") and acc_platform in ("x", "twitter"):
                return acc
            elif target == acc_platform:
                return acc
        return None

    # ── Content Extraction ────────────────────────────────────────────

    def extract_youtube(self, url: str) -> dict:
        """Extract content from a YouTube video. Polls until complete."""
        data = self._post("/source-resolutions-v3", {
            "source": {"sourceType": "youtube", "url": url}
        })
        return self._poll(
            path=f"/source-resolutions-v3/{data['id']}",
            done_key="status", done_val="completed",
            fail_substring="fail",
            interval=POLL_INTERVAL_EXTRACT,
            timeout=EXTRACTION_TIMEOUT,
            label="Extracting YouTube",
        )

    # ── Visual Generation ─────────────────────────────────────────────

    def get_templates(self) -> list:
        return self._get("/videos/templates")

    def generate_visual(self, template_id: str, prompt: str) -> dict:
        """Generate a visual from a template. Polls until complete."""
        data = self._post("/videos/from-templates", {
            "templateId": template_id,
            "inputs": {},
            "prompt": prompt,
            "render": True,
        })
        return self._poll(
            path=f"/videos/creations/{data['id']}",
            done_key="status", done_val="done",
            fail_substring="fail",
            interval=POLL_INTERVAL_VISUAL,
            timeout=VISUAL_TIMEOUT,
            label="Generating visual",
        )

    # ── Publishing ────────────────────────────────────────────────────

    def create_post(self, account_id: str, platform: str, text: str,
                    media_urls: list[str] | None = None,
                    schedule_time: str | None = None,
                    page_id: str | None = None) -> dict:
        """Create a post on a social platform."""
        target = {"targetType": platform}
        if page_id:
            target["pageId"] = page_id

        payload = {
            "post": {
                "accountId": account_id,
                "content": {
                    "text": text,
                    "mediaUrls": media_urls or [],
                    "platform": platform,
                },
                "target": target,
            }
        }
        if schedule_time:
            payload["scheduledTime"] = schedule_time

        return self._post("/posts", payload)

    def wait_for_publish(self, post_id: str) -> dict:
        """Poll until post is published."""
        return self._poll(
            path=f"/posts/{post_id}",
            done_key="status", done_val="published",
            fail_substring="fail",
            interval=POLL_INTERVAL_PUBLISH,
            timeout=PUBLISH_TIMEOUT,
            label="Publishing",
        )
