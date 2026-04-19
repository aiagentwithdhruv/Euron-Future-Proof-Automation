"""
Ingestion layer 3/3 — embed_chunks.
Reads chunks JSONL, embeds via Gemini, upserts into Supabase pgvector.

Rule 50: no imports from retrieval/ or generation/.
Re-embedding is idempotent via chunk_id on_conflict.

Usage:
    python tools/ingestion/embed_chunks.py --in .tmp/chunks.jsonl --batch 20
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.embeddings import embed  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402
from tools._shared.supabase_client import upsert  # noqa: E402

logger = get_logger(__name__)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def embed_and_store(chunks: list[dict], batch: int) -> dict:
    table = config.get("VECTOR_TABLE", "knowledge_chunks")
    total = len(chunks)
    stored = 0
    for i in range(0, total, batch):
        group = chunks[i:i + batch]
        texts = [c["content"] for c in group]
        vectors = embed(texts, task_type="RETRIEVAL_DOCUMENT")

        rows = []
        for c, vec in zip(group, vectors):
            rows.append({
                "chunk_id": c["chunk_id"],
                "source_id": c["source_id"],
                "source_path": c["source_path"],
                "section": c.get("section"),
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "token_estimate": c.get("token_estimate"),
                "metadata": c.get("metadata", {}),
                "embedding": vec,
            })
        upsert(table, rows, on_conflict="chunk_id")
        stored += len(rows)
        logger.info(
            f"embedded+stored batch {i // batch + 1}: {stored}/{total}",
            extra={"count": stored},
        )

    return {"stored": stored, "total": total, "table": table}


def main() -> int:
    p = argparse.ArgumentParser(description="Embed chunks and upsert into Supabase.")
    p.add_argument("--in", dest="inp", default=".tmp/chunks.jsonl")
    p.add_argument("--batch", type=int, default=20)
    args = p.parse_args()

    inp = Path(args.inp)
    if not inp.is_absolute():
        inp = _PROJECT_ROOT / inp
    if not inp.exists():
        raise FileNotFoundError(f"Input not found: {inp}. Run chunk_docs.py first.")

    chunks = _read_jsonl(inp)
    if not chunks:
        print(json.dumps({"status": "ok", "stored": 0, "total": 0}, indent=2))
        return 0

    result = embed_and_store(chunks, args.batch)
    print(json.dumps({"status": "ok", **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
