---
name: Code Review Checklist
category: coding
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [code-review, security, quality, best-practices]
difficulty: intermediate
tools: [claude-code, cursor, gemini]
---

# Code Review Checklist

## Purpose
> Perform a structured code review covering security, performance, architecture, and best practices.

## When to Use
- Before merging any PR
- After completing a feature implementation
- Teaching code review practices

## The Prompt

```
Review the following code with this structured checklist. For each category, give a verdict (PASS/WARNING/FAIL) with specific line references.

Code to review:
{{CODE_OR_FILE_PATH}}

## Review Categories

### 1. Security
- [ ] No hardcoded secrets, API keys, or tokens
- [ ] User inputs validated and sanitized
- [ ] SQL injection protection (parameterized queries)
- [ ] Auth/authz checks on protected routes
- [ ] No sensitive data in logs or error messages
- [ ] Prompt injection resistance (if AI-facing)

### 2. Architecture
- [ ] Follows clean architecture (routes → services → repos)
- [ ] No business logic in routes/controllers
- [ ] No database access outside repositories
- [ ] Proper separation of concerns

### 3. Error Handling
- [ ] No swallowed exceptions
- [ ] Consistent error response format
- [ ] Client errors (4xx) vs server errors (5xx) distinguished
- [ ] Graceful degradation for external service failures

### 4. Performance
- [ ] No N+1 query patterns
- [ ] Appropriate use of pagination
- [ ] No unnecessary blocking operations
- [ ] Indexes exist for filtered/joined columns

### 5. Code Quality
- [ ] Type hints/TypeScript types present
- [ ] Clear, descriptive naming
- [ ] No code duplication
- [ ] Tests exist for critical paths

Output format:
- Overall verdict: PASS / FAIL
- Critical issues (must fix)
- Warnings (should fix)
- Suggestions (nice to have)
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{CODE_OR_FILE_PATH}}` | The code to review or file path | `src/api/routes/users.py` |

## Tips
- Run this on every PR, not just big ones
- Focus on critical issues first, suggestions last
- Pair with the `test-runner` agent after fixing issues
