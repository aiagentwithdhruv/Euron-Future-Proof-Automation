---
name: n8n Workflow Builder
category: automation
version: 1.0
author: Dhruv
created: 2026-03-15
updated: 2026-03-15
tags: [n8n, workflow, automation, no-code]
difficulty: intermediate
tools: [claude-code, cursor, gemini, n8n]
---

# n8n Workflow Builder

## Purpose
> Generate complete n8n workflow configurations from natural language descriptions.

## When to Use
- Building new automation workflows
- Connecting multiple services together
- Teaching workflow automation concepts

## The Prompt

```
Design an n8n workflow for the following automation:

**Goal:** {{WORKFLOW_GOAL}}
**Trigger:** {{TRIGGER_TYPE}}
**Services involved:** {{SERVICES}}
**Data flow:** {{DATA_FLOW}}

Requirements:
1. Define each node with its type, configuration, and connections
2. Include error handling nodes (Error Trigger → notification)
3. Add data transformation nodes where needed
4. Specify credentials needed (list them, don't hardcode)
5. Add a summary of the complete flow at the top

Output:
- Visual flow diagram (text-based)
- Node-by-node configuration
- Required credentials list
- Test plan to verify the workflow works
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{WORKFLOW_GOAL}}` | What the workflow should accomplish | `Auto-post new blog entries to LinkedIn and Twitter` |
| `{{TRIGGER_TYPE}}` | How the workflow starts | `Webhook, Schedule (every 6h), RSS feed` |
| `{{SERVICES}}` | External services to connect | `WordPress, LinkedIn, Twitter, Slack` |
| `{{DATA_FLOW}}` | How data moves through the system | `RSS → filter new → format → post to social → notify Slack` |
