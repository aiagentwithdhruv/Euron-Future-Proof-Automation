"""Format ranked news articles into a Telegram-ready message.

Usage:
    python tools/format_message.py --input .tmp/ranked_news.json
    python tools/format_message.py --input .tmp/ranked_news.json --format plain

Output:
    Writes formatted message to .tmp/telegram_message.txt
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logger import info
from shared.sandbox import validate_write_path


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special_chars = r'_*[]()~`>#+-=|{}.!'
    escaped = ""
    for char in text:
        if char in special_chars:
            escaped += f"\\{char}"
        else:
            escaped += char
    return escaped


def format_markdown_v2(articles: list) -> str:
    """Format articles as Telegram MarkdownV2 message."""
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    lines = [f"*{escape_markdown_v2('AI News Digest')}* {escape_markdown_v2('—')} {escape_markdown_v2(today)}\n"]

    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        summary = article.get("summary", article.get("description", ""))[:200]
        url = article.get("url", "")
        source = article.get("source", "Unknown")

        lines.append(f"*{i}\\.*  [{escape_markdown_v2(title)}]({url})")
        lines.append(f"_{escape_markdown_v2(source)}_")
        if summary:
            lines.append(escape_markdown_v2(summary))
        lines.append("")

    lines.append(escape_markdown_v2("— Powered by AI News Bot"))
    return "\n".join(lines)


def format_plain(articles: list) -> str:
    """Format articles as plain text (no markdown)."""
    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    lines = [f"AI News Digest — {today}\n"]

    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        summary = article.get("summary", article.get("description", ""))[:200]
        url = article.get("url", "")
        source = article.get("source", "Unknown")

        lines.append(f"{i}. {title}")
        lines.append(f"   {source}")
        if summary:
            lines.append(f"   {summary}")
        if url:
            lines.append(f"   {url}")
        lines.append("")

    lines.append("— Powered by AI News Bot")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Format news for Telegram")
    parser.add_argument("--input", default=".tmp/ranked_news.json", help="Input JSON file")
    parser.add_argument("--output", default=".tmp/telegram_message.txt", help="Output file")
    parser.add_argument("--format", choices=["markdown", "plain"], default="markdown", help="Message format")
    args = parser.parse_args()

    input_path = Path(__file__).parent.parent / args.input
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    articles = json.loads(input_path.read_text())
    info(f"Formatting {len(articles)} articles as {args.format}")

    if args.format == "markdown":
        message = format_markdown_v2(articles)
    else:
        message = format_plain(articles)

    output_path = validate_write_path(str(Path(__file__).parent.parent / args.output))
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(message)
    print(json.dumps({"status": "success", "output_path": str(output_path), "length": len(message)}))


if __name__ == "__main__":
    main()
