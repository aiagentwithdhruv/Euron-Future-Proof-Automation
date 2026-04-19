# Atlas — RAG Product Knowledge Chatbot

> **Persona:** Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina.
> **Rule #0:** If unclear, STOP and ask Angelina.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules
2. `../learning-hub/ERRORS.md`
3. `../learning-hub/automations/CATALOG.md`
4. `../student-starter-kit/coding-rules/rules/50-rag-system.md` — RAG separation rules
5. `../Agentic Workflow for Students/shared/` — shared modules
6. `../student-starter-kit/agents/backend-builder.md` — persona
7. `../student-starter-kit/skills/guardrail-pipeline/SKILL.md`

---

## Objective (one sentence)

**Ingest product catalog + FAQ + policies → deploy one AI brain that answers questions on website AND WhatsApp with cited sources.**

---

## Agentic Loop

- **Sense:** User question (website widget OR WhatsApp message OR API call)
- **Think:** Embed query → retrieve top-k chunks → LLM reads chunks + question
- **Decide:** Can answer from sources? Or escalate to human? Or ask clarifying question?
- **Act:** Reply with answer + cited source links. OR forward to human queue.
- **Learn:** Log every Q + A + feedback (thumbs up/down) → improve retrieval + prompts

---

## Build Contract

1. RAG architecture STRICTLY separated: `ingestion/`, `retrieval/`, `generation/` (rule 50)
2. Workflows first, tools second
3. Embeddings = Gemini Embedding 2 (one model all modalities) OR OpenAI text-embedding-3-small
4. Vector DB = Supabase pgvector (free) OR Qdrant local
5. Test locally end-to-end → log
6. Deploy backend as FastAPI but DON'T deploy yet

---

## Tools to Build

### Ingestion
| Tool | Input | Output |
|------|-------|--------|
| `tools/ingestion/load_docs.py` | --path dir/ --type pdf\|md\|docx | chunks JSONL |
| `tools/ingestion/chunk_docs.py` | JSONL | chunked JSONL (semantic chunking) |
| `tools/ingestion/embed_chunks.py` | JSONL | stored in vector DB + metadata |

### Retrieval
| Tool | Input | Output |
|------|-------|--------|
| `tools/retrieval/search.py` | --query TEXT --k 5 | top-k chunks JSON |

### Generation
| Tool | Input | Output |
|------|-------|--------|
| `tools/generation/answer.py` | query, context chunks | answer + citations |

### Orchestration
| Tool | Input | Output |
|------|-------|--------|
| `tools/ask.py` | --query | full pipeline answer |
| `api/main.py` | FastAPI endpoint | `/ask`, `/feedback`, `/reingest` |
| `channels/whatsapp_webhook.py` | Webhook | same brain, WhatsApp I/O |

---

## Workflow SOPs

- `workflows/ingest-docs.md` — how to add new docs to the brain
- `workflows/answer-flow.md` — query → embed → search → generate → cite
- `workflows/reingest-schedule.md` — weekly re-ingestion for updated content

---

## APIs / Tools

| API | Free Tier | Used For |
|-----|-----------|----------|
| Euri | 200K tokens/day | LLM generation |
| Gemini | Embeddings free tier | Embeddings |
| Supabase | Free | pgvector store + DB |
| Meta WhatsApp Cloud | Free sandbox | WhatsApp channel |
| FastAPI | Free | HTTP API |

---

## Env Vars

```
EURI_API_KEY=
GOOGLE_API_KEY=                  # Gemini embeddings
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
VECTOR_TABLE=knowledge_chunks

WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=

CHUNK_SIZE=800
CHUNK_OVERLAP=100
TOP_K=5
```

---

## Rules of Engagement

- **Doubt = STOP.** Questions to Angelina:
  - "What's the knowledge source — folder of PDFs, website scrape, Google Drive, or Notion?"
  - "Which vector DB — Supabase pgvector or local Qdrant?"
  - "Embedding model — Gemini Embedding 2 or OpenAI?"
  - "WhatsApp business number ready or should I use Meta sandbox?"
- **STRICT RAG separation.** ingestion/retrieval/generation never cross. Rule 50 is non-negotiable.
- **Every answer MUST cite sources** — no cite = no send.
- **Escalate when confidence low** — threshold check before replying.

---

## Test Command

```bash
cd RAG_Knowledge_Chatbot
python tools/ingestion/load_docs.py --path ./knowledge/ --type md
python tools/ask.py --query "What's your refund policy?"
```

---

## When Done

Update catalog + ping Angelina for website widget + WhatsApp deploy.
