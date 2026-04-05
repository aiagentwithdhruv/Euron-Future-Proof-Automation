---
name: n8n-workflow-deploy
description: Deploy automations as n8n workflows — visual, webhook-driven, multi-step. Use when user asks to create a workflow, connect services visually, or deploy to n8n.
argument-hint: "[workflow-description]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# n8n Workflow Deployment

## Goal
Create and deploy visual automation workflows using n8n. Connect any APIs, trigger via webhooks/schedule, no code needed for basic flows.

## When to Use
- Multi-step workflows (Form → CRM → Email → Slack → Sheet)
- Webhook-driven automation (receive events, process, respond)
- Visual workflows students/clients can understand without code
- Connecting 400+ integrations via built-in nodes

## Prerequisites
- n8n running (self-hosted on VPS or n8n Cloud)
- For self-hosted: Docker installed on VPS

## Self-Hosted Setup (Docker Compose)

### 1. Create docker-compose.yml on your VPS
```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
      - N8N_HOST=your-domain.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://your-domain.com/
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

volumes:
  n8n_data:
```

### 2. Start n8n
```bash
docker-compose up -d
```

### 3. Access n8n
Open `http://your-vps-ip:5678` or `https://your-domain.com`

## Creating a Workflow

### Via n8n UI (Visual)
1. Open n8n dashboard
2. Click "New Workflow"
3. Add trigger node (Webhook, Schedule, or Manual)
4. Add processing nodes (HTTP Request, Code, IF, etc.)
5. Connect nodes by dragging edges
6. Click "Activate" to make it live

### Via JSON Import
1. Create a workflow JSON file
2. In n8n: Workflows → Import → paste JSON

### Example: Social Media Post Workflow
```json
{
  "name": "Daily Social Media Post",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {"interval": [{"field": "hours", "hoursInterval": 24}]}
      },
      "position": [250, 300]
    },
    {
      "name": "Generate Content",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.euron.one/api/v1/euri/chat/completions",
        "method": "POST",
        "headers": {"Authorization": "Bearer {{$env.EURI_API_KEY}}"},
        "body": {
          "model": "gpt-4o-mini",
          "messages": [{"role": "user", "content": "Write a LinkedIn post about AI automation"}]
        }
      },
      "position": [450, 300]
    },
    {
      "name": "Post to LinkedIn",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.linkedin.com/rest/posts",
        "method": "POST",
        "headers": {
          "Authorization": "Bearer {{$env.LINKEDIN_ACCESS_TOKEN}}",
          "LinkedIn-Version": "202603"
        },
        "body": "={{JSON.stringify({author: 'urn:li:person:' + $env.LINKEDIN_PERSON_URN, lifecycleState: 'PUBLISHED', visibility: 'PUBLIC', commentary: $json.choices[0].message.content, distribution: {feedDistribution: 'MAIN_FEED'}})}}"
      },
      "position": [650, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": {"main": [[{"node": "Generate Content", "type": "main", "index": 0}]]},
    "Generate Content": {"main": [[{"node": "Post to LinkedIn", "type": "main", "index": 0}]]}
  }
}
```

## Free Hosting Options

| Option | Cost | Setup |
|--------|------|-------|
| Oracle Cloud Free VPS | $0 forever | Docker Compose on ARM VM |
| PikaPods | ~$3.80/mo | Managed, zero DevOps |
| Hostinger VPS | ~$5/mo | 1-click n8n template |
| DigitalOcean | $6/mo | Docker Compose on droplet |

## Gotchas

1. **Webhook URLs change if n8n restarts** (self-hosted without domain). Use Cloudflare Tunnel for stable URLs.
2. **n8n stores data in SQLite by default** — switch to PostgreSQL for production.
3. **Environment variables** — set in docker-compose.yml, not in workflow nodes.
4. **Activate workflows** — creating a workflow doesn't start it. Click the toggle.
5. **Error handling** — always add an Error Trigger node to catch failures.

---

## Schema

### Inputs
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `workflow_description` | string | Yes | What the workflow should do |
| `trigger_type` | string | No | webhook, schedule, or manual (default: schedule) |
| `nodes` | array | No | Specific n8n nodes to use |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `workflow_json` | file | Importable n8n workflow JSON |
| `deployed` | boolean | Whether workflow was activated |

### Credentials
| Name | Source |
|------|--------|
| Per-integration | n8n Credentials panel (OAuth, API keys) |

### Composable With
Any project — n8n can call any API, webhook, or script.

### Cost
Free (self-hosted), ~$24/mo (n8n Cloud Starter)
