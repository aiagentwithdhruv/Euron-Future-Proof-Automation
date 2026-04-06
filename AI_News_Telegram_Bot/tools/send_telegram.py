"""Send a formatted message to Telegram via Bot API.

Usage:
    python tools/send_telegram.py --input .tmp/telegram_message.txt
    python tools/send_telegram.py --input .tmp/telegram_message.txt --parse-mode plain
    python tools/send_telegram.py --message "Hello from AI News Bot"

Output:
    Sends message to configured Telegram chat. Prints result JSON.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from shared.env_loader import load_env, get_required
from shared.logger import info, error
from shared.retry import with_retry


@with_retry(max_attempts=3, base_delay=2.0)
def send_message(bot_token: str, chat_id: str, text: str, parse_mode: str = "MarkdownV2") -> dict:
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": False,
    }
    if parse_mode != "plain":
        payload["parse_mode"] = parse_mode

    resp = requests.post(url, json=payload, timeout=15)

    if resp.status_code == 400 and "can't parse entities" in resp.text.lower():
        info("MarkdownV2 parse failed — retrying as plain text")
        payload.pop("parse_mode", None)
        resp = requests.post(url, json=payload, timeout=15)

    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Send message to Telegram")
    parser.add_argument("--input", help="File containing the message text")
    parser.add_argument("--message", help="Direct message text (alternative to --input)")
    parser.add_argument("--parse-mode", default="MarkdownV2", choices=["MarkdownV2", "HTML", "plain"],
                        help="Telegram parse mode")
    args = parser.parse_args()

    load_env()
    bot_token = get_required("TELEGRAM_BOT_TOKEN")
    chat_id = get_required("TELEGRAM_CHAT_ID")

    if args.input:
        input_path = Path(__file__).parent.parent / args.input
        if not input_path.exists():
            error(f"Input file not found: {input_path}")
            sys.exit(1)
        text = input_path.read_text()
    elif args.message:
        text = args.message
    else:
        error("Provide --input or --message")
        sys.exit(1)

    if len(text) > 4096:
        info(f"Message too long ({len(text)} chars) — truncating to 4096")
        text = text[:4090] + "\n\\.\\.\\."

    info(f"Sending message to Telegram chat {chat_id} ({len(text)} chars)")
    result = send_message(bot_token, chat_id, text, args.parse_mode)

    if result.get("ok"):
        info("Message sent successfully")
        print(json.dumps({"status": "success", "message_id": result["result"]["message_id"]}))
    else:
        error(f"Telegram API error: {result}")
        print(json.dumps({"status": "error", "details": result}))
        sys.exit(1)


if __name__ == "__main__":
    main()
