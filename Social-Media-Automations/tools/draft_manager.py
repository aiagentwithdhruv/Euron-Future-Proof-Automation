#!/usr/bin/env python3
"""
Draft Manager — save, list, review, approve, and post drafts.
Central to the Draft -> Approve -> Post workflow.

Usage:
  python tools/draft_manager.py --save --content "Hello world" --platforms linkedin,x
  python tools/draft_manager.py --list
  python tools/draft_manager.py --show <draft_id>
  python tools/draft_manager.py --approve <draft_id>
  python tools/draft_manager.py --post <draft_id>
  python tools/draft_manager.py --delete <draft_id>
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

DRAFTS_DIR = Path(__file__).parent.parent / ".tmp" / "drafts"
RUNS_DIR = Path(__file__).parent.parent / "runs"


def save_draft(content: dict) -> str:
    """Save a new draft. Returns draft ID.

    content dict structure:
    {
        "platforms": ["linkedin", "x", "instagram", "youtube"],
        "posts": {
            "linkedin": {"text": "...", "media": ["/path/to/image.jpg"]},
            "x": {"text": "...", "media": ["/path/to/image.jpg"]},
            "instagram": {"text": "...", "media": ["/path/to/image.jpg"]},
            "youtube": {"title": "...", "description": "...", "tags": [...], "video": "/path/to/video.mp4"}
        },
        "topic": "original topic or null",
        "mode": "manual" or "ai"
    }
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    draft_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    draft = {
        "id": draft_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "draft",
        "approved_platforms": [],
        **content,
    }

    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    with open(draft_path, "w") as f:
        json.dump(draft, f, indent=2)

    print(f"Draft saved: {draft_id}")
    return draft_id


def list_drafts(status_filter: str = None) -> list:
    """List all drafts, optionally filtered by status."""
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    drafts = []

    for f in sorted(DRAFTS_DIR.glob("*.json"), reverse=True):
        with open(f) as fp:
            draft = json.load(fp)
            if status_filter and draft.get("status") != status_filter:
                continue
            drafts.append(draft)

    if not drafts:
        print("No drafts found.")
        return drafts

    print(f"\n{'ID':<30} {'Status':<12} {'Platforms':<25} {'Created'}")
    print("-" * 90)
    for d in drafts:
        platforms = ", ".join(d.get("platforms", []))
        created = d["created_at"][:19].replace("T", " ")
        print(f"{d['id']:<30} {d['status']:<12} {platforms:<25} {created}")

    print(f"\nTotal: {len(drafts)} draft(s)")
    return drafts


def show_draft(draft_id: str) -> dict:
    """Show full details of a draft."""
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"Error: Draft '{draft_id}' not found")
        sys.exit(1)

    with open(draft_path) as f:
        draft = json.load(f)

    print(f"\n{'='*60}")
    print(f"Draft: {draft['id']}")
    print(f"Status: {draft['status']}")
    print(f"Created: {draft['created_at']}")
    print(f"Mode: {draft.get('mode', 'manual')}")
    if draft.get("topic"):
        print(f"Topic: {draft['topic']}")
    print(f"{'='*60}")

    posts = draft.get("posts", {})
    for platform, post in posts.items():
        print(f"\n--- {platform.upper()} ---")
        if platform == "youtube":
            print(f"Title: {post.get('title', '')}")
            print(f"Description: {post.get('description', '')[:200]}...")
            print(f"Tags: {', '.join(post.get('tags', []))}")
            if post.get("video"):
                print(f"Video: {post['video']}")
        else:
            print(f"Text ({len(post.get('text', ''))} chars):")
            print(post.get("text", ""))
            if post.get("media"):
                print(f"Media: {', '.join(post['media'])}")

    print(f"\n{'='*60}")
    return draft


def approve_draft(draft_id: str, platforms: list = None) -> dict:
    """Approve a draft for posting."""
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"Error: Draft '{draft_id}' not found")
        sys.exit(1)

    with open(draft_path) as f:
        draft = json.load(f)

    if platforms:
        draft["approved_platforms"] = platforms
    else:
        draft["approved_platforms"] = draft.get("platforms", [])

    draft["status"] = "approved"
    draft["approved_at"] = datetime.now(timezone.utc).isoformat()

    with open(draft_path, "w") as f:
        json.dump(draft, f, indent=2)

    print(f"Draft '{draft_id}' approved for: {', '.join(draft['approved_platforms'])}")
    return draft


