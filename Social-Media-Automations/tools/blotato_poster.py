#!/usr/bin/env python3
"""
Blotato Poster — Post to Twitter, Instagram, YouTube via Blotato API.
Correct API: https://backend.blotato.com/v2
Auth: blotato-api-key header (NOT Bearer token)

LEARNED THE HARD WAY:
- Platform name for X is "twitter" not "x"
- Instagram max 5 hashtags via Blotato
- YouTube target needs: title, privacyStatus, shouldNotifySubscribers
- Blotato needs PUBLIC URLs for media, not local files
- All operations are async — poll for completion
- Use postSubmissionId (not id) for polling
"""

import os
import sys
import time
import json
import subprocess
import requests
from pathlib import Path

BASE_URL = "https://backend.blotato.com/v2"

# Blotato uses "twitter" not "x"
PLATFORM_MAP = {"x": "twitter", "twitter": "twitter", "instagram": "instagram", "youtube": "youtube", "linkedin": "linkedin"}


def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())


def get_headers(json_content=True):
    key = os.getenv("BLOTATO_API_KEY")
    if not key:
        raise ValueError("BLOTATO_API_KEY not set in .env")
    h = {"blotato-api-key": key}
    if json_content:
        h["Content-Type"] = "application/json"
    return h


def get_account_id(platform: str) -> str:
    env_map = {
        "twitter": "BLOTATO_X_ID",
        "instagram": "BLOTATO_INSTAGRAM_ID",
        "youtube": "BLOTATO_YOUTUBE_ID",
        "linkedin": "BLOTATO_LINKEDIN_ID",
    }
    p = PLATFORM_MAP.get(platform, platform)
    val = os.getenv(env_map.get(p, ""))
    if not val:
        raise ValueError(f"No account ID for {platform}")
    return val


def host_local_file(file_path: str) -> str:
    """Upload a local file to tmpfiles.org and return the direct download URL."""
    print(f"    Hosting file ({os.path.getsize(file_path)/1024/1024:.1f} MB)...")
    with open(file_path, "rb") as f:
        resp = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=300)
    if resp.status_code != 200:
        raise Exception(f"File hosting failed ({resp.status_code})")
    url = resp.json()["data"]["url"]
    # Convert to direct download URL
    direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    print(f"    Hosted: {direct_url[:60]}...")
    return direct_url


def convert_mkv_to_mp4(mkv_path: str) -> str:
    """Convert MKV to MP4 if needed."""
    if not mkv_path.lower().endswith(".mkv"):
        return mkv_path
    mp4_path = "/tmp/blotato_video.mp4"
    print("    Converting MKV to MP4...")
    subprocess.run(
        ["ffmpeg", "-y", "-i", mkv_path, "-c:v", "libx264", "-c:a", "aac",
         "-movflags", "+faststart", "-preset", "fast", mp4_path],
        capture_output=True, timeout=180,
    )
    print(f"    Converted: {os.path.getsize(mp4_path)/1024/1024:.1f} MB")
    return mp4_path


def poll_post(submission_id: str, max_wait: int = 120) -> dict:
    """Poll until post is published or failed."""
    headers = get_headers()
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{BASE_URL}/posts/{submission_id}", headers=headers, timeout=10)
        data = resp.json()
        status = data.get("status", "")
        if status == "published":
            return data
        elif "fail" in status.lower():
            raise Exception(f"Post failed: {data}")
        time.sleep(5)
    return {"status": "timeout", "note": "Still processing — check platform manually"}


def post_to_twitter(text: str, image_path: str = None) -> dict:
    """Post to X/Twitter via Blotato."""
    media_urls = []
    if image_path and os.path.exists(image_path):
        media_urls = [host_local_file(image_path)]

    payload = {
        "post": {
            "accountId": get_account_id("twitter"),
            "content": {"text": text, "mediaUrls": media_urls, "platform": "twitter"},
            "target": {"targetType": "twitter"},
        }
    }
    resp = requests.post(f"{BASE_URL}/posts", headers=get_headers(), json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise Exception(f"Twitter post failed ({resp.status_code}): {resp.text[:200]}")

    sid = resp.json().get("postSubmissionId", resp.json().get("id", ""))
    return poll_post(sid) if sid else resp.json()


def post_to_instagram(caption: str, media_path: str = None) -> dict:
    """Post to Instagram via Blotato. Max 5 hashtags!"""
    media_urls = []
    if media_path and os.path.exists(media_path):
        if media_path.lower().endswith(".mkv"):
            media_path = convert_mkv_to_mp4(media_path)
        media_urls = [host_local_file(media_path)]

    payload = {
        "post": {
            "accountId": get_account_id("instagram"),
            "content": {"text": caption, "mediaUrls": media_urls, "platform": "instagram"},
            "target": {"targetType": "instagram"},
        }
    }
    resp = requests.post(f"{BASE_URL}/posts", headers=get_headers(), json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise Exception(f"Instagram post failed ({resp.status_code}): {resp.text[:200]}")

    sid = resp.json().get("postSubmissionId", resp.json().get("id", ""))
    return poll_post(sid) if sid else resp.json()


def post_to_youtube(title: str, description: str, video_path: str, privacy: str = "public") -> dict:
    """Post to YouTube via Blotato. Video required!"""
    if not video_path or not os.path.exists(video_path):
        raise ValueError("YouTube requires a video file")

    if video_path.lower().endswith(".mkv"):
        video_path = convert_mkv_to_mp4(video_path)

    video_url = host_local_file(video_path)

    payload = {
        "post": {
            "accountId": get_account_id("youtube"),
            "content": {"text": description, "mediaUrls": [video_url], "platform": "youtube"},
            "target": {
                "targetType": "youtube",
                "title": title[:100],
                "privacyStatus": privacy,
                "shouldNotifySubscribers": False,
            },
        }
    }
    resp = requests.post(f"{BASE_URL}/posts", headers=get_headers(), json=payload, timeout=60)
    if resp.status_code not in (200, 201):
        raise Exception(f"YouTube post failed ({resp.status_code}): {resp.text[:200]}")

    sid = resp.json().get("postSubmissionId", resp.json().get("id", ""))
    return poll_post(sid, max_wait=300) if sid else resp.json()


if __name__ == "__main__":
    import argparse
    load_env()

    parser = argparse.ArgumentParser(description="Post via Blotato")
    parser.add_argument("--platform", required=True, choices=["x", "twitter", "instagram", "youtube"])
    parser.add_argument("--text", required=True, help="Post text")
    parser.add_argument("--image", type=str, help="Image path (twitter)")
    parser.add_argument("--video", type=str, help="Video path (instagram, youtube)")
    parser.add_argument("--title", type=str, help="Video title (youtube)")

    args = parser.parse_args()
    p = args.platform

    if p in ("x", "twitter"):
        result = post_to_twitter(args.text, args.image)
    elif p == "instagram":
        result = post_to_instagram(args.text, args.video or args.image)
    elif p == "youtube":
        result = post_to_youtube(args.title or "Untitled", args.text, args.video)

    print(json.dumps(result, indent=2))
