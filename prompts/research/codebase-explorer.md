---
name: Codebase Explorer
category: research
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [exploration, documentation, architecture, onboarding]
difficulty: intermediate
tools: [claude-code, cursor]
---

# Codebase Explorer

## Purpose
> Explore and document an unfamiliar codebase systematically.

## When to Use
- Onboarding to a new project
- Understanding legacy code
- Documenting existing systems

## The Prompt

```
Explore this codebase and create a comprehensive map:

**Focus area:** {{FOCUS_AREA}}
**Questions I need answered:** {{QUESTIONS}}

Investigation steps:
1. **Structure** — Map the directory tree, identify layers, find entry points
2. **Data flow** — Trace how data enters, transforms, and exits the system
3. **Key abstractions** — Identify core classes/modules and their responsibilities
4. **Configuration** — Find env vars, config files, feature flags
5. **Dependencies** — List external services, APIs, databases used
6. **Patterns** — Identify coding patterns, conventions, architectural style

Output:
- Architecture diagram (text-based)
- Module-by-module summary (one paragraph each)
- Entry points and request flow
- Key files to read first (ordered)
- Potential issues or tech debt spotted
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{FOCUS_AREA}}` | What to focus on | `Backend API layer`, `Auth system`, `Full stack` |
| `{{QUESTIONS}}` | Specific things to figure out | `How does auth work? Where is the AI logic?` |
