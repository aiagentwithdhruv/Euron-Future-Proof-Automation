# Learning Hub — Future-Proof AI Automation

> The system that learns from its own mistakes and compounds intelligence over time.
> Adapted from the MSBC Learning Hub pattern. Every session reads this. Every error improves it.

---

## How The Diamond Works

```
Agent builds automation --> hits error --> fixes it
  --> Logs to ERRORS.md (this hub)
    --> Logs improvement to LEARNINGS.md
      --> Updates technique file if pattern discovered
        --> Next session reads all of this on startup
          --> Never repeats the same mistake
            --> System compounds intelligence over time
```

---

## Structure

```
learning-hub/
├── CLAUDE.md              # You are here (hub rules)
├── ERRORS.md              # Error log: Error --> Cause --> Fix --> Rule
├── LEARNINGS.md           # Improvement log: What worked, what to keep doing
├── SELF-UPDATE.md         # Protocol for auto-updating on session start
├── techniques/            # Reusable automation patterns
│   ├── webhook-patterns.md
│   ├── bot-deployment.md
│   ├── api-integration.md
│   ├── cost-optimization.md
│   ├── deployment-patterns.md
│   └── [new patterns added as discovered]
└── automations/
    └── CATALOG.md         # Registry of all automations built
```

---

## Rules for Every Session

### On Session Start
1. **Read `ERRORS.md`** — check for relevant past mistakes before building
2. **Read `LEARNINGS.md`** — check for patterns that apply to current task
3. **Check `techniques/`** — is there a technique file for what we're building?

### During Build
4. **When you hit an error** — log it immediately to `ERRORS.md` using the format below
5. **When you discover a pattern** — check if a technique file exists; create or update it
6. **When a prompt works well** — log it to the project's `PROMPTS.md` AND root `PROMPTS.md`

### On Session End
7. **Log what was learned** — add to `LEARNINGS.md` if anything new was discovered
8. **Update `automations/CATALOG.md`** — if a new automation was built or an existing one was updated
9. **Update technique files** — if any patterns were confirmed or discovered

---

## Error Entry Format

```markdown
### [DATE] — [SHORT TITLE]
**Error:** What went wrong
**Cause:** Why it happened
**Fix:** What solved it
**Rule:** One-line rule to prevent this forever
**Applies to:** [project/everyone/specific-tool]
**Category:** [API | Deployment | AI/LLM | Frontend | Backend | Database | Security | n8n | General]
```

---

## Learning Entry Format

```markdown
### [DATE] — [SHORT TITLE]
**What:** What was discovered or confirmed
**Context:** Where/when this happened
**Pattern:** The reusable insight
**Applies to:** [project/everyone/specific-phase]
```

---

## Technique File Format

```markdown
# [Pattern Name] — [Short Description]

> **Source:** [Where learned — class, project, error]
> **Applies to:** [Phase/project type]
> **Last verified:** [Date]

---

## Problem
[What problem does this solve?]

## Pattern
[The reusable approach — steps, architecture, code]

## Example
[Real example from a bootcamp project]

## Gotchas
[Common mistakes when applying this pattern]

## Related
[Links to other technique files]
```

---

## Categories for Errors

1. **API** — Rate limits, auth failures, response parsing
2. **Deployment** — Docker, VPS, Vercel, Railway, domain/SSL
3. **AI/LLM** — Prompt failures, hallucination, cost overrun, model routing
4. **Frontend** — UI bugs, build failures, responsive issues
5. **Backend** — FastAPI, async, DB queries, serialization
6. **Database** — Schema, migrations, connection, queries
7. **Security** — Secrets leaked, injection, auth bypass
8. **n8n** — Workflow errors, webhook failures, node config
9. **Bots** — Telegram/Discord/WhatsApp API issues
10. **General** — Everything else

---

## Connection to Other Systems

| System | Relationship |
|--------|-------------|
| Root `CLAUDE.md` | References this hub; reads on session start |
| Root `PROMPTS.md` | Prompts discovered here get indexed there |
| Root `DEPLOY.md` | Deployment errors feed back here |
| Project `CLAUDE.md` | Each project inherits learning hub access |
| MSBC Learning Hub | Same Diamond pattern; different scope |
| Obsidian AI Second Brain | Sync techniques via `scripts/sync-obsidian.sh` |

---

> **"The factory that learns from its own mistakes is the factory that never stops improving."**
