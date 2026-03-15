---
name: Tech Comparison
category: research
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [comparison, analysis, decision-making, tech-stack]
difficulty: beginner
tools: [claude-code, cursor, gemini]
---

# Tech Comparison

## Purpose
> Compare technologies with a structured pros/cons matrix to make informed decisions.

## When to Use
- Choosing between frameworks, libraries, or services
- Evaluating tech stack options for a new project
- Teaching decision-making frameworks

## The Prompt

```
Compare these technologies for {{USE_CASE}}:

**Options:** {{TECH_OPTIONS}}
**Context:** {{PROJECT_CONTEXT}}
**Priority:** {{PRIORITIES}}

Evaluation criteria:
1. **Learning curve** — How fast can the team be productive?
2. **Performance** — Speed, scalability, resource usage
3. **Ecosystem** — Libraries, community, documentation
4. **Production readiness** — Stability, security, enterprise adoption
5. **Cost** — Licensing, hosting, operational overhead
6. **Integration** — How well it fits with {{EXISTING_STACK}}

Output format:
- Comparison matrix (criteria × options, scored 1-5)
- Pros/cons list for each option
- "Best for" scenarios (when to pick each)
- Final recommendation with reasoning
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{USE_CASE}}` | What you're building | `Real-time chat with AI agents` |
| `{{TECH_OPTIONS}}` | Technologies to compare | `FastAPI vs Express vs Django` |
| `{{PROJECT_CONTEXT}}` | Team and project details | `3-person team, MVP in 4 weeks` |
| `{{PRIORITIES}}` | What matters most | `Speed of development > scalability` |
| `{{EXISTING_STACK}}` | Current tech | `React frontend, PostgreSQL, Vercel` |
