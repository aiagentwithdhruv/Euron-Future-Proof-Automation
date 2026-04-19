# RAG Product Knowledge Chatbot

> One AI brain. Knows your catalog + FAQ + policies. Answers on website + WhatsApp with citations.
> Built with **strict rule-50 separation**: ingestion / retrieval / generation are three
> standalone layers; only `tools/ask.py` composes them.

---

## What It Does

Ingests your business docs (markdown, text, PDFs) into Supabase pgvector. When a user
asks a question on your website or WhatsApp:

1. Query is embedded (Gemini)
2. Top-k similar chunks are retrieved (pgvector cosine)
3. **Confidence gate** — below 0.6, escalate to a human
4. LLM (Euri) generates a grounded answer **with citations**
5. **Citation gate** — if the LLM returns zero valid citations, escalate anyway
6. Reply with answer + source list, or hand-off message

## Agentic Loop

- **Sense:** User query (web widget / WhatsApp / API)
- **Think:** Embed → retrieve top-k
- **Decide:** confidence gate → citation gate
- **Act:** Reply with cited answer OR escalate
- **Learn:** `/feedback` verdicts logged to Supabase

## Architecture (rule 50)

```
ingestion/         retrieval/         generation/
load_docs      →   (none)        →    (none)
chunk_docs         search             answer
embed_chunks   ↘          ↓               ↓
                      tools/ask.py (orchestrator)
                              ↓
                     api/main.py  +  channels/whatsapp_webhook.py
```

`ingestion/`, `retrieval/`, `generation/` never import each other. Verified by
the AST audit in `runs/2026-04-19-build-and-dry-test.md`.

## Setup

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
#    fill: GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, EURI_API_KEY,
#          WHATSAPP_* (if using WhatsApp channel), API_KEY (optional endpoint guard)

# 3. Apply DB schema once
#    Open Supabase → SQL Editor → paste contents of db/supabase_schema.sql → Run

# 4. Ingest knowledge
python tools/ingestion/load_docs.py   --path ./knowledge --type md
python tools/ingestion/chunk_docs.py
python tools/ingestion/embed_chunks.py
```

## Run

```bash
# Ask via CLI
python tools/ask.py --query "What's your refund policy?"

# Serve API (web widget + WhatsApp webhook)
uvicorn api.main:app --reload --port 8000
```

### Endpoints

| Method | Path | Body | Purpose |
|--------|------|------|---------|
| GET | `/health` | – | liveness |
| POST | `/ask` | `{query, k?, channel?}` | grounded answer or escalation |
| POST | `/feedback` | `{query, verdict, ...}` | log `up` / `down` / `escalated` |
| POST | `/reingest` | `{path, type?}` | run the 3-stage ingestion |
| GET/POST | `/whatsapp` | Meta webhook | WhatsApp verify + inbound |

## Deploy (LIVE) ✅

Deployed to **n8n** (`n8n.aiwithdhruv.cloud`) as a public chat widget. No FastAPI / Koyeb needed — the entire RAG pipeline runs as an n8n workflow.

**Public chat URL:** `https://n8n.aiwithdhruv.cloud/webhook/aiwithdhruv-chat/chat`

**Workflow:** `AIwithDhruv RAG Chatbot` (ID `ujZtAayfgpduXZhc`)

**Pipeline inside n8n:**
```
Chat Trigger (public)
    → Extract Query (Code)
    → Embed via Gemini (HTTP Request)
    → Search Supabase pgvector (HTTP Request → match_chunks RPC)
    → Build Context + gate (Code; escalates if similarity < 0.4 or no hits)
    → Answer via Euri (HTTP Request → gpt-4o-mini)
    → Format Response (Code; enforces citation line)
```

To update the bot's knowledge: edit `knowledge/aiwithdhruv-master.md`, then re-run the chunk+embed+push script. Details in `runs/2026-04-19-build-and-dry-test.md`.

See root `DEPLOY.md` for the two deployment paths used across the bootcamp.

---

**Phase:** 4
**Status:** ✅ Deployed to n8n — live public chat widget
**Owner:** Atlas (build) → Angelina (deploy, 2026-04-19)
