"""
Ingestion layer 2/3 — chunk_docs.
Reads docs JSONL, produces chunks JSONL with deterministic sliding-window
chunking and section-heading metadata.

Rule 50: no imports from retrieval/ or generation/.

Usage:
    python tools/ingestion/chunk_docs.py \
        --in .tmp/docs.jsonl --out .tmp/chunks.jsonl \
        --chunk-size 800 --overlap 100
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def _section_index(content: str) -> list[tuple[int, str]]:
    """List of (char_offset, heading_text) in order of appearance."""
    sections: list[tuple[int, str]] = []
    offset = 0
    for line in content.splitlines(keepends=True):
        m = _HEADING.match(line.strip())
        if m:
            sections.append((offset, m.group(2).strip()))
        offset += len(line)
    return sections


def _section_for_offset(sections: list[tuple[int, str]], pos: int) -> str | None:
    """Return the most recent heading at or before `pos`."""
    current: str | None = None
    for off, heading in sections:
        if off <= pos:
            current = heading
        else:
            break
    return current


def _chunk_text(content: str, size: int, overlap: int) -> list[tuple[int, str]]:
    """Return [(start_offset, text), ...]. Char-based sliding window."""
    if size <= 0:
        raise ValueError("chunk size must be > 0")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must satisfy 0 <= overlap < size")

    if not content:
        return []

    out: list[tuple[int, str]] = []
    step = size - overlap
    pos = 0
    n = len(content)
    while pos < n:
        end = min(pos + size, n)
        # Prefer breaking at the nearest sentence/paragraph boundary within the
        # last 20% of the window to keep chunks semantically clean.
        if end < n:
            window = content[pos:end]
            cut = _best_break(window, int(size * 0.8))
            if cut > 0:
                end = pos + cut
        text = content[pos:end].strip()
        if text:
            out.append((pos, text))
        if end >= n:
            break
        pos = max(pos + step, end - overlap)
    return out


def _best_break(window: str, min_keep: int) -> int:
    """Find last paragraph/sentence boundary after min_keep chars. Returns 0 if none."""
    for sep in ("\n\n", ". ", "? ", "! ", "\n"):
        idx = window.rfind(sep, min_keep)
        if idx != -1:
            return idx + len(sep)
    return 0


def chunk_docs(docs: list[dict], size: int, overlap: int) -> list[dict]:
    chunks: list[dict] = []
    for doc in docs:
        content = doc.get("content", "")
        sections = _section_index(content)
        pieces = _chunk_text(content, size, overlap)
        for i, (pos, text) in enumerate(pieces):
            chunks.append({
                "chunk_id": f"{doc['source_id']}::{i:04d}",
                "source_id": doc["source_id"],
                "source_path": doc["source_path"],
                "section": _section_for_offset(sections, pos),
                "chunk_index": i,
                "content": text,
                "token_estimate": max(1, len(text) // 4),
                "metadata": {
                    "title": doc.get("title"),
                    "type": doc.get("type"),
                    "updated_at": doc.get("updated_at"),
                    "char_offset": pos,
                },
            })
    return chunks


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Input not found: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Chunk docs JSONL into chunks JSONL.")
    p.add_argument("--in", dest="inp", default=".tmp/docs.jsonl")
    p.add_argument("--out", default=".tmp/chunks.jsonl")
    p.add_argument("--chunk-size", type=int, default=config.get_int("CHUNK_SIZE", 800))
    p.add_argument("--overlap", type=int, default=config.get_int("CHUNK_OVERLAP", 100))
    args = p.parse_args()

    inp = Path(args.inp)
    out = Path(args.out)
    if not inp.is_absolute():
        inp = _PROJECT_ROOT / inp
    if not out.is_absolute():
        out = _PROJECT_ROOT / out

    docs = _read_jsonl(inp)
    chunks = chunk_docs(docs, args.chunk_size, args.overlap)
    _write_jsonl(chunks, out)

    result = {
        "status": "ok",
        "docs_in": len(docs),
        "chunks_out": len(chunks),
        "chunk_size": args.chunk_size,
        "overlap": args.overlap,
        "output": str(out.relative_to(_PROJECT_ROOT)),
    }
    print(json.dumps(result, indent=2))
    logger.info(f"chunked {len(docs)} docs -> {len(chunks)} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
