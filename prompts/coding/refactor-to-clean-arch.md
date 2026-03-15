---
name: Refactor to Clean Architecture
category: coding
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [refactoring, clean-architecture, design-patterns]
difficulty: advanced
tools: [claude-code, cursor, gemini]
---

# Refactor to Clean Architecture

## Purpose
> Refactor messy/monolithic code into clean, layered architecture with proper separation of concerns.

## When to Use
- Code has business logic mixed into routes/controllers
- Database queries scattered across multiple layers
- Need to make code testable and maintainable

## The Prompt

```
Refactor this code to follow clean architecture:

{{CODE_OR_FILE_PATH}}

Current problems to fix:
{{PROBLEMS}}

Target architecture:
1. Routes/Controllers — HTTP concerns only (parse request, call service, return response)
2. Services — All business logic, orchestration, validation rules
3. Repositories — All database/external data access
4. Schemas/DTOs — Data validation and transformation

Rules:
- Routes must NOT contain business logic or database calls
- Services must NOT import HTTP framework objects (Request, Response)
- Repositories must NOT contain business rules
- Each layer only depends on the layer below it
- Use dependency injection for testability
- Preserve all existing behavior — this is a refactor, not a rewrite
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{CODE_OR_FILE_PATH}}` | Code or file to refactor | `src/api/main.py` |
| `{{PROBLEMS}}` | Specific issues to address | `SQL in routes, no error handling, mixed concerns` |
