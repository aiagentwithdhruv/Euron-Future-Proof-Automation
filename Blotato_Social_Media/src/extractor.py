"""YouTube content extraction via Blotato."""

from src.client import BlotatoClient


def extract_video(client: BlotatoClient, url: str) -> dict:
    """Extract title, transcript, and metadata from a YouTube video.

    Returns:
        {"title": str, "content": str}
    """
    print("\n[1/4] Extracting YouTube video content...")
    data = client.extract_youtube(url)

    title = data.get("title", "Untitled")
    content = data.get("content", "")

    print(f"  Title: {title}")
    print(f"  Content: {len(content)} chars extracted")

    return {"title": title, "content": content}
