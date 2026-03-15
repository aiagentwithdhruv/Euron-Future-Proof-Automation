---
name: Course Module Designer
category: content
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [course, education, curriculum, teaching, bootcamp]
difficulty: intermediate
tools: [claude-code, gemini]
---

# Course Module Designer

## Purpose
> Design structured course modules with learning objectives, exercises, and assessments.

## When to Use
- Creating bootcamp or course content
- Designing workshop curricula
- Planning educational content for Euron/students

## The Prompt

```
Design a course module for:

**Module title:** {{MODULE_TITLE}}
**Target learners:** {{LEARNER_PROFILE}}
**Prerequisites:** {{PREREQUISITES}}
**Duration:** {{DURATION}}

Structure each module with:

1. **Learning Objectives** (3-5)
   - By the end of this module, learners will be able to:
   - Use measurable verbs (build, implement, debug, deploy — not "understand" or "learn")

2. **Concepts** (theory — 30% of time)
   - Key concepts with analogies
   - Visual diagrams or architecture sketches
   - Real-world examples

3. **Hands-on Lab** (practice — 50% of time)
   - Step-by-step guided exercise
   - Starter code provided
   - Clear success criteria ("you'll know it works when...")
   - Common mistakes and how to fix them

4. **Challenge** (assessment — 20% of time)
   - Independent exercise that applies all concepts
   - Multiple difficulty levels (basic → stretch goals)
   - Rubric for self-assessment

5. **Resources**
   - Documentation links
   - Recommended reading
   - Next module preview

Rules:
- Every concept must have a practical exercise
- No concept without a "why this matters" explanation
- Include estimated time for each section
- Design for self-paced AND instructor-led delivery
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{MODULE_TITLE}}` | Module name | `Building Your First AI Agent with Claude Code` |
| `{{LEARNER_PROFILE}}` | Who they are | `CS students with Python basics, no AI experience` |
| `{{PREREQUISITES}}` | What they need to know | `Python fundamentals, basic CLI usage` |
| `{{DURATION}}` | Module length | `3 hours (1h theory, 1.5h lab, 30min challenge)` |
