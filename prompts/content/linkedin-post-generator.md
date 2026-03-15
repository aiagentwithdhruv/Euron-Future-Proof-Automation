---
name: LinkedIn Post Generator
category: content
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [linkedin, social-media, thought-leadership, personal-brand]
difficulty: beginner
tools: [claude-code, gemini]
---

# LinkedIn Post Generator

## Purpose
> Create LinkedIn posts with strong hooks, value-packed body, and engagement-driving CTAs.

## When to Use
- Sharing learnings, wins, or insights on LinkedIn
- Building personal brand in AI/tech space
- Teaching social media content creation

## The Prompt

```
Write a LinkedIn post about:

**Topic:** {{TOPIC}}
**Key insight:** {{INSIGHT}}
**Tone:** {{TONE}}

Structure:
1. **Hook (line 1)** — Pattern interrupt. Must make the scroll stop. Use one of:
   - Bold contrarian take
   - Surprising statistic or result
   - "I just did X and here's what happened"
   - Question that challenges assumptions

2. **Body (5-10 lines)** — Deliver the insight. Use:
   - Short paragraphs (1-2 sentences each)
   - Line breaks for readability
   - Concrete examples, not abstract advice
   - Numbers and specifics over vague claims

3. **CTA (last 1-2 lines)** — Drive engagement:
   - Ask a specific question (not "thoughts?")
   - Invite sharing of their experience
   - Tag relevant people if appropriate

Rules:
- No hashtag spam (max 3-5 relevant hashtags at bottom)
- No corporate jargon
- Write like you talk
- Under 1300 characters for optimal reach
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{TOPIC}}` | Post subject | `How I automated 80% of my workflow with AI agents` |
| `{{INSIGHT}}` | The core takeaway | `Most people use AI for chat, not automation` |
| `{{TONE}}` | Voice/style | `Authentic, slightly provocative, data-backed` |
