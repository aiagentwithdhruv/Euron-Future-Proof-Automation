#!/usr/bin/env python3
"""
Content Engine — Generate platform-optimized social media content using AI.

Usage:
  # AI mode: generate from topic
  python tools/content_engine.py --topic "AI agents are replacing SaaS" --platforms linkedin,x,instagram

  # Manual mode: adapt your text for each platform
  python tools/content_engine.py --text "Your raw content here" --platforms linkedin,x

  # From URL: extract and generate posts from a link
  python tools/content_engine.py --url "https://example.com/article" --platforms linkedin,x
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow importing draft_manager from same directory
sys.path.insert(0, os.path.dirname(__file__))
from draft_manager import save_draft

# LLM client setup
def get_llm_client():
    """Get OpenAI-compatible LLM client. Tries Euri first, then OpenRouter."""
    try:
        from openai import OpenAI
    except ImportError:
        print("Error: pip install openai")
        sys.exit(1)

    if os.getenv("EURI_API_KEY"):
        return OpenAI(
            base_url="https://api.euron.one/api/v1/euri",
            api_key=os.getenv("EURI_API_KEY"),
        ), "gpt-4o-mini"
    elif os.getenv("OPENROUTER_API_KEY"):
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        ), "anthropic/claude-sonnet-4-6"
    else:
        print("Error: Set EURI_API_KEY or OPENROUTER_API_KEY in .env")
        sys.exit(1)


PLATFORM_PROMPTS = {
    "linkedin": """Write a LinkedIn post about this topic. Rules:
- Professional but conversational tone
- 150-300 words (sweet spot for engagement)
- Start with a strong hook (first 2 lines are visible before "see more")
- Use line breaks for readability (short paragraphs)
- End with a question or call-to-action to drive comments
- Include 3-5 relevant hashtags at the end
- No emojis unless they add meaning
- Max 3000 characters""",

    "x": """Write a tweet about this topic. Rules:
- Punchy, direct, opinionated
- Max 280 characters (STRICT — count carefully)
- No hashtags in the main text unless they're essential
- If the idea needs more space, write a thread (2-3 tweets, numbered)
- First tweet must hook — it's the only one people see in feed
- Be specific, not generic""",

    "instagram": """Write an Instagram caption about this topic. Rules:
- First line is the hook (people see only 2 lines before "more")
- 100-200 words ideal
- Conversational, slightly casual
- End with a CTA (save this, share, comment your thoughts)
- Put hashtags at the END, separated by dots or line breaks
- 15-25 relevant hashtags
- Format for mobile reading (short lines)""",

    "youtube": """Write a YouTube video title + description about this topic. Rules:
- TITLE: Under 60 characters, curiosity-driven, include main keyword
- DESCRIPTION: 200-500 words
  - First 2 lines: hook + main value (visible without expanding)
  - Summary of what the video covers
  - Timestamps if applicable
  - Links/resources
  - CTA to subscribe
- TAGS: 10-15 relevant tags, comma-separated
- Return as JSON: {"title": "...", "description": "...", "tags": ["...", "..."]}""",
}


def generate_posts(topic: str, platforms: list, custom_instructions: str = None) -> dict:
    """Generate platform-optimized posts from a topic."""
    client, model = get_llm_client()
    posts = {}

    for platform in platforms:
        prompt = PLATFORM_PROMPTS.get(platform, "Write a social media post about this topic.")

        if custom_instructions:
            prompt += f"\n\nAdditional instructions: {custom_instructions}"

        messages = [
            {"role": "system", "content": f"You are a social media content expert. You write content for {platform}. Return ONLY the post text, no explanations or meta-commentary."},
            {"role": "user", "content": f"Topic: {topic}\n\n{prompt}"},
        ]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.8,
                max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()

            if platform == "youtube":
                # Try to parse as JSON for youtube
                try:
                    yt_data = json.loads(content)
                    posts[platform] = {
                        "title": yt_data.get("title", ""),
                        "description": yt_data.get("description", ""),
                        "tags": yt_data.get("tags", []),
                        "video": None,
                    }
                except json.JSONDecodeError:
                    posts[platform] = {
                        "title": content[:100],
                        "description": content,
                        "tags": [],
                        "video": None,
                    }
            else:
                posts[platform] = {"text": content, "media": []}

            print(f"  [{platform}] Generated ({len(content)} chars)")

        except Exception as e:
            print(f"  [{platform}] ERROR: {e}")
            posts[platform] = {"text": f"Error generating: {e}", "media": []}

    return posts


def adapt_text(text: str, platforms: list) -> dict:
    """Adapt user-provided text for each platform using AI."""
    client, model = get_llm_client()
    posts = {}

    for platform in platforms:
        prompt = PLATFORM_PROMPTS.get(platform, "")

        messages = [
            {"role": "system", "content": f"Adapt the following content for {platform}. Keep the core message but optimize for the platform's format and audience. Return ONLY the adapted post text."},
            {"role": "user", "content": f"Original content:\n{text}\n\n{prompt}"},
        ]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            content = response.choices[0].message.content.strip()

            if platform == "youtube":
                try:
                    yt_data = json.loads(content)
                    posts[platform] = {
                        "title": yt_data.get("title", ""),
                        "description": yt_data.get("description", ""),
                        "tags": yt_data.get("tags", []),
                        "video": None,
                    }
                except json.JSONDecodeError:
                    posts[platform] = {"title": content[:100], "description": content, "tags": [], "video": None}
            else:
                posts[platform] = {"text": content, "media": []}

            print(f"  [{platform}] Adapted ({len(content)} chars)")

        except Exception as e:
            print(f"  [{platform}] ERROR: {e}")
            posts[platform] = {"text": text, "media": []}

    return posts


def load_env():
    """Load .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="Content Engine — generate social media posts")
    parser.add_argument("--topic", type=str, help="Topic to generate posts about")
    parser.add_argument("--text", type=str, help="Raw text to adapt for each platform")
    parser.add_argument("--platforms", type=str, default="linkedin,x",
                        help="Comma-separated platforms (default: linkedin,x)")
    parser.add_argument("--instructions", type=str, help="Additional instructions for AI")
    parser.add_argument("--no-draft", action="store_true", help="Print output without saving draft")

    args = parser.parse_args()
    platforms = [p.strip() for p in args.platforms.split(",")]

    if not args.topic and not args.text:
        print("Error: Provide --topic or --text")
        parser.print_help()
        sys.exit(1)

    print(f"Generating posts for: {', '.join(platforms)}")
    print()

    if args.topic:
        posts = generate_posts(args.topic, platforms, args.instructions)
        mode = "ai"
        topic = args.topic
    else:
        posts = adapt_text(args.text, platforms)
        mode = "manual"
        topic = None

    if args.no_draft:
        print("\n" + json.dumps(posts, indent=2))
    else:
        draft_content = {
            "platforms": platforms,
            "posts": posts,
            "topic": topic,
            "mode": mode,
        }
        draft_id = save_draft(draft_content)
        print(f"\nDraft saved. Review with: python tools/draft_manager.py --show {draft_id}")
        print(f"Approve with: python tools/draft_manager.py --approve {draft_id}")
