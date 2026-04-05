#!/usr/bin/env python3
"""
X/Twitter Poster — Post text and images to X via API v2.

Setup:
  1. Create app at https://developer.x.com/en/portal/dashboard
  2. Set app permissions to "Read and Write"
  3. Generate OAuth 1.0a tokens (Access Token + Secret)
  4. Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET in .env

Usage:
  python tools/x_poster.py --text "Hello X!"
  python tools/x_poster.py --text "Check this out" --image /path/to/image.jpg
"""

import argparse
import json
import os
import sys
import requests
import hmac
import hashlib
import base64
import time
import urllib.parse
import uuid
from pathlib import Path


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def get_config():
    keys = {
        "api_key": os.getenv("X_API_KEY"),
        "api_secret": os.getenv("X_API_SECRET"),
        "access_token": os.getenv("X_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("X_ACCESS_TOKEN_SECRET"),
    }
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(f"Error: Missing in .env: {', '.join(missing)}")
        sys.exit(1)
    return keys


def oauth1_header(method: str, url: str, params: dict, keys: dict) -> str:
    """Generate OAuth 1.0a Authorization header."""
    oauth_params = {
        "oauth_consumer_key": keys["api_key"],
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA256",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": keys["access_token"],
        "oauth_version": "1.0",
    }

    all_params = {**oauth_params, **params}
    sorted_params = sorted(all_params.items())
    param_string = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(v), safe='')}"
                           for k, v in sorted_params)

    base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
    signing_key = f"{urllib.parse.quote(keys['api_secret'], safe='')}&{urllib.parse.quote(keys['access_token_secret'], safe='')}"

    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha256).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature
    header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return header


def upload_media(image_path: str, keys: dict) -> str:
    """Upload media to X and return media_id."""
    url = "https://upload.twitter.com/1.1/media/upload.json"

    # Use OAuth 1.0a for upload
    with open(image_path, "rb") as f:
        files = {"media_data": base64.b64encode(f.read()).decode()}

    auth_header = oauth1_header("POST", url, {}, keys)
    headers = {"Authorization": auth_header}

    resp = requests.post(url, headers=headers, data=files, timeout=60)
    if resp.status_code not in (200, 201, 202):
        raise Exception(f"Media upload failed ({resp.status_code}): {resp.text}")

    media_id = resp.json()["media_id_string"]
    print(f"  Media uploaded: {media_id}")
    return media_id


def post_to_x(text: str, media: list = None) -> dict:
    """Post a tweet to X. Returns result dict."""
    keys = get_config()

    url = "https://api.x.com/2/tweets"
    payload = {"text": text}

    # Upload media if provided
    if media and len(media) > 0:
        media_ids = []
        for image_path in media[:4]:  # X allows max 4 images
            if os.path.exists(image_path):
                try:
                    media_id = upload_media(image_path, keys)
                    media_ids.append(media_id)
                except Exception as e:
                    print(f"  Warning: Media upload failed: {e}")
            else:
                print(f"  Warning: File not found: {image_path}")

        if media_ids:
            payload["media"] = {"media_ids": media_ids}

    auth_header = oauth1_header("POST", url, {}, keys)
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)

    if resp.status_code in (200, 201):
        data = resp.json().get("data", {})
        tweet_id = data.get("id", "unknown")
        print(f"  X: Posted successfully (ID: {tweet_id})")
        return {"status": "success", "post_id": tweet_id, "platform": "x"}
    else:
        error = resp.text[:500]
        print(f"  X: FAILED ({resp.status_code}): {error}")
        return {"status": "error", "reason": error, "platform": "x"}


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Post to X (Twitter)")
    parser.add_argument("--text", required=True, help="Tweet text (max 280 chars)")
    parser.add_argument("--image", type=str, help="Path to image file")

    args = parser.parse_args()

    if len(args.text) > 280:
        print(f"Warning: Text is {len(args.text)} chars (max 280)")

    media = [args.image] if args.image else None
    result = post_to_x(args.text, media)
    print(json.dumps(result, indent=2))
