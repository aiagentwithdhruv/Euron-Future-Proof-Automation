# Run Log — Build + Dry Test

**Date:** 2026-04-19
**Owner:** Atlas
**Phase:** 4
**Session:** initial build, local verification

---

## What Was Built

RAG Product-Knowledge Chatbot with **strict ingestion/retrieval/generation separation** (rule 50).

### File tree

```
RAG_Knowledge_Chatbot/
├── api/main.py                          # FastAPI /ask /feedback /reingest /health
├── channels/whatsapp_webhook.py         # Meta WhatsApp Cloud webhook (same brain)
├── db/supabase_schema.sql               # pgvector table + match_chunks RPC + feedback_events
├── knowledge/
│   ├── refund-policy.md
│   ├── shipping-faq.md
│   └── product-catalog.md
├── prompts/
│   ├── answer_with_cite_v1.md
│   ├── clarify_question.md
│   └── chunk_summary.md
├── tools/
│   ├── _shared/                         # primitives only (not RAG logic)
│   │   ├── config.py                    # env loader
│   │   ├── logger.py                    # JSON logs + secret masking
│   │   ├── embeddings.py                # Gemini embedContent wrapper
│   │   └── supabase_client.py           # REST upsert / rpc / insert
│   ├── ingestion/                       # Layer 1
│   │   ├── load_docs.py
│   │   ├── chunk_docs.py
│   │   └── embed_chunks.py
│   ├── retrieval/                       # Layer 2
│   │   └── search.py
│   ├── generation/                      # Layer 3
│   │   └── answer.py
│   └── ask.py                           # orchestrator (only cross-layer caller)
├── workflows/
│   ├── ingest-docs.md
│   ├── answer-flow.md
│   └── reingest-schedule.md
├── requirements.txt
└── .env.example
```

---

## Dry Test Results (no external APIs)

Ran the two ingestion stages that need no credentials to confirm the pipeline
shape, chunking logic, and metadata preservation.

### Stage 1 — `load_docs.py`
```bash
python3 tools/ingestion/load_docs.py --path ./knowledge --type md --out .tmp/docs.jsonl
```
Output:
```json
{ "status": "ok", "docs_loaded": 3, "output": ".tmp/docs.jsonl",
  "sources": ["product-catalog", "refund-policy", "shipping-faq"] }
```

### Stage 2 — `chunk_docs.py`
```bash
python3 tools/ingestion/chunk_docs.py --chunk-size 800 --overlap 100
```
Output:
```json
{ "status": "ok", "docs_in": 3, "chunks_out": 6,
  "chunk_size": 800, "overlap": 100, "output": ".tmp/chunks.jsonl" }
```

Resulting chunks (section extraction working):

| chunk_id | section | source |
|----------|---------|--------|
| product-catalog::0000 | Product Catalog (Sample) | product-catalog |
| product-catalog::0001 | Leather Chelsea Boot — SKU BOOT-007 | product-catalog |
| refund-policy::0000 | Refund Policy | refund-policy |
| refund-policy::0001 | Exclusions | refund-policy |
| shipping-faq::0000 | Shipping FAQ | shipping-faq |
| shipping-faq::0001 | Address Changes | shipping-faq |

Every chunk carries: `chunk_id`, `source_id`, `source_path`, `section`,
`chunk_index`, `content`, `token_estimate`, `metadata.title`,
`metadata.type`, `metadata.updated_at`, `metadata.char_offset`.

### Rule 50 audit (scripted AST scan)

```
RULE 50 AUDIT: PASS — no cross-layer imports between ingestion/retrieval/generation.
ORCHESTRATOR AUDIT: PASS — tools/ask.py imports retrieval + generation (expected).
```

### Byte-code compile

```
python3 -m compileall -q tools api channels   →   clean
```

---

## Full End-to-End Test (requires creds — NOT run here)

These need `GOOGLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`,
`EURI_API_KEY` in `.env`, and `db/supabase_schema.sql` applied once in the
Supabase SQL editor.

```bash
# 1. Apply schema once
#    Paste db/supabase_schema.sql in Supabase → SQL Editor → Run

# 2. Install deps
pip install -r requirements.txt

# 3. Ingest
python3 tools/ingestion/load_docs.py   --path ./knowledge --type md
python3 tools/ingestion/chunk_docs.py
python3 tools/ingestion/embed_chunks.py

# 4. Query (expect answered w/ citations)
python3 tools/ask.py --query "What's your refund policy?"

# 5. Query (expect escalated)
python3 tools/ask.py --query "Who won the 2023 Cricket World Cup?"

# 6. Serve API
uvicorn api.main:app --reload --port 8000
curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -H "x-api-key: $API_KEY" \
     -d '{"query":"Refund window?"}'
```

---

## Handoff

- **Status:** built, dry-tested on ingestion stages 1 + 2, static audit of rule 50 passes.
- **Blockers for full E2E:** none code-wise — needs Supabase project + Gemini key + Euri key.
- **Not deployed** — per brief, build only. Ping Angelina for deploy dispatch.

## Notes for Next Session

- Embedding model aliased: `EMBEDDING_MODEL=gemini-embedding-2` is mapped to
  the real API id `text-embedding-004` (768 dims) inside `_shared/embeddings.py`.
  If a future Gemini "Embedding 2" ships with different dims, update
  `db/supabase_schema.sql` (vector(768) → vector(N)) and the alias.
- `CONFIDENCE_THRESHOLD=0.6` is the escalation trigger. Tune after 100+ real queries.
- Citation gate: generator returns zero valid citations → always escalate. No silent
  un-cited replies.
