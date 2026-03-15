---
name: Market Research
category: research
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [market, research, analysis, business, strategy]
difficulty: intermediate
tools: [claude-code, gemini]
---

# Market Research

## Purpose
> Research market landscape for a product, service, or technology.

## When to Use
- Evaluating a new product idea
- Understanding competitive landscape
- Preparing pitch decks or business cases

## The Prompt

```
Research the market landscape for:

**Product/Service:** {{PRODUCT}}
**Target market:** {{TARGET_MARKET}}
**Key question:** {{KEY_QUESTION}}

Research areas:
1. **Market size** — TAM, SAM, SOM with data sources
2. **Competitors** — Top 5-10 players, their positioning, pricing, strengths/weaknesses
3. **Trends** — Key market trends, emerging technologies, shifts in buyer behavior
4. **Target users** — Primary personas, their pain points, current solutions
5. **Differentiation** — Gaps in the market, underserved segments, positioning opportunities
6. **Risks** — Market risks, regulatory concerns, technical barriers

Output:
- Executive summary (3 sentences)
- Competitor comparison table
- Market trend analysis
- Opportunity assessment
- Recommended positioning
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PRODUCT}}` | What you're building/selling | `AI-powered workflow automation for SMBs` |
| `{{TARGET_MARKET}}` | Who it's for | `Small businesses with 10-50 employees` |
| `{{KEY_QUESTION}}` | Main thing to answer | `Is there demand for no-code AI automation?` |
