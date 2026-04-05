#!/usr/bin/env python3
"""
Post to ALL platforms in one command.

LinkedIn  = Direct API (text + image via curl)
X/Twitter = Blotato (text + image)
Instagram = Blotato (caption + video/image)
YouTube   = Blotato (title + description + video)

Usage:
  python tools/post_all.py --topic "AI agents" --image /path/to/img.png --video /path/to/video.mp4
  python tools/post_all.py --text-file content.json --image photo.jpg --video reel.mp4
  python tools/post_all.py --linkedin "LI text" --x "tweet" --instagram "caption" --youtube-title "Title" --youtube-desc "desc" --image img.png --video vid.mp4
"""

import argparse
import json
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

# ── Load env ──────────────────────────────────────────────
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

# ── Blotato helpers ───────────────────────────────────────
BLOTATO_BASE = "https://backend.blotato.com/v2"

def bh(json_type=True):
    h = {"blotato-api-key": os.getenv("BLOTATO_API_KEY")}
    if json_type:
        h["Content-Type"] = "application/json"
    return h

def host_file(path: str) -> str:
    """Upload local file to tmpfiles.org, return direct URL."""
    with open(path, "rb") as f:
        r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=300)
    url = r.json()["data"]["url"]
    return url.replace("tmpfiles.org/", "tmpfiles.org/dl/")

def poll_blotato(sid: str, max_wait=120):
    for _ in range(max_wait // 5):
        r = requests.get(f"{BLOTATO_BASE}/posts/{sid}", headers=bh(), timeout=10).json()
        st = r.get("status", "")
        if st == "published":
            return r
        if "fail" in st.lower():
            return r
        time.sleep(5)
    return {"status": "timeout"}

def ensure_mp4(path: str) -> str:
    if not path.lower().endswith(".mkv"):
        return path
    mp4 = "/tmp/post_all_video.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", path, "-c:v", "libx264", "-c:a", "aac",
                    "-movflags", "+faststart", "-preset", "fast", mp4],
                   capture_output=True, timeout=180)
    return mp4

# ── LinkedIn (Direct API) ────────────────────────────────
def post_linkedin(text: str, image_path: str = None) -> dict:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = os.getenv("LINKEDIN_PERSON_URN")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
               "LinkedIn-Version": "202603", "X-Restli-Protocol-Version": "2.0.0"}

    image_urn = None
    if image_path and os.path.exists(image_path):
        # Compress
        from PIL import Image
        jpg = Path("/tmp/li_post.jpg")
        Image.open(image_path).convert("RGB").resize((1200, 627)).save(jpg, "JPEG", quality=80)

        # Register + upload via curl
        reg = requests.post("https://api.linkedin.com/rest/images?action=initializeUpload",
                           headers=headers, json={"initializeUploadRequest": {"owner": f"urn:li:person:{urn}"}}, timeout=30)
        data = reg.json()["value"]
        image_urn = data["image"]

        cr = subprocess.run(["curl", "-s", "-w", "%{http_code}", "--max-time", "120", "-X", "PUT",
                            "-H", f"Authorization: Bearer {token}", "-H", "Content-Type: application/octet-stream",
                            "--data-binary", f"@{jpg}", data["uploadUrl"]],
                           capture_output=True, text=True, timeout=130)
        code = cr.stdout.strip()[-3:] if cr.stdout else "000"
        if code not in ("200", "201"):
            image_urn = None

    body = {"author": f"urn:li:person:{urn}", "lifecycleState": "PUBLISHED", "visibility": "PUBLIC",
            "commentary": text, "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []}}
    if image_urn:
        body["content"] = {"media": {"id": image_urn, "title": "Post image"}}

    resp = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=body, timeout=30)
    if resp.status_code in (200, 201):
        return {"status": "success", "id": resp.headers.get("x-restli-id", "ok")}
    return {"status": "error", "detail": resp.text[:200]}

# ── X/Twitter (Blotato) ──────────────────────────────────
def post_x(text: str, image_path: str = None) -> dict:
    media = []
    if image_path and os.path.exists(image_path):
        media = [host_file(image_path)]

    payload = {"post": {"accountId": os.getenv("BLOTATO_X_ID"),
               "content": {"text": text, "mediaUrls": media, "platform": "twitter"},
               "target": {"targetType": "twitter"}}}
    r = requests.post(f"{BLOTATO_BASE}/posts", headers=bh(), json=payload, timeout=60)
    if r.status_code not in (200, 201):
        return {"status": "error", "detail": r.text[:200]}
    sid = r.json().get("postSubmissionId", "")
    return poll_blotato(sid) if sid else {"status": "submitted"}

