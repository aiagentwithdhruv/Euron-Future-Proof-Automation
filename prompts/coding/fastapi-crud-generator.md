---
name: FastAPI CRUD Generator
category: coding
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [fastapi, crud, api, python, backend]
difficulty: beginner
tools: [claude-code, cursor, gemini]
---

# FastAPI CRUD Generator

## Purpose
> Generate a complete FastAPI CRUD API with clean architecture (routes → services → repositories).

## When to Use
- Starting a new API resource/endpoint
- Adding CRUD operations for a new database table
- Teaching clean architecture patterns

## The Prompt

```
Create a complete FastAPI CRUD API for {{RESOURCE_NAME}} with the following fields:
{{FIELDS}}

Requirements:
- Clean 3-layer architecture: routes (HTTP only) → services (business logic) → repositories (DB access)
- Pydantic schemas for request/response validation
- Async database operations
- Pagination for list endpoints
- Proper error handling with consistent error response format
- RESTful naming under /api/v1/{{RESOURCE_NAME_PLURAL}}

Generate these files:
1. schemas/{{RESOURCE_NAME}}.py — Pydantic models (Create, Update, Response, List)
2. repositories/{{RESOURCE_NAME}}_repository.py — Database CRUD operations
3. services/{{RESOURCE_NAME}}_service.py — Business logic layer
4. routes/{{RESOURCE_NAME}}_routes.py — FastAPI router with endpoints
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{RESOURCE_NAME}}` | Name of the resource (singular) | `user`, `project`, `task` |
| `{{RESOURCE_NAME_PLURAL}}` | Plural form for URL paths | `users`, `projects`, `tasks` |
| `{{FIELDS}}` | List of fields with types | `name: str, email: str, role: enum(admin,user)` |

## Example Usage

**Input:**
```
Create a complete FastAPI CRUD API for project with the following fields:
name: str (required), description: str (optional), status: enum(active, paused, completed), owner_id: UUID

Requirements: [as above]
```

## Tips
- Always specify field types and required/optional
- Include enum values inline for clarity
- Add `owner_id` or `tenant_id` for multi-tenant setups
