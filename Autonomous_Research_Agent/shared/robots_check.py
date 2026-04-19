"""robots.txt check + per-domain rate limiter.

Project rules (CLAUDE.md + ATLAS-PROMPT.md):
- Respect robots.txt — skip disallowed URLs.
- Rate-limit 3 seconds between requests to the same domain.
"""

import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from shared.logger import info, warn

USER_AGENT = "Angelina-OS-Research-Agent/1.0 (+https://aiwithdhruv.com)"

_robots_cache: dict[str, RobotFileParser] = {}
_last_request_at: dict[str, float] = {}


def _get_robot_parser(base: str) -> RobotFileParser | None:
    if base in _robots_cache:
        return _robots_cache[base]
    parser = RobotFileParser()
    robots_url = f"{base}/robots.txt"
    try:
        parser.set_url(robots_url)
        parser.read()
        _robots_cache[base] = parser
        info(f"robots.txt fetched: {robots_url}")
        return parser
    except Exception as e:
        warn(f"robots.txt fetch failed for {robots_url} — assuming allow", error=str(e))
        _robots_cache[base] = None  # type: ignore
        return None


def is_allowed(url: str) -> bool:
    """Return True if robots.txt allows our User-Agent to fetch this URL."""
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parser = _get_robot_parser(base)
    if parser is None:
        return True
    allowed = parser.can_fetch(USER_AGENT, url)
    if not allowed:
        warn(f"robots.txt DISALLOW: {url}")
    return allowed


def wait_for_rate_limit(url: str, min_interval_sec: float = 3.0):
    """Ensure at least `min_interval_sec` has passed since the last request to this domain."""
    parsed = urlparse(url)
    domain = parsed.netloc
    now = time.monotonic()
    last = _last_request_at.get(domain, 0.0)
    delta = now - last
    if delta < min_interval_sec and last > 0:
        wait = min_interval_sec - delta
        info(f"rate-limit: sleeping {wait:.2f}s before hitting {domain}")
        time.sleep(wait)
    _last_request_at[domain] = time.monotonic()


def safe_headers() -> dict:
    """Default headers for polite scraping."""
    return {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
