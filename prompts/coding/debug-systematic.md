---
name: Systematic Debugging
category: coding
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [debugging, troubleshooting, scientific-method]
difficulty: intermediate
tools: [claude-code, cursor, gemini]
---

# Systematic Debugging

## Purpose
> Debug issues methodically using hypothesis-driven investigation instead of random guessing.

## When to Use
- Bug reports that aren't immediately obvious
- Intermittent failures
- Teaching debugging methodology

## The Prompt

```
Debug this issue using the scientific method:

**Symptom:** {{SYMPTOM}}
**Expected behavior:** {{EXPECTED}}
**Actual behavior:** {{ACTUAL}}
**Context:** {{CONTEXT}}

Follow this process:
1. **Reproduce** — Confirm the issue and identify exact steps to trigger it
2. **Hypothesize** — List 3 most likely root causes, ranked by probability
3. **Investigate** — For each hypothesis, identify what evidence would confirm/deny it
4. **Test** — Check the most likely hypothesis first
5. **Fix** — Apply the minimal fix that addresses the root cause
6. **Verify** — Confirm the fix resolves the issue without breaking anything else

Output:
- Root cause (one sentence)
- The fix (code diff)
- Why this happened (so it can be prevented)
- Test to add (to catch regression)
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{SYMPTOM}}` | What's going wrong | `API returns 500 on user creation` |
| `{{EXPECTED}}` | What should happen | `Returns 201 with user object` |
| `{{ACTUAL}}` | What actually happens | `Returns 500 with "Internal Server Error"` |
| `{{CONTEXT}}` | Relevant context | `Started after deploying commit abc123` |
