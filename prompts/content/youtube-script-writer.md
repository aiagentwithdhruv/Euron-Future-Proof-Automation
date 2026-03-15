---
name: YouTube Script Writer
category: content
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [youtube, script, video, content-creation, tutorial]
difficulty: beginner
tools: [claude-code, cursor, gemini]
---

# YouTube Script Writer

## Purpose
> Write engaging YouTube tutorial/explainer scripts with hooks, structure, and clear teaching flow.

## When to Use
- Creating tutorial or explainer videos
- Planning YouTube content for AI/tech topics
- Teaching content creation

## The Prompt

```
Write a YouTube script for:

**Topic:** {{TOPIC}}
**Target audience:** {{AUDIENCE}}
**Video length:** {{DURATION}}
**Style:** {{STYLE}}

Script structure:
1. **Hook (0:00-0:30)** — Bold claim, surprising fact, or relatable problem. Make viewer stay.
2. **Context (0:30-1:30)** — Why this matters. What they'll learn. What they'll be able to do after.
3. **Main content** — Break into 3-5 clear sections. Each section: concept → example → result.
4. **Recap (last 60s)** — Summarize key takeaways. Show the before/after.
5. **CTA** — Subscribe, comment prompt (specific question), link to next video.

Rules:
- Conversational tone, not academic
- Use analogies for complex concepts
- Include on-screen text suggestions in [BRACKETS]
- Mark b-roll/demo moments with [SHOW: description]
- Keep sentences short and punchy
- Front-load value — don't gate the good stuff behind 10 minutes of intro
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{TOPIC}}` | Video subject | `Build an AI agent with Claude Code in 10 minutes` |
| `{{AUDIENCE}}` | Who's watching | `Developers new to AI agents` |
| `{{DURATION}}` | Target length | `8-12 minutes` |
| `{{STYLE}}` | Presentation style | `Tutorial with live coding, casual tone` |
