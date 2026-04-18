#!/usr/bin/env python3
"""
Daily LinkedIn Post — runs in GitHub Actions

Picks today's topic from topics/topics.md (based on day of year),
generates a post with AI (Euri + gpt-4o), posts to LinkedIn via direct API.

Usage:
  python tools/daily_linkedin.py                 # Post today's topic
  python tools/daily_linkedin.py --dry-run       # Generate but don't post
  python tools/daily_linkedin.py --topic "..."   # Override topic
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def pick_todays_topic(topics_file: Path) -> str:
    """Pick topic based on day of year. Rotates through the list."""
    topics = []
    for line in topics_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---") and not line.startswith("One topic"):
            topics.append(line)

    if not topics:
        raise ValueError("No topics found in topics.md")

    day_of_year = datetime.now(timezone.utc).timetuple().tm_yday
    idx = day_of_year % len(topics)
    return topics[idx]


def generate_linkedin_post(topic_prompt: str) -> str:
    """Use Euri to generate a high-quality LinkedIn post."""
    from openai import OpenAI

    client = OpenAI(
        base_url="https://api.euron.one/api/v1/euri",
        api_key=os.getenv("EURI_API_KEY"),
    )

    system = """You are writing LinkedIn posts in Dhruv Tomar's voice (AIwithDhruv).

VOICE RULES:
- First-person, direct, builder's perspective — NOT a guru/teacher
- Start with a hook that stops scrolling — address a specific audience or fear or contrarian take
- Short paragraphs (1-3 sentences each)
- Use Unicode bold (𝗯𝗼𝗹𝗱) for 1-2 key phrases — NOT markdown
- Include specific numbers and concrete examples
- Emotional empathy — acknowledge the reader's fear/situation before giving advice
- End with a question to drive comments
- 3-5 relevant hashtags at the end
- Total length: 180-280 words
- NO em-dashes overused, NO corporate speak, NO "excited to announce"

FORMAT:
- Hook (2-3 lines max)
- Empathetic context (2-3 lines)
- Specific examples or reframes
- Key insight in bold
- Action / reframe
- Question for engagement
- Hashtags

Return ONLY the post text. No preamble, no explanation."""

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": topic_prompt},
        ],
        temperature=0.85,
        max_tokens=1500,
    )
    return resp.choices[0].message.content.strip()


def post_to_linkedin(text: str) -> dict:
    """Post to LinkedIn via direct API."""
    import requests

    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.getenv("LINKEDIN_PERSON_URN")

    if not token or not person_urn:
        raise ValueError("LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN required")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202603",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    body = {
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

    resp = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=body, timeout=30)

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id", "success")
        return {"status": "success", "post_id": post_id}
    return {"status": "error", "code": resp.status_code, "detail": resp.text[:300]}


def main():
    parser = argparse.ArgumentParser(description="Daily LinkedIn post")
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't post")
    parser.add_argument("--topic", type=str, help="Override topic")
    args = parser.parse_args()

    load_env()

    topics_file = ROOT / "topics" / "topics.md"

    if args.topic:
        topic = args.topic
    else:
        topic = pick_todays_topic(topics_file)

    print(f"Topic: {topic[:100]}...")
    print()
    print("Generating post...")
    post_text = generate_linkedin_post(topic)

    print("=" * 60)
    print(post_text)
    print("=" * 60)
    print(f"Length: {len(post_text)} chars")
    print()

    if args.dry_run:
        print("DRY RUN — not posted.")
        return

    print("Posting to LinkedIn...")
    result = post_to_linkedin(post_text)
    if result["status"] == "success":
        print(f"POSTED! ID: {result['post_id']}")
    else:
        print(f"FAILED ({result.get('code')}): {result.get('detail')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
