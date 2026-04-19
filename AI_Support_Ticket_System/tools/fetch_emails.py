"""Fetch new emails from IMAP OR load from a fixture file (for testing).

Usage:
    python tools/fetch_emails.py --since 15 --output .tmp/new_emails.json
    python tools/fetch_emails.py --fixtures .tmp/fake_emails.json --output .tmp/new_emails.json

IMAP mode requires IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASS in .env.
IMAP_PASS MUST be a Gmail App Password — never the real Google password.
"""

import argparse
import email
import imaplib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.env_loader import load_env, get_required, get_optional
from shared.logger import info, error, warn
from shared.sandbox import validate_write_path


def _decode(value) -> str:
    """Decode RFC 2047 encoded header values into plain UTF-8."""
    if value is None:
        return ""
    parts = []
    for chunk, enc in decode_header(value):
        if isinstance(chunk, bytes):
            try:
                parts.append(chunk.decode(enc or "utf-8", errors="replace"))
            except LookupError:
                parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return "".join(parts).strip()


def _extract_sender_email(from_header: str) -> str:
    """Pull the raw email address out of a From: header."""
    match = re.search(r"<([^>]+)>", from_header or "")
    if match:
        return match.group(1).strip().lower()
    return (from_header or "").strip().lower()


def _extract_sender_name(from_header: str) -> str:
    """Pull the display name out of a From: header, or fall back to local-part."""
    from_header = from_header or ""
    match = re.match(r'^\s*"?([^"<]+?)"?\s*<', from_header)
    if match:
        return match.group(1).strip()
    addr = _extract_sender_email(from_header)
    return addr.split("@")[0] if "@" in addr else addr


def _extract_plain_body(msg) -> str:
    """Walk a multipart email and extract the plaintext body."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        return payload.decode(charset, errors="replace").strip()
                    except LookupError:
                        return payload.decode("utf-8", errors="replace").strip()
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        charset = msg.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace").strip()
        except LookupError:
            return payload.decode("utf-8", errors="replace").strip()
    return str(msg.get_payload() or "")


def load_from_fixtures(fixtures_path: str) -> list:
    """Load pre-formatted fake emails for dry-run testing."""
    path = Path(fixtures_path)
    if not path.exists():
        error(f"Fixture file not found: {fixtures_path}")
        sys.exit(1)

    data = json.loads(path.read_text())
    if not isinstance(data, list):
        error("Fixture must be a JSON array of email objects")
        sys.exit(1)

    required = {"id", "from", "subject", "body"}
    for i, m in enumerate(data):
        missing = required - set(m.keys())
        if missing:
            error(f"Fixture entry {i} missing fields: {missing}")
            sys.exit(1)
        m.setdefault("received_at", datetime.now(timezone.utc).isoformat())
        # Normalise sender fields
        m["from_email"] = _extract_sender_email(m["from"])
        m["from_name"] = _extract_sender_name(m["from"])

    info(f"Loaded {len(data)} fixture emails from {fixtures_path}")
    return data


def fetch_from_imap(since_minutes: int) -> list:
    """Connect to IMAP and fetch emails newer than since_minutes."""
    host = get_required("IMAP_HOST")
    port = int(get_optional("IMAP_PORT", "993"))
    user = get_required("IMAP_USER")
    password = get_required("IMAP_PASS")
    mailbox = get_optional("IMAP_MAILBOX", "INBOX")

    info(f"Connecting to IMAP {host}:{port} as {user}")
    try:
        conn = imaplib.IMAP4_SSL(host, port)
        conn.login(user, password)
    except imaplib.IMAP4.error as e:
        error(f"IMAP auth failed: {e}. Check IMAP_PASS — must be a Gmail App Password.")
        sys.exit(2)
    except Exception as e:
        error(f"IMAP connection failed: {e}")
        sys.exit(2)

    try:
        conn.select(mailbox)
        since_date = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).strftime("%d-%b-%Y")
        status, data = conn.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            error(f"IMAP SEARCH failed: {status}")
            return []

        ids = data[0].split()
        info(f"Found {len(ids)} messages since {since_date}")

        emails = []
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=since_minutes)
        for msg_id in ids[-200:]:  # hard cap at 200 per poll
            status, fetched = conn.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue
            raw = fetched[0][1]
            msg = email.message_from_bytes(raw)

            date_str = msg.get("Date", "")
            try:
                received_at = email.utils.parsedate_to_datetime(date_str)
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)
                if received_at < cutoff:
                    continue
            except Exception:
                received_at = datetime.now(timezone.utc)

            from_header = _decode(msg.get("From"))
            emails.append({
                "id": msg.get("Message-ID") or f"imap-{msg_id.decode()}",
                "from": from_header,
                "from_email": _extract_sender_email(from_header),
                "from_name": _extract_sender_name(from_header),
                "subject": _decode(msg.get("Subject")),
                "body": _extract_plain_body(msg),
                "received_at": received_at.isoformat(),
                "in_reply_to": msg.get("In-Reply-To") or "",
                "references": msg.get("References") or "",
            })

        conn.close()
        conn.logout()
        info(f"Fetched {len(emails)} emails within window")
        return emails
    except Exception as e:
        error(f"IMAP fetch failed: {e}")
        try:
            conn.logout()
        except Exception:
            pass
        return []


def main():
    parser = argparse.ArgumentParser(description="Fetch new support emails")
    parser.add_argument("--since", type=int, default=15, help="Look back this many minutes (IMAP mode)")
    parser.add_argument("--fixtures", help="Path to fake emails JSON (dry-run mode)")
    parser.add_argument("--output", default=".tmp/new_emails.json", help="Where to write fetched emails")
    args = parser.parse_args()

    # env only needed for IMAP mode
    if not args.fixtures:
        load_env()

    if args.fixtures:
        emails = load_from_fixtures(args.fixtures)
    else:
        emails = fetch_from_imap(args.since)

    out_path = validate_write_path(str(Path(__file__).parent.parent / args.output))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(emails, indent=2, ensure_ascii=False))

    print(json.dumps({"status": "success", "output_path": str(out_path), "count": len(emails)}))


if __name__ == "__main__":
    main()
