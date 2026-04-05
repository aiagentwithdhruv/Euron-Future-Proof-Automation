# Improvement Log — What We Learned

> Patterns confirmed, techniques validated, insights worth keeping.
> Not just errors — this captures what WORKED and why.

---

## How to Log

```
### [DATE] — [SHORT TITLE]
**What:** What was discovered or confirmed
**Context:** Where/when this happened
**Pattern:** The reusable insight
**Applies to:** [project/everyone/specific-phase]
```

---

## Architecture & Design

### 2026-04-05 — 3-Layer separation preserves accuracy
**What:** Separating AI reasoning from deterministic execution keeps accuracy at 90% instead of compounding to 59% over 5 steps
**Context:** Core bootcamp architecture principle
**Pattern:** Agent reasons -> Workflows instruct -> Tools execute. Never let the agent do execution inline.
**Applies to:** Everyone — every automation must follow this

### 2026-04-05 — Agentic Loop as universal test
**What:** Every automation can be validated against Sense -> Think -> Decide -> Act -> Learn
**Context:** Core mental model across all 8 phases
**Pattern:** If your automation can't answer "what does it sense?" and "how does it learn?", it's incomplete
**Applies to:** Everyone

---

## Deployment

### 2026-04-05 — Free tier stack for students
**What:** Railway + Vercel + GitHub Actions + Supabase gives $0/month for most automations
**Context:** Students shouldn't invest money before proving value
**Pattern:** Start free, move to VPS ($3-4/mo) when you need 24/7 uptime or self-hosted n8n
**Applies to:** Phase 5, all deployment decisions

---

## API Integration

### 2026-04-05 — Euri API as primary LLM gateway
**What:** Euri (euron.one) provides 200K free tokens/day with OpenAI-compatible SDK
**Context:** Students can use GPT-4o models for free, just swap base_url
**Pattern:** Always try Euri first -> OpenRouter second -> Direct API keys last
**Applies to:** Everyone — all LLM calls

---

## Tools & Automation

_(New entries will be added as patterns are discovered)_

---

## Teaching & Students

_(New entries will be added from class sessions)_

---

## Stats

| Metric | Count |
|--------|-------|
| Total learnings | 4 |
| Last updated | 2026-04-05 |
