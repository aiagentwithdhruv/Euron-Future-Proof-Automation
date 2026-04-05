#!/usr/bin/env python3
"""
Instagram Poster — Post images and reels via Meta Graph API.

Setup:
  1. Create Facebook Business Page (if you don't have one)
  2. Convert Instagram to Professional Account (Business or Creator)
  3. Link Instagram to Facebook Page
  4. Create Meta App at https://developers.facebook.com/apps/
  5. Add Instagram Graph API product
  6. Get long-lived access token (see workflows/instagram-auth.md)
  7. Get Instagram Business Account ID
  8. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID in .env

Usage:
  python tools/instagram_poster.py --caption "Hello Instagram!" --image /path/to/photo.jpg
  python tools/instagram_poster.py --caption "Watch this" --video /path/to/reel.mp4 --reel
"""

import argparse
import json
import os
import sys
import time
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
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    if not token:
        print("Error: INSTAGRAM_ACCESS_TOKEN not set")
        sys.exit(1)
    if not account_id:
        print("Error: INSTAGRAM_BUSINESS_ACCOUNT_ID not set")
        print("Get it: curl 'https://graph.facebook.com/v21.0/me/accounts?access_token=TOKEN'")
        sys.exit(1)
    return token, account_id


def post_image(token: str, account_id: str, image_url: str, caption: str) -> dict:
    """Post a single image to Instagram.
    Note: Instagram API requires a PUBLIC URL for images, not local files.
    For local files, upload to a temp hosting service first.
    """
    base = "https://graph.facebook.com/v21.0"

    # Step 1: Create media container
    create_url = f"{base}/{account_id}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token,
    }

    resp = requests.post(create_url, params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Container creation failed ({resp.status_code}): {resp.text}")

    container_id = resp.json()["id"]
    print(f"  Container created: {container_id}")

    # Step 2: Wait for processing
    _wait_for_container(token, container_id)

    # Step 3: Publish
    publish_url = f"{base}/{account_id}/media_publish"
    params = {
        "creation_id": container_id,
        "access_token": token,
    }

    resp = requests.post(publish_url, params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Publish failed ({resp.status_code}): {resp.text}")

    post_id = resp.json()["id"]
    return {"status": "success", "post_id": post_id, "platform": "instagram"}


def post_reel(token: str, account_id: str, video_url: str, caption: str) -> dict:
    """Post a reel (video) to Instagram.
    Note: Instagram API requires a PUBLIC URL for videos.
    """
    base = "https://graph.facebook.com/v21.0"

    # Step 1: Create reel container
    create_url = f"{base}/{account_id}/media"
    params = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": token,
    }

    resp = requests.post(create_url, params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Reel container failed ({resp.status_code}): {resp.text}")

    container_id = resp.json()["id"]
    print(f"  Reel container created: {container_id}")

    # Step 2: Wait for video processing (can take 30-60 seconds)
    _wait_for_container(token, container_id, max_wait=120)

    # Step 3: Publish
    publish_url = f"{base}/{account_id}/media_publish"
    params = {
        "creation_id": container_id,
        "access_token": token,
    }

    resp = requests.post(publish_url, params=params, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Reel publish failed ({resp.status_code}): {resp.text}")

    post_id = resp.json()["id"]
    return {"status": "success", "post_id": post_id, "platform": "instagram", "type": "reel"}


def _wait_for_container(token: str, container_id: str, max_wait: int = 60):
    """Wait for media container to finish processing."""
    base = "https://graph.facebook.com/v21.0"
    check_url = f"{base}/{container_id}"
    params = {"fields": "status_code", "access_token": token}

    elapsed = 0
    while elapsed < max_wait:
        resp = requests.get(check_url, params=params, timeout=10)
        if resp.status_code == 200:
            status = resp.json().get("status_code")
            if status == "FINISHED":
                return
            elif status == "ERROR":
                raise Exception(f"Container processing failed: {resp.json()}")
        time.sleep(5)
        elapsed += 5
        print(f"  Processing... ({elapsed}s)")

    raise Exception(f"Container processing timed out after {max_wait}s")


def post_to_instagram(text: str, media: list = None) -> dict:
    """Post to Instagram. Called by draft_manager."""
    token, account_id = get_config()

    if not media or len(media) == 0:
        return {"status": "error", "reason": "Instagram requires at least one image or video", "platform": "instagram"}

    media_path = media[0]

    # Check if it's a URL or local file
    if media_path.startswith("http"):
        media_url = media_path
    elif os.path.exists(media_path):
        # Instagram API needs public URLs — local files need to be uploaded somewhere first
        return {
            "status": "error",
            "reason": "Instagram API requires public URLs for media. Upload the image to a hosting service first, or use a temp file host.",
            "platform": "instagram",
            "hint": "You can use: imgbb.com (free API), Cloudinary, or Supabase Storage",
        }
    else:
        return {"status": "error", "reason": f"Media not found: {media_path}", "platform": "instagram"}

    # Detect type
    if any(media_url.lower().endswith(ext) for ext in [".mp4", ".mov", ".avi"]):
        result = post_reel(token, account_id, media_url, text)
    else:
        result = post_image(token, account_id, media_url, text)

    print(f"  Instagram: {'Posted' if result['status'] == 'success' else 'FAILED'}")
    return result


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Post to Instagram")
    parser.add_argument("--caption", required=True, help="Post caption")
    parser.add_argument("--image", type=str, help="Public URL of image")
    parser.add_argument("--video", type=str, help="Public URL of video (for reels)")
    parser.add_argument("--reel", action="store_true", help="Post as reel")

    args = parser.parse_args()

    if args.video or args.reel:
        media_url = args.video or args.image
        if not media_url:
            print("Error: --video URL required for reels")
            sys.exit(1)
        result = post_to_instagram(args.caption, [media_url])
    elif args.image:
        result = post_to_instagram(args.caption, [args.image])
    else:
        print("Error: --image or --video required for Instagram")
        sys.exit(1)

    print(json.dumps(result, indent=2))