def post_draft(draft_id: str) -> dict:
    """Post an approved draft to all approved platforms."""
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"Error: Draft '{draft_id}' not found")
        sys.exit(1)

    with open(draft_path) as f:
        draft = json.load(f)

    if draft["status"] != "approved":
        print(f"Error: Draft must be approved first (current: {draft['status']})")
        sys.exit(1)

    results = {}
    posts = draft.get("posts", {})

    for platform in draft.get("approved_platforms", []):
        post_data = posts.get(platform)
        if not post_data:
            results[platform] = {"status": "skipped", "reason": "no content for platform"}
            continue

        try:
            if platform == "linkedin":
                from linkedin_poster import post_to_linkedin
                result = post_to_linkedin(post_data["text"], post_data.get("media"))
            elif platform == "x":
                from x_poster import post_to_x
                result = post_to_x(post_data["text"], post_data.get("media"))
            elif platform == "instagram":
                from instagram_poster import post_to_instagram
                result = post_to_instagram(post_data["text"], post_data.get("media"))
            elif platform == "youtube":
                from youtube_uploader import upload_to_youtube
                result = upload_to_youtube(post_data)
            else:
                result = {"status": "error", "reason": f"Unknown platform: {platform}"}

            results[platform] = result
            print(f"  [{platform}] {'Posted' if result.get('status') == 'success' else 'FAILED'}")

        except Exception as e:
            results[platform] = {"status": "error", "reason": str(e)}
            print(f"  [{platform}] ERROR: {e}")

    # Update draft status
    draft["status"] = "posted"
    draft["posted_at"] = datetime.now(timezone.utc).isoformat()
    draft["results"] = results

    with open(draft_path, "w") as f:
        json.dump(draft, f, indent=2)

    # Log the run
    _log_run(draft, results)

    return results


def delete_draft(draft_id: str):
    """Delete a draft."""
    draft_path = DRAFTS_DIR / f"{draft_id}.json"
    if not draft_path.exists():
        print(f"Error: Draft '{draft_id}' not found")
        sys.exit(1)

    draft_path.unlink()
    print(f"Draft '{draft_id}' deleted.")


def _log_run(draft: dict, results: dict):
    """Log posting results to runs/."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = RUNS_DIR / f"{today}-social-post.md"

    entry = f"""
### {draft['id']}
- **Time:** {datetime.now(timezone.utc).isoformat()}
- **Mode:** {draft.get('mode', 'manual')}
- **Topic:** {draft.get('topic', 'N/A')}
- **Platforms:** {', '.join(draft.get('approved_platforms', []))}
- **Results:**
"""
    for platform, result in results.items():
        status = result.get("status", "unknown")
        entry += f"  - {platform}: {status}"
        if result.get("post_id"):
            entry += f" (ID: {result['post_id']})"
        if result.get("reason"):
            entry += f" — {result['reason']}"
        entry += "\n"

    with open(log_path, "a") as f:
        f.write(entry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draft Manager — save, list, approve, post")
    parser.add_argument("--save", action="store_true", help="Save a new draft")
    parser.add_argument("--list", action="store_true", help="List all drafts")
    parser.add_argument("--show", type=str, help="Show draft details")
    parser.add_argument("--approve", type=str, help="Approve a draft")
    parser.add_argument("--post", type=str, help="Post an approved draft")
    parser.add_argument("--delete", type=str, help="Delete a draft")
    parser.add_argument("--content", type=str, help="Content text (for --save)")
    parser.add_argument("--platforms", type=str, default="linkedin,x",
                        help="Comma-separated platforms (default: linkedin,x)")
    parser.add_argument("--status", type=str, help="Filter by status (for --list)")

    args = parser.parse_args()

    if args.save:
        platforms = [p.strip() for p in args.platforms.split(",")]
        content = {
            "platforms": platforms,
            "posts": {p: {"text": args.content or "", "media": []} for p in platforms},
            "topic": None,
            "mode": "manual",
        }
        save_draft(content)
    elif args.list:
        list_drafts(args.status)
    elif args.show:
        show_draft(args.show)
    elif args.approve:
        platforms = [p.strip() for p in args.platforms.split(",")] if args.platforms else None
        approve_draft(args.approve, platforms)
    elif args.post:
        post_draft(args.post)
    elif args.delete:
        delete_draft(args.delete)
    else:
        parser.print_help()
