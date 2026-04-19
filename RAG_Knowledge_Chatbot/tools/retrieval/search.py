"""
Retrieval layer — search.
Embed a query → cosine-similarity lookup via Supabase pgvector RPC.

Rule 50: this module MUST NOT import from generation/. Retrieval is independent
of answer generation. The only cross-layer primitives it uses are shared helpers
(embedding call + db client) — never ingestion or generation logic.

Usage (CLI):
    python tools/retrieval/search.py --query "refund policy" --k 5
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
from tools._shared.supabase_client import rpc  # noqa: E402

logger = get_logger(__name__)


def search(query: str, k: int = 5, source_filter: str | None = None) -> dict:
    """Return top-k chunks with cosine similarity. Raises on empty query."""
    q = (query or "").strip()
    if not q:
        raise ValueError("query must be a non-empty string")

    query_vec = embed([q], task_type="RETRIEVAL_QUERY")[0]
    rows = rpc(
        "match_chunks",
        {
            "query_embedding": query_vec,
            "match_count": k,
            "source_filter": source_filter,
        },
    ) or []

    results = [
        {
            "chunk_id": r["chunk_id"],
            "source_id": r["source_id"],
            "source_path": r["source_path"],
            "section": r.get("section"),
            "chunk_index": r["chunk_index"],
            "content": r["content"],
            "metadata": r.get("metadata") or {},
            "similarity": float(r.get("similarity") or 0.0),
        }
        for r in rows
    ]
    top_score = results[0]["similarity"] if results else 0.0
    logger.info(
        f"retrieved {len(results)} chunks, top={top_score:.3f}",
        extra={"count": len(results)},
    )
    return {
        "query": q,
        "k": k,
        "top_similarity": top_score,
        "results": results,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Retrieve top-k chunks for a query.")
    p.add_argument("--query", required=True)
    p.add_argument("--k", type=int, default=config.get_int("TOP_K", 5))
    p.add_argument("--source", default=None, help="Optional source_id filter")
    args = p.parse_args()

    out = search(args.query, k=args.k, source_filter=args.source)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
