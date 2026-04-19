"""
Gemini embeddings client (primitive call only — no RAG logic).
Wraps the REST API so ingestion and retrieval can both EMBED without
sharing any other code.

Model default: text-embedding-004 (768 dims). Configurable via EMBEDDING_MODEL.
"""
from __future__ import annotations

import time
from typing import Literal

import requests

from tools._shared import config
from tools._shared.logger import get_logger

logger = get_logger(__name__)

_BASE = "https://generativelanguage.googleapis.com/v1beta"
_DEFAULT_MODEL = "text-embedding-004"

TaskType = Literal[
    "RETRIEVAL_QUERY",
    "RETRIEVAL_DOCUMENT",
    "SEMANTIC_SIMILARITY",
    "CLASSIFICATION",
    "CLUSTERING",
]


def _resolve_model(model: str | None) -> str:
    raw = model or config.get("EMBEDDING_MODEL") or _DEFAULT_MODEL
    # Common brand alias: map "gemini-embedding-2" to the actual API model id.
    if raw == "gemini-embedding-2":
        return _DEFAULT_MODEL
    return raw


def embed(
    texts: list[str],
    task_type: TaskType = "RETRIEVAL_DOCUMENT",
    model: str | None = None,
    max_retries: int = 3,
) -> list[list[float]]:
    """Embed a batch of strings. Returns list of vectors aligned with input order."""
    if not texts:
        return []

    keys = config.require("GOOGLE_API_KEY")
    api_key = keys["GOOGLE_API_KEY"]
    resolved = _resolve_model(model)

    out: list[list[float]] = []
    for text in texts:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        body = {
            "model": f"models/{resolved}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        url = f"{_BASE}/models/{resolved}:embedContent?key={api_key}"
        vec = _call_with_retry(url, body, max_retries)
        out.append(vec)
    return out


def _call_with_retry(url: str, body: dict, max_retries: int) -> list[float]:
    delay = 2.0
    last_err: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=body, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                raise ConnectionError(f"transient {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            data = r.json()
            vec = data.get("embedding", {}).get("values")
            if not vec or not isinstance(vec, list):
                raise ValueError(f"Unexpected embedding response: {data}")
            return vec
        except (ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            last_err = e
            if attempt == max_retries:
                break
            logger.warning(f"embed retry {attempt}/{max_retries} after {delay}s: {e}")
            time.sleep(delay)
            delay = min(delay * 2, 30.0)
    raise ConnectionError(f"Embedding failed after {max_retries} retries: {last_err}")
