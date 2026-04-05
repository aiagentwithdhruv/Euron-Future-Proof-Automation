"""Publishing posts to social platforms via Blotato."""

from src.client import BlotatoClient
from src.logger import log_post


def publish_all(client: BlotatoClient, youtube_url: str, posts: dict,
                visuals: dict, schedule_time: str | None = None) -> dict:
    """Publish posts to all platforms. Returns results per platform."""
    print("\n[4/4] Publishing posts...")
    results = {}

    for platform in posts:
        account = client.find_account(platform)
        if not account:
            print(f"  {platform.upper()}: No connected account. Skipping.")
            log_post(youtube_url, platform, posts[platform]["text"],
                     visuals.get(platform, ""), "", "skipped — no account")
            continue

        account_id = account["id"]
        media_urls = [visuals[platform]] if visuals.get(platform) else []

        # LinkedIn company page ID
        page_id = None
        if platform == "linkedin":
            try:
                subs = client.get_subaccounts(account_id)
                if subs:
                    page_id = subs[0].get("id")
            except Exception:
                pass

        try:
            result = client.create_post(
                account_id=account_id,
                platform=platform,
                text=posts[platform]["text"],
                media_urls=media_urls,
                schedule_time=schedule_time,
                page_id=page_id,
            )

            post_id = result.get("postSubmissionId") or result.get("id")
            if post_id:
                published = client.wait_for_publish(post_id)
                live_url = published.get("publicUrl", "")
                print(f"  {platform.upper()}: Published! {live_url}")
                log_post(youtube_url, platform, posts[platform]["text"],
                         visuals.get(platform, ""), live_url, "published")
                results[platform] = {"status": "published", "url": live_url}
            else:
                print(f"  {platform.upper()}: Submitted")
                log_post(youtube_url, platform, posts[platform]["text"],
                         visuals.get(platform, ""), "", "submitted")
                results[platform] = {"status": "submitted"}

        except Exception as e:
            print(f"  {platform.upper()}: Failed — {e}")
            log_post(youtube_url, platform, posts[platform]["text"],
                     visuals.get(platform, ""), "", f"failed — {e}")
            results[platform] = {"status": "failed", "error": str(e)}

    return results
