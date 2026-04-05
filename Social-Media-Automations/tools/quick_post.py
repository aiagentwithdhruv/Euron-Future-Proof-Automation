#!/usr/bin/env python3
"""Quick post to LinkedIn with AI-generated image (Nano Banana 2)."""
import os, sys, requests
from pathlib import Path

# Load env
env_path = Path(__file__).parent.parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from openai import OpenAI
from PIL import Image

token = os.getenv("LINKEDIN_ACCESS_TOKEN")
person_urn = os.getenv("LINKEDIN_PERSON_URN")
euri_key = os.getenv("EURI_API_KEY")

POST_TEXT = """AI is not replacing humans. It is freeing them.

The smartest companies in 2026 are not asking "should we automate?" — they are asking "what should our people focus on instead?"

Every hour spent on repetitive tasks is an hour stolen from strategy and creativity.

AI handles the repetitive. Humans handle the meaningful.

Which side are you on?

#AIAutomation #FutureOfWork #AI #Leadership"""

# 1. Generate image
print("1. Generating image with Nano Banana 2...")
client = OpenAI(base_url="https://api.euron.one/api/v1/euri", api_key=euri_key)
resp = client.images.generate(
    model="gemini-3.1-flash-image-preview",
    prompt="Clean LinkedIn visual: human hand and robot hand collaborating on holographic dashboard, blue-purple gradient, modern corporate, minimal",
    size="1024x1024", n=1,
)
image_url = resp.data[0].url
print(f"   Generated: {image_url[:80]}...")

# 2. Download + compress
print("2. Downloading + compressing...")
img_data = requests.get(image_url, timeout=30).content
media_dir = Path(__file__).parent.parent / ".tmp" / "media"
media_dir.mkdir(parents=True, exist_ok=True)
raw_path = media_dir / "raw.png"
jpg_path = media_dir / "post.jpg"
with open(raw_path, "wb") as f:
    f.write(img_data)
Image.open(raw_path).convert("RGB").resize((1200, 627)).save(jpg_path, "JPEG", quality=80)
print(f"   Compressed: {os.path.getsize(jpg_path)/1024:.0f} KB")

# 3. Register LinkedIn upload
print("3. Registering upload...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "LinkedIn-Version": "202603",
    "X-Restli-Protocol-Version": "2.0.0",
}
reg = requests.post(
    "https://api.linkedin.com/rest/images?action=initializeUpload",
    headers=headers,
    json={"initializeUploadRequest": {"owner": f"urn:li:person:{person_urn}"}},
    timeout=30,
)
data = reg.json()["value"]
upload_url, image_urn = data["uploadUrl"], data["image"]
print(f"   URN: {image_urn}")

# 4. Upload image
print("4. Uploading image to LinkedIn...")
with open(jpg_path, "rb") as f:
    img_bytes = f.read()
resp = requests.put(
    upload_url,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
    data=img_bytes,
    timeout=300,
)
print(f"   Upload: {resp.status_code}")

# 5. Post
print("5. Posting...")
post_body = {
    "author": f"urn:li:person:{person_urn}",
    "lifecycleState": "PUBLISHED",
    "visibility": "PUBLIC",
    "commentary": POST_TEXT,
    "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
    "content": {"media": {"id": image_urn, "title": "AI Automation"}},
}
resp = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=post_body, timeout=30)
if resp.status_code in (200, 201):
    print(f"\nPOSTED! ID: {resp.headers.get('x-restli-id', 'success')}")
else:
    print(f"\nError ({resp.status_code}): {resp.text[:300]}")
