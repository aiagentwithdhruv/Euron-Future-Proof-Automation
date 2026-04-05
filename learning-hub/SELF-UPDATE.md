# Self-Update Protocol

> How this system keeps itself accurate, growing, and connected.
> Run automatically on session start. Manually trigger with "update the hub".

---

## On Every Session Start

Claude MUST do these checks silently (no need to announce unless something important is found):

### 1. Check Learning Hub Health
- Does `learning-hub/ERRORS.md` exist and have the right format?
- Does `learning-hub/LEARNINGS.md` exist?
- Are there technique files relevant to today's task?

### 2. Read Recent Errors
- Scan `ERRORS.md` for entries related to today's task
- Apply those rules proactively (don't repeat logged mistakes)

### 3. Read Recent Learnings
- Scan `LEARNINGS.md` for patterns that apply
- Use confirmed techniques instead of guessing

### 4. Check Automation Catalog
- Is the project we're working on already cataloged?
- If not, note it for cataloging at session end

---

## On Error During Build

When any error occurs during a build session:

```
1. Fix the error (priority: get it working)
2. Log to ERRORS.md using the standard format:
   ### [DATE] — [SHORT TITLE]
   **Error:** What went wrong
   **Cause:** Why it happened
   **Fix:** What solved it
   **Rule:** One-line prevention rule
   **Applies to:** [scope]
   **Category:** [one of 10 categories]
3. Check if this error reveals a pattern worth adding to techniques/
4. Continue building
```

---

## On Session End

Before closing a session where we built something:

```
1. Log any new learnings to LEARNINGS.md
2. Update automations/CATALOG.md if something new was built
3. Update root PROMPTS.md if any prompts were created
4. Update technique files if patterns were discovered
5. Run sync if CLAUDE.md was edited:
   ./sync.sh
```

---

## Trigger Phrases

When Dhruv says any of these, execute the corresponding action:

| Phrase | Action |
|--------|--------|
| "update the hub" | Run full self-update check (steps 1-4 above) |
| "log this error" | Add error entry to ERRORS.md |
| "log this learning" | Add entry to LEARNINGS.md |
| "what have we learned about X" | Search ERRORS.md + LEARNINGS.md + techniques/ |
| "catalog this" | Add/update entry in automations/CATALOG.md |
| "sync to obsidian" | Run scripts/sync-obsidian.sh |
| "check for mistakes" | Read ERRORS.md for patterns related to current work |
| "what automations do we have" | Read automations/CATALOG.md |

---

## Obsidian Sync Protocol

The learning hub can sync to the AI Second Brain (Obsidian vault):

```bash
bash scripts/sync-obsidian.sh
```

**What syncs:**
- `techniques/*.md` -> Obsidian `03-Resources/automation-techniques/`
- `ERRORS.md` -> Obsidian `03-Resources/error-logs/automation-errors.md`
- `LEARNINGS.md` -> Obsidian `03-Resources/learning-logs/automation-learnings.md`
- `automations/CATALOG.md` -> Obsidian `01-Projects/automation-catalog.md`

**What does NOT sync:**
- `.env` files (secrets)
- `.tmp/` folders (intermediate data)
- `runs/` logs (too verbose for Obsidian)

---

## Auto-Growth Expectations

| Timeframe | Expected State |
|-----------|---------------|
| Week 1 | 5-10 error entries, 3-5 learnings, 1-2 technique files |
| Month 1 | 30+ errors, 15+ learnings, 5+ techniques, full catalog |
| Month 3 | 100+ errors, 50+ learnings, 10+ techniques, competitive moat |
| Month 6 | System so rich it prevents 90% of errors before they happen |

---

## Rules

1. **Never skip logging** — an unlogged error is a wasted failure
2. **Log immediately** — don't batch up errors for later
3. **Include the "Why"** — the cause matters more than the fix
4. **One-line rules** — if you can't say the prevention rule in one line, it's not clear enough
5. **Cross-reference** — link errors to techniques, learnings to projects
6. **Date everything** — YYYY-MM-DD on every entry
7. **Don't be precious** — log small mistakes too, they compound

---

> **"The system that learns from its mistakes is the system that never stops improving."**
