# RAG_Knowledge_Chatbot — Prompts

---

## Prompts

| Name | File | Purpose | Variables | Category | Used By |
|------|------|---------|-----------|----------|---------|
| `answer_with_cite_v1` | `prompts/answer_with_cite_v1.md` | Generate grounded answer + citations from retrieved chunks | `{query}`, `{chunks}` | generation | `tools/generation/answer.py` |
| `clarify_question` | `prompts/clarify_question.md` | Ask one short clarifying question when the query is ambiguous | `{query}`, `{topics}` | clarification | (future) escalation handler |
| `chunk_summary` | `prompts/chunk_summary.md` | One-line semantic summary of an ingested chunk | `{chunk_text}`, `{title}`, `{section}` | ingestion | (optional) ingestion pass |

---

## Status

All three prompts **written + wired**. `answer_with_cite_v1` is the only one
live on the critical path today; the other two are staged for the next
escalation/UX pass.

**Last Updated:** 2026-04-19 — built by Atlas.
