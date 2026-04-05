#!/usr/bin/env python3
"""
repurpose-youtube-video — Turn any YouTube video into social media posts.

Usage:
    python run.py <youtube_url>                              # Draft mode (review first)
    python run.py <youtube_url> --publish                    # Auto-publish to all
    python run.py <youtube_url> --platforms linkedin,x       # Specific platforms
    python run.py <youtube_url> --publish --schedule "2026-03-25T15:00:00Z"
"""

import argparse
import json
import sys

from src.config import DATA_DIR, PLATFORMS
from src.client import BlotatoClient
from src.extractor import extract_video
from src.generator import generate_posts, generate_visuals
from src.publisher import publish_all


DRAFTS_PATH = DATA_DIR / "drafts.json"


def show_drafts(posts: dict, visuals: dict):
    """Display drafts for user review."""
    print("\n" + "=" * 60)
    print("  DRAFT REVIEW")
    print("=" * 60)
    for platform in posts:
        print(f"\n--- {platform.upper()} ---")
        print(f"Text: {posts[platform]['text']}")
        print(f"Prompt: {posts[platform]['prompt_used'][:200]}...")
        print(f"Visual: {visuals.get(platform, 'None')}")
    print()


def save_drafts(url: str, video_data: dict, posts: dict,
                visuals: dict, platforms: list[str]):
    """Save drafts to JSON for review and later publishing."""
    DRAFTS_PATH.write_text(json.dumps({
        "youtube_url": url,
        "video_data": video_data,
        "posts": posts,
        "visuals": visuals,
        "platforms": platforms,
    }, indent=2))
    print(f"Drafts saved to: {DRAFTS_PATH}")
    print("Edit the drafts, then run: python run.py --publish-drafts")


def publish_drafts(client: BlotatoClient, schedule_time: str | None = None):
    """Load and publish previously saved drafts."""
    if not DRAFTS_PATH.exists():
        print("Error: No drafts found. Run `python run.py <youtube_url>` first.")
        sys.exit(1)

    drafts = json.loads(DRAFTS_PATH.read_text())
    results = publish_all(
        client,
        drafts["youtube_url"],
        drafts["posts"],
        drafts["visuals"],
        schedule_time,
    )
    print_results(results)


def print_results(results: dict):
    """Display publishing results."""
    print("\n" + "=" * 60)
    print("  PUBLISHING COMPLETE")
    print("=" * 60)
    for platform, result in results.items():
        status = result.get("status", "unknown")
        url = result.get("url", "")
        print(f"  {platform.upper()}: {status} {url}")
    print(f"\nFull log: data/posts_log.md")


def main():
    parser = argparse.ArgumentParser(
        description="Repurpose YouTube videos into LinkedIn, Instagram, and X posts."
    )
    parser.add_argument("url", nargs="?", help="YouTube video URL")
    parser.add_argument(
        "--publish", action="store_true",
        help="Auto-publish (skip draft review)"
    )
    parser.add_argument(
        "--publish-drafts", action="store_true",
        help="Publish previously saved drafts from data/drafts.json"
    )
    parser.add_argument(
        "--platforms", default="linkedin,x,instagram",
        help="Comma-separated platforms (default: linkedin,x,instagram)"
    )
    parser.add_argument(
        "--schedule", default=None,
        help="Schedule time in ISO 8601 (e.g., 2026-03-25T15:00:00Z)"
    )
    args = parser.parse_args()

    # Initialize client
    try:
        client = BlotatoClient()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Publish existing drafts
    if args.publish_drafts:
        publish_drafts(client, args.schedule)
        return

    # Require URL for new repurpose
    if not args.url:
        parser.print_help()
        sys.exit(1)

    platforms = [p.strip().lower() for p in args.platforms.split(",")]
    for p in platforms:
        if p not in PLATFORMS:
            print(f"Error: Unknown platform '{p}'. Choose from: {', '.join(PLATFORMS)}")
            sys.exit(1)

    print(f"Repurposing for: {', '.join(p.upper() for p in platforms)}")
    print(f"Mode: {'Auto-publish' if args.publish else 'Draft review'}")

    # Step 1: Extract
    video_data = extract_video(client, args.url)

    # Step 2: Generate posts
    posts = generate_posts(video_data["title"], video_data["content"], platforms)

    # Step 3: Generate visuals
    visuals = generate_visuals(client, video_data["title"], platforms)

    # Step 4: Draft or publish
    if args.publish:
        results = publish_all(client, args.url, posts, visuals, args.schedule)
        print_results(results)
    else:
        show_drafts(posts, visuals)
        save_drafts(args.url, video_data, posts, visuals, platforms)


if __name__ == "__main__":
    main()
