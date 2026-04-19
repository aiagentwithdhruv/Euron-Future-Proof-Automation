"""
Ingestion layer 1/3 — load_docs.
Walks a directory, reads files, writes docs JSONL.

Rule 50: this module MUST NOT import from retrieval/ or generation/.

Usage:
    python tools/ingestion/load_docs.py --path ./knowledge --type md \
        --out .tmp/docs.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is importable when run as a script.
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

_SUPPORTED = {"md", "txt", "pdf"}


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or f"doc-{int(time.time())}"


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "PDF ingestion requires `pypdf`. Install with `pip install pypdf` "
            "or ingest .md/.txt instead."
        ) from e
    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _normalize(text: str) -> str:
    # Strip BOM, collapse Windows line endings, trim trailing whitespace per line.
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    # Collapse runs of 3+ blank lines to 2.
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln.strip():
            blank = 0
            out.append(ln)
        else:
            blank += 1
            if blank <= 2:
                out.append("")
    return "\n".join(out).strip()


def _derive_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s.lstrip("# ").strip()
        if s and not s.startswith("#"):
            return s[:120]
    return fallback


def _iter_files(root: Path, ext: str) -> list[Path]:
    if ext == "all":
        return sorted(
            p for p in root.rglob("*")
            if p.is_file() and p.suffix.lower().lstrip(".") in _SUPPORTED
        )
    return sorted(root.rglob(f"*.{ext}"))


def load_dir(path: Path, doc_type: str) -> list[dict]:
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Knowledge path not found or not a dir: {path}")

    docs: list[dict] = []
    for fp in _iter_files(path, doc_type):
        ext = fp.suffix.lower().lstrip(".")
        try:
            raw = _read_pdf(fp) if ext == "pdf" else _read_text(fp)
        except Exception as e:
            logger.error(f"skip {fp.name}: {e}")
            continue

        content = _normalize(raw)
        if not content:
            logger.warning(f"empty after normalize: {fp.name}")
            continue

        rel = fp.relative_to(path)
        source_id = _slugify(str(rel.with_suffix("")))
        stat = fp.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

        docs.append({
            "source_id": source_id,
            "source_path": str(rel),
            "title": _derive_title(content, fp.stem),
            "type": ext,
            "content": content,
            "byte_size": stat.st_size,
            "updated_at": updated_at,
        })
    return docs


def _write_jsonl(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    p = argparse.ArgumentParser(description="Load docs from a directory into JSONL.")
    p.add_argument("--path", required=True, help="Directory with docs")
    p.add_argument("--type", default="md", choices=sorted(_SUPPORTED | {"all"}))
    p.add_argument("--out", default=".tmp/docs.jsonl", help="Output JSONL path")
    args = p.parse_args()

    root = Path(args.path).resolve()
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _PROJECT_ROOT / out_path

    docs = load_dir(root, args.type)
    _write_jsonl(docs, out_path)

    result = {
        "status": "ok",
        "docs_loaded": len(docs),
        "output": str(out_path.relative_to(_PROJECT_ROOT)),
        "sources": [d["source_id"] for d in docs],
    }
    print(json.dumps(result, indent=2))
    logger.info(f"loaded {len(docs)} docs -> {out_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
