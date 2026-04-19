"""Input sanitization + URL/email validation."""

from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(value: str) -> str:
    v = (value or "").strip()
    if not EMAIL_RE.match(v):
        raise ValueError(f"Invalid email: {value!r}")
    return v.lower()


def safe_domain(url_or_domain: str) -> str | None:
    if not url_or_domain:
        return None
    v = url_or_domain.strip().lower()
    v = v.replace("https://", "").replace("http://", "").replace("www.", "")
    v = v.split("/")[0].split("?")[0]
    if not v or "." not in v:
        return None
    return v


def validate_url(url: str) -> str:
    if not url:
        raise ValueError("Empty URL")
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise ValueError(f"URL scheme must be http(s): {url!r}")
    if not p.netloc:
        raise ValueError(f"URL missing host: {url!r}")
    # Reject obvious internal ranges (quick guard; not exhaustive)
    host = p.netloc.split(":")[0]
    if host in ("localhost", "127.0.0.1", "0.0.0.0"):
        raise ValueError("Refusing to fetch localhost/loopback URL.")
    if host.startswith("169.254.") or host.startswith("10.") or host.startswith("192.168."):
        raise ValueError("Refusing to fetch private-network URL.")
    return url


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:max_len] or "prospect"
