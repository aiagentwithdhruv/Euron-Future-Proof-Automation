# Self-Update Protocol — Student Doubts System

> How Claude keeps this folder accurate and growing.
> Dhruv triggers updates. Claude executes them.

---

## Trigger Phrase

When Dhruv says any of these, the self-update protocol activates:

- **"log this doubt"**
- **"add this question"**
- **"student asked: ..."**
- **"new doubt from WhatsApp: ..."**
- **"update the doubts"**

---

## What Claude Does When a New Doubt Comes In

### Step 1 — Determine the Phase/Week
Map the topic to the correct phase using the syllabus:
- Business audit, systems thinking → Phase 1 (Week 1-2)
- AI design, prompt engineering → Phase 2 (Week 3-4)
- n8n, webhooks, APIs, CRM → Phase 3 (Week 5-7)
- AI routing, RAG, agents, Euri → Phase 4 (Week 8-10)
- VPS, Docker, deployment, SSL → Phase 5 (Week 11-12)
- E-commerce, healthcare, real estate → Phase 6 (Week 13-14)
- AI Personal Assistant, backend, frontend → Phase 7 (Week 15-17)
- Portfolio, clients, pricing → Phase 8 (Week 18-19)
- Everything else → General

### Step 2 — Create a Doubt ID
Format: `[PHASE-WEEK-ID]` or `[G-ID]` for general
- Example: `W3-D001` = Phase 2, Week 3, first doubt
- Example: `G-D002` = General, second doubt
- Increment the ID number sequentially within each section

### Step 3 — Add to DOUBTS-LOG.md
Add the entry under the correct phase section:
```markdown
### [ID] "Student's exact question in quotes"
- **Date:** YYYY-MM-DD
- **Source:** WhatsApp / Live session / Community
- **Question:** Full question as asked
- **Answer:** Clear, complete answer in Dhruv's voice
- **Code Fix:** (if applicable — include working snippet)
- **WhatsApp Reply:** Copy-paste ready, 3-5 lines max
- **Pattern:** One-line label for this doubt type
```

### Step 4 — Update INDEX.md
Add a new row to the index table:
```markdown
| [ID](DOUBTS-LOG.md#anchor) | Phase# | Week# | Short topic | keyword1, keyword2, keyword3 | YYYY-MM-DD |
```
Also add the ID under the correct "Doubts by Phase" section.
Update the Stats table (increment total count, update last updated date).

### Step 5 — Check if it's a New Pattern
Compare against the Common Doubt Patterns table in `CONTEXT.md`.
- If it's a **new pattern** not in the table → add a row
- If it's an **existing pattern** → increment frequency (note in INDEX.md Recurring Patterns)

### Step 6 — Check if Answer Needs a Reply Template
- If the answer is reusable (same doubt will come from multiple students) → add to `REPLY-TEMPLATES.md` under the correct phase section
- Template format: plain text, 3-5 lines, Dhruv's voice, no markdown formatting (WhatsApp doesn't render it)

### Step 7 — Confirm to Dhruv
After all updates:
```
Logged [ID] under Phase X / Week Y.
Added to INDEX. [Pattern: new/existing].
WhatsApp reply ready — copy from REPLY-TEMPLATES.md > [section].
```

---

## Update Rules

| Rule | Detail |
|------|--------|
| Never modify original question | Log student's exact words |
| Always answer completely | Not just "check the docs" — give the actual answer |
| Keep WhatsApp replies ≤ 5 lines | Dhruv's voice: direct, no fluff |
| Don't duplicate doubts | Check INDEX first — if similar exists, add a note to existing entry |
| Date format | Always YYYY-MM-DD |
| Update stats in INDEX.md | Every time a new doubt is added |

---

## When to Update CONTEXT.md

Update the Common Doubt Patterns table in `CONTEXT.md` when:
- A doubt appears **2+ times** from different students
- A doubt reveals a **fundamental misunderstanding** about the course
- A doubt exposes a **tool/API confusion** not yet documented

Do NOT update CONTEXT.md for one-off, specific questions.

---

## File Ownership

| File | Who Updates | How Often |
|------|------------|-----------|
| `CONTEXT.md` | Claude | When new pattern emerges (2+ occurrences) |
| `DOUBTS-LOG.md` | Claude | Every new doubt |
| `REPLY-TEMPLATES.md` | Claude | Every reusable answer |
| `INDEX.md` | Claude | Every new doubt |
| `SELF-UPDATE.md` | Claude | Only if protocol needs to change |

---

## Example Trigger

**Dhruv says:**
> "Log this doubt — student asked: how do I connect WhatsApp Business API to n8n?"

**Claude does:**
1. Identifies → Phase 3, Week 6 (Multi-Channel Communication)
2. Creates ID → `W6-D001`
3. Adds full entry to DOUBTS-LOG.md
4. Adds row to INDEX.md
5. Checks CONTEXT.md — new pattern? → Yes → adds row
6. Adds WhatsApp reply template to REPLY-TEMPLATES.md under Phase 3
7. Confirms to Dhruv with the ID and template location

---

*This protocol ensures the doubts system grows smarter with every session.*
*Last updated: 2026-03-08*
