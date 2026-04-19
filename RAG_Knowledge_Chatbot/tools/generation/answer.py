"""
Generation layer — answer.
Takes (query, chunks) and produces a grounded answer + citations + confidence
using the Euri LLM (OpenAI-compatible).

Rule 50: this module MUST NOT import from ingestion/ or retrieval/.
It receives chunks; it does NOT retrieve them. It emits an answer; it does NOT
re-run search. This keeps retrieval independent from answer generation.

Prompt source: prompts/answer_with_cite_v1.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests

_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from tools._shared import config  # noqa: E402
from tools._shared.logger import get_logger  # noqa: E402

logger = get_logger(__name__)

_EURI_BASE = "https://api.euron.one/api/v1/euri"
_DEFAULT_MODEL = "gpt-4o-mini"
_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "answer_with_cite_v1.md"


def _load_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt file missing: {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _format_chunks(chunks: list[dict]) -> str:
    lines: list[str] = []
    for i, c in enumerate(chunks, start=1):
        header = f"[{i}] source={c['source_id']} section={c.get('section') or '-'} chunk_id={c['chunk_id']}"
        lines.append(header)
        lines.append(c["content"].strip())
        lines.append("")
    return "\n".join(lines).strip()


def _extract_json(text: str) -> dict:
    """LLMs occasionally wrap JSON in prose. Pull the first {...} block."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", stripped)
        if not m:
            raise
        return json.loads(m.group(0))


def generate(query: str, chunks: list[dict], model: str | None = None) -> dict:
    """Generate a grounded answer. Returns {answer, citations, confidence, grounded}."""
    if not query or not query.strip():
        raise ValueError("query must be non-empty")
    if not chunks:
        # Never fabricate. Caller should have caught this via confidence gate.
        return {
            "answer": None,
            "citations": [],
            "confidence": 0.0,
            "grounded": False,
            "reason": "no_chunks_provided",
        }

    keys = config.require("EURI_API_KEY")
    system = _load_prompt()
    context = _format_chunks(chunks)
    user = (
        f"User question:\n{query}\n\n"
        f"Context chunks (numbered):\n{context}\n\n"
        f"Return ONLY the JSON object specified in the system instructions."
    )

    chosen = model or config.get("LLM_MODEL") or _DEFAULT_MODEL
    body = {
        "model": chosen,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {keys['EURI_API_KEY']}",
        "Content-Type": "application/json",
    }

    r = requests.post(
        f"{_EURI_BASE}/chat/completions",
        headers=headers,
        json=body,
        timeout=60,
    )
    if r.status_code >= 400:
        # Try without response_format in case provider doesn't support it.
        body.pop("response_format", None)
        r = requests.post(
            f"{_EURI_BASE}/chat/completions",
            headers=headers,
            json=body,
            timeout=60,
        )
    r.raise_for_status()
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    answer = (parsed.get("answer") or "").strip()
    raw_cites = parsed.get("citations") or []
    confidence = float(parsed.get("confidence") or 0.0)
    grounded = bool(parsed.get("grounded", True)) and bool(answer) and bool(raw_cites)

    # Normalize + validate citations against provided chunks.
    valid_ids = {c["chunk_id"] for c in chunks}
    by_id = {c["chunk_id"]: c for c in chunks}
    normalized: list[dict] = []
    for cite in raw_cites:
        cid = cite.get("chunk_id")
        if cid and cid in valid_ids:
            src = by_id[cid]
            normalized.append({
                "n": cite.get("n"),
                "chunk_id": cid,
                "source_id": src["source_id"],
                "source_path": src["source_path"],
                "section": src.get("section"),
            })

    if not normalized:
        # The prompt failed to cite anything verifiable → mark ungrounded.
        grounded = False

    logger.info(
        f"generated answer, cites={len(normalized)} conf={confidence:.2f} grounded={grounded}",
    )

    return {
        "answer": answer if grounded else None,
        "citations": normalized,
        "confidence": confidence,
        "grounded": grounded,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Generate grounded answer from query + chunks JSON.")
    p.add_argument("--query", required=True)
    p.add_argument("--chunks", required=True, help="Path to JSON with 'results' list (search output)")
    p.add_argument("--model", default=None)
    args = p.parse_args()

    payload = json.loads(Path(args.chunks).read_text(encoding="utf-8"))
    chunks = payload.get("results", payload) if isinstance(payload, dict) else payload
    out = generate(args.query, chunks, model=args.model)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
