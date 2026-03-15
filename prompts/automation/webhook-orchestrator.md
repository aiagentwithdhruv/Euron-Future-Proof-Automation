---
name: Webhook Orchestrator
category: automation
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [webhook, event-driven, orchestration, modal]
difficulty: advanced
tools: [claude-code, modal, n8n]
---

# Webhook Orchestrator

## Purpose
> Design event-driven webhook pipelines for multi-step automation.

## When to Use
- Building event-driven architectures
- Chaining multiple services via webhooks
- Setting up Modal webhook endpoints

## The Prompt

```
Design a webhook-driven pipeline for:

**Use case:** {{USE_CASE}}
**Events to handle:** {{EVENTS}}
**Actions per event:** {{ACTIONS}}
**Error handling:** {{ERROR_STRATEGY}}

Requirements:
1. Define webhook endpoints (URL structure, HTTP method, payload schema)
2. Validate incoming payloads (reject malformed requests)
3. Add idempotency (prevent duplicate processing)
4. Include retry logic with exponential backoff
5. Log all events for debugging
6. Add authentication (webhook secret/HMAC verification)

Output:
- Endpoint definitions with payload schemas
- Processing logic for each event type
- Error handling and retry strategy
- Monitoring/alerting recommendations
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{USE_CASE}}` | The automation scenario | `Process Stripe payments → update DB → send email` |
| `{{EVENTS}}` | Events to listen for | `payment.succeeded, payment.failed, subscription.cancelled` |
| `{{ACTIONS}}` | What to do per event | `Update user status, send receipt, notify team` |
| `{{ERROR_STRATEGY}}` | How to handle failures | `Retry 3x with backoff, then alert Slack` |
