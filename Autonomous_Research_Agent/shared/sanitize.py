"""Input + output sanitization — shell safety, URL safety, PII stripping."""

import re


_PII_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PII_PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,5}(?!\d)")
# Conservative SSN-ish pattern (only US 3-2-4) — keep narrow to avoid false positives.
_PII_SSN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")


def sanitize_text(text: str) -> str:
    """Strip shell metacharacters + control characters."""
    cleaned = re.sub(r"[;&|`$(){}]", "", text)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    return cleaned.strip()


def sanitize_url(url: str) -> str:
    """Only allow http/https. Block internal/private IPs."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL scheme: {url}")
    blocked = ["127.0.0.1", "localhost", "0.0.0.0", "169.254.", "10.", "192.168."]
    for pattern in blocked:
        if pattern in url:
            raise ValueError(f"Blocked internal URL: {url}")
    return url


def strip_pii(text: str) -> str:
    """Redact emails, phone numbers, and SSN-like strings from scraped content.

    Project rule (CLAUDE.md): Never store PII from scraped content.
    This is a defense-in-depth scrub — run before writing to snapshots or logs.
    """
    if not text:
        return text
    text = _PII_EMAIL.sub("[email]", text)
    text = _PII_SSN.sub("[ssn]", text)
    text = _PII_PHONE.sub("[phone]", text)
    return text
