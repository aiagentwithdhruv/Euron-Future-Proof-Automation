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

### 2026-04-19 — Snapshot-diff as source-of-truth beats re-analyzing full content
**What:** For any "watcher" agent (competitor, site, feed), the diff between last week's snapshot and this week's is the only input the LLM ever needs. Full scraped bodies are never re-read.
**Context:** `Autonomous_Research_Agent` — weekly competitor research. Storing full page bodies and re-analyzing would explode tokens/cost and break PII rules.
**Pattern:** fetch → build compact snapshot (hashes + titles + headings + pricing hints + URLs) → diff vs previous → feed ONLY diff to LLM → save new snapshot as next week's baseline. Snapshots are small (~1–5KB per competitor) and commitable.
**Applies to:** Any agent that watches for changes — competitor research, site monitoring, feed deltas, doc-update detection.

### 2026-04-19 — robots.txt isn't optional; build it as a gate, not a decoration
**What:** Major AI-automation vendors (n8n.io, lindy.ai) block bots on root/pricing in their robots.txt. If your scraper doesn't check, you're either silently violating ToS or getting 403'd.
**Context:** Dry-run test caught 5/6 URLs correctly skipped with `robots.txt DISALLOW` warnings — the single blog subdomain (`blog.n8n.io`) allowed. Without the gate, the agent would have hit the disallowed URLs and either been blocked or stored content it shouldn't have.
**Pattern:** `shared/robots_check.py` — cache `RobotFileParser` per domain + `is_allowed(url)` gate called BEFORE every GET + per-domain `wait_for_rate_limit()` enforcing 3s minimum gap + polite User-Agent with contact. Scraper returns status=`skipped` with reason=`robots-disallow` instead of failing. This lets the run log show exactly what was legal vs blocked.
**Applies to:** Every scraping/research agent. Reusable module in `Autonomous_Research_Agent/shared/robots_check.py`.

### 2026-04-19 — Best-effort multi-channel delivery: missing creds skip, don't crash
**What:** A delivery tool that requires ALL channel creds to be set is brittle. Better: each channel checks its own creds, missing → `status: skipped, reason: no-credentials`, others proceed.
**Context:** `Autonomous_Research_Agent/tools/deliver_report.py`. Dry-run succeeded with zero delivery credentials configured — every channel cleanly reported "skipped" in receipts.
**Pattern:** Receipt object per channel: `{status: ok|skipped|error, ...}`. Log aggregates them, failures are visible but don't abort the run. Hard failure only if the report itself can't be produced.
**Applies to:** Any multi-channel delivery automation — social posting, notifications, digest bots.

---

## Teaching & Students

_(New entries will be added from class sessions)_

---

## Stats

| Metric | Count |
|--------|-------|
| Total learnings | 4 |
| Last updated | 2026-04-05 |
