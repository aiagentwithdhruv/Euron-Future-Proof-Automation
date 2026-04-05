#!/usr/bin/env python3
"""
YouTube Uploader — Upload videos via YouTube Data API v3.

Setup:
  1. Create project at https://console.cloud.google.com/
  2. Enable YouTube Data API v3
  3. Create OAuth 2.0 credentials (Desktop App type)
  4. Run first-time auth to get refresh token (see workflows/youtube-auth.md)
  5. Set YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN in .env

Usage:
  python tools/youtube_uploader.py --video /path/to/video.mp4 --title "My Video" --description "..."
  python tools/youtube_uploader.py --video short.mp4 --title "Quick tip" --short
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
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        missing = []
        if not client_id: missing.append("YOUTUBE_CLIENT_ID")
        if not client_secret: missing.append("YOUTUBE_CLIENT_SECRET")
        if not refresh_token: missing.append("YOUTUBE_REFRESH_TOKEN")
        print(f"Error: Missing in .env: {', '.join(missing)}")
        sys.exit(1)

    return client_id, client_secret, refresh_token


def get_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Exchange refresh token for access token."""
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }

    resp = requests.post(url, data=data, timeout=10)
    if resp.status_code != 200:
        raise Exception(f"Token refresh failed ({resp.status_code}): {resp.text}")

    return resp.json()["access_token"]


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list = None,
    privacy: str = "private",
    is_short: bool = False,
) -> dict:
    """Upload a video to YouTube using resumable upload."""
    client_id, client_secret, refresh_token = get_config()
    access_token = get_access_token(client_id, client_secret, refresh_token)

    if not os.path.exists(video_path):
        return {"status": "error", "reason": f"Video not found: {video_path}", "platform": "youtube"}

    file_size = os.path.getsize(video_path)
    print(f"  Uploading: {video_path} ({file_size / 1024 / 1024:.1f} MB)")

    # For shorts, add #Shorts to title if not present
    if is_short and "#Shorts" not in title:
        title = f"{title} #Shorts"

    # Step 1: Initialize resumable upload
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:30],
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "privacyStatus": privacy,  # "private", "unlisted", or "public"
            "selfDeclaredMadeForKids": False,
        },
    }

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Upload-Content-Type": "video/*",
        "X-Upload-Content-Length": str(file_size),
    }

    resp = requests.post(init_url, headers=headers, json=metadata, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Upload init failed ({resp.status_code}): {resp.text}")

    upload_url = resp.headers["Location"]

    # Step 2: Upload video binary
    upload_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "video/*",
        "Content-Length": str(file_size),
    }

    with open(video_path, "rb") as f:
        resp = requests.put(upload_url, headers=upload_headers, data=f, timeout=600)

    if resp.status_code in (200, 201):
        video_data = resp.json()
        video_id = video_data["id"]
        print(f"  YouTube: Uploaded successfully (ID: {video_id})")
        print(f"  URL: https://youtube.com/watch?v={video_id}")
        return {
            "status": "success",
            "post_id": video_id,
            "url": f"https://youtube.com/watch?v={video_id}",
            "platform": "youtube",
        }
    else:
        error = resp.text[:500]
        print(f"  YouTube: FAILED ({resp.status_code}): {error}")
        return {"status": "error", "reason": error, "platform": "youtube"}


def upload_to_youtube(post_data: dict) -> dict:
    """Upload to YouTube from draft data. Called by draft_manager."""
    video_path = post_data.get("video")
    if not video_path:
        return {"status": "error", "reason": "No video path provided", "platform": "youtube"}

    return upload_video(
        video_path=video_path,
        title=post_data.get("title", "Untitled"),
        description=post_data.get("description", ""),
        tags=post_data.get("tags", []),
        privacy="private",  # Default to private for safety
    )


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Upload to YouTube")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title (max 100 chars)")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", type=str, default="", help="Comma-separated tags")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--short", action="store_true", help="Mark as YouTube Short")

    args = parser.parse_args()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    result = upload_video(
        video_path=args.video,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy=args.privacy,
        is_short=args.short,
    )
    print(json.dumps(result, indent=2))