# ── Instagram (Blotato) ──────────────────────────────────
def post_instagram(caption: str, media_path: str = None) -> dict:
    media = []
    if media_path and os.path.exists(media_path):
        mp4 = ensure_mp4(media_path) if any(media_path.lower().endswith(e) for e in [".mkv", ".mp4", ".mov"]) else media_path
        media = [host_file(mp4)]

    payload = {"post": {"accountId": os.getenv("BLOTATO_INSTAGRAM_ID"),
               "content": {"text": caption, "mediaUrls": media, "platform": "instagram"},
               "target": {"targetType": "instagram"}}}
    r = requests.post(f"{BLOTATO_BASE}/posts", headers=bh(), json=payload, timeout=60)
    if r.status_code not in (200, 201):
        return {"status": "error", "detail": r.text[:200]}
    sid = r.json().get("postSubmissionId", "")
    return poll_blotato(sid) if sid else {"status": "submitted"}

# ── YouTube (Blotato) ────────────────────────────────────
def post_youtube(title: str, description: str, video_path: str) -> dict:
    if not video_path or not os.path.exists(video_path):
        return {"status": "error", "detail": "YouTube requires a video file"}

    mp4 = ensure_mp4(video_path)
    video_url = host_file(mp4)

    payload = {"post": {"accountId": os.getenv("BLOTATO_YOUTUBE_ID"),
               "content": {"text": description, "mediaUrls": [video_url], "platform": "youtube"},
               "target": {"targetType": "youtube", "title": title[:100],
                          "privacyStatus": "public", "shouldNotifySubscribers": False}}}
    r = requests.post(f"{BLOTATO_BASE}/posts", headers=bh(), json=payload, timeout=60)
    if r.status_code not in (200, 201):
        return {"status": "error", "detail": r.text[:200]}
    sid = r.json().get("postSubmissionId", "")
    return poll_blotato(sid, max_wait=300) if sid else {"status": "submitted"}


# ── Main ──────────────────────────────────────────────────
if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Post to ALL platforms at once")
    parser.add_argument("--linkedin", type=str, help="LinkedIn post text")
    parser.add_argument("--x", type=str, help="X/Twitter tweet text")
    parser.add_argument("--instagram", type=str, help="Instagram caption (max 5 hashtags!)")
    parser.add_argument("--youtube-title", type=str, help="YouTube video title")
    parser.add_argument("--youtube-desc", type=str, help="YouTube video description")
    parser.add_argument("--image", type=str, help="Image path (for LinkedIn + X)")
    parser.add_argument("--video", type=str, help="Video path (for Instagram + YouTube)")
    parser.add_argument("--platforms", type=str, default="linkedin,x,instagram,youtube",
                        help="Comma-separated platforms to post to")

    args = parser.parse_args()
    platforms = [p.strip() for p in args.platforms.split(",")]
    results = {}

    if "linkedin" in platforms and args.linkedin:
        print(f"[LinkedIn] Posting...")
        try:
            results["linkedin"] = post_linkedin(args.linkedin, args.image)
            print(f"[LinkedIn] {results['linkedin'].get('status', '?')}")
        except Exception as e:
            results["linkedin"] = {"status": "error", "detail": str(e)}
            print(f"[LinkedIn] ERROR: {e}")

    if "x" in platforms and args.x:
        print(f"[X] Posting...")
        try:
            results["x"] = post_x(args.x, args.image)
            print(f"[X] {results['x'].get('status', '?')}")
        except Exception as e:
            results["x"] = {"status": "error", "detail": str(e)}
            print(f"[X] ERROR: {e}")

    if "instagram" in platforms and args.instagram:
        print(f"[Instagram] Posting...")
        try:
            results["instagram"] = post_instagram(args.instagram, args.video or args.image)
            print(f"[Instagram] {results['instagram'].get('status', '?')}")
        except Exception as e:
            results["instagram"] = {"status": "error", "detail": str(e)}
            print(f"[Instagram] ERROR: {e}")

    if "youtube" in platforms and args.youtube_title:
        print(f"[YouTube] Posting...")
        try:
            results["youtube"] = post_youtube(args.youtube_title, args.youtube_desc or "", args.video)
            print(f"[YouTube] {results['youtube'].get('status', '?')}")
        except Exception as e:
            results["youtube"] = {"status": "error", "detail": str(e)}
            print(f"[YouTube] ERROR: {e}")

    print("\n" + "=" * 40)
    print("RESULTS")
    print("=" * 40)
    for p, r in results.items():
        status = r.get("status", "?")
        url = r.get("publicUrl", "")
        print(f"  {p:<12} {status} {url}")
