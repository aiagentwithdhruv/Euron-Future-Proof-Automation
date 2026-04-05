#!/usr/bin/env python3
"""
LinkedIn Poster — Post text and images to LinkedIn via API v2.

Setup:
  1. Create app at https://www.linkedin.com/developers/apps
  2. Request "Share on LinkedIn" and "Sign In with LinkedIn using OpenID Connect" products
  3. Get OAuth2 access token (see workflows/linkedin-auth.md)
  4. Set LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN in .env

Usage:
  python tools/linkedin_poster.py --text "Hello LinkedIn!"
  python tools/linkedin_poster.py --text "Check this out" --image /path/to/image.jpg
"""

import argparse
import json
import os
import sys
import requests
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
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")
    if not token:
        print("Error: LINKEDIN_ACCESS_TOKEN not set in .env")
        sys.exit(1)
    if not person_urn:
        print("Error: LINKEDIN_PERSON_URN not set in .env")
        print("Get it: curl -H 'Authorization: Bearer YOUR_TOKEN' https://api.linkedin.com/v2/userinfo")
        sys.exit(1)
    return token, person_urn


def upload_image(token: str, person_urn: str, image_path: str) -> str:
    """Upload image to LinkedIn and return asset URN."""
    # Step 1: Register upload
    register_url = "https://api.linkedin.com/rest/images?action=initializeUpload"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202603",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    register_body = {
        "initializeUploadRequest": {
            "owner": f"urn:li:person:{person_urn}",
        }
    }

    resp = requests.post(register_url, headers=headers, json=register_body, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Image register failed ({resp.status_code}): {resp.text}")

    data = resp.json()["value"]
    upload_url = data["uploadUrl"]
    image_urn = data["image"]

    # Step 2: Upload binary via curl (Python requests times out on LinkedIn uploads)
    import subprocess
    result = subprocess.run([
        "curl", "-s", "-w", "%{http_code}", "--max-time", "120",
        "-X", "PUT",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/octet-stream",
        "--data-binary", f"@{image_path}",
        upload_url,
    ], capture_output=True, text=True, timeout=130)
    http_code = result.stdout.strip()[-3:] if result.stdout else "000"
    if http_code not in ("200", "201"):
        raise Exception(f"Image upload failed (HTTP {http_code}): {result.stderr[:200]}")

    print(f"  Image uploaded: {image_urn}")
    return image_urn


def post_to_linkedin(text: str, media: list = None) -> dict:
    """Post to LinkedIn. Returns result dict."""
    token, person_urn = get_config()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202603",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    # Build post body
    post_body = {
        "author": f"urn:li:person:{person_urn}",
        "lifecycleState": "PUBLISHED",
        "visibility": "PUBLIC",
        "commentary": text,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
    }

    # Add image if provided
    if media and len(media) > 0:
        image_path = media[0]
        if os.path.exists(image_path):
            image_urn = upload_image(token, person_urn, image_path)
            post_body["content"] = {
                "media": {
                    "id": image_urn,
                    "title": "Image",
                }
            }
        else:
            print(f"  Warning: Image not found: {image_path}")

    # Post
    url = "https://api.linkedin.com/rest/posts"
    resp = requests.post(url, headers=headers, json=post_body, timeout=30)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", "unknown")
        print(f"  LinkedIn: Posted successfully (ID: {post_id})")
        return {"status": "success", "post_id": post_id, "platform": "linkedin"}
    else:
        error = resp.text[:500]
        print(f"  LinkedIn: FAILED ({resp.status_code}): {error}")
        return {"status": "error", "reason": error, "platform": "linkedin"}


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Post to LinkedIn")
    parser.add_argument("--text", required=True, help="Post text")
    parser.add_argument("--image", type=str, help="Path to image file")

    args = parser.parse_args()
    media = [args.image] if args.image else None
    result = post_to_linkedin(args.text, media)
    print(json.dumps(result, indent=2))
