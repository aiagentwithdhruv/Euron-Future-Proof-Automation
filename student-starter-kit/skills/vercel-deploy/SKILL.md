---
name: vercel-deploy
description: Deploy frontends, dashboards, webhooks, and API endpoints to Vercel. Use when user needs a web UI, dashboard, webhook receiver, or Next.js/React frontend.
argument-hint: "[project-path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Vercel Deployment

## Goal
Deploy web frontends, dashboards, serverless API endpoints, and webhook receivers to Vercel. Free tier is generous. Best for the "web face" of your automations.

## When to Use
- React/Next.js frontends and dashboards
- Serverless API endpoints (webhook receivers, form handlers)
- The "client-facing layer" — what users see and interact with
- Static sites, landing pages, documentation

## When NOT to Use
- Always-on bots (use Koyeb)
- Scheduled tasks (use GitHub Actions)
- Heavy AI/GPU workloads (use Modal)
- Long-running processes >60 seconds

## Prerequisites
- Vercel account (vercel.com — free)
- Node.js installed (for Vercel CLI)
- `npm i -g vercel`

## Step-by-Step

### Method 1: Next.js Frontend (Most Common)

#### 1. Create Next.js app
```bash
npx create-next-app@latest my-dashboard --typescript --tailwind
cd my-dashboard
```

#### 2. Build your dashboard
```typescript
// app/page.tsx — Automation dashboard
export default function Home() {
  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold">My Automations</h1>
      <div className="grid grid-cols-3 gap-4 mt-8">
        <AutomationCard name="LinkedIn Post" status="active" lastRun="2 hours ago" />
        <AutomationCard name="News Bot" status="active" lastRun="6 hours ago" />
        <AutomationCard name="Lead Scraper" status="paused" lastRun="3 days ago" />
      </div>
    </main>
  );
}
```

#### 3. Deploy
```bash
vercel deploy
# Follow prompts: link to project, confirm settings
# Get URL: https://my-dashboard.vercel.app
```

#### 4. Production deploy
```bash
vercel --prod
```

### Method 2: Serverless API (Webhook Receiver)

#### 1. Create API route
```python
# api/webhook.py (Vercel Python serverless function)
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length))

        # Process the webhook
        result = {"received": True, "data": body}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
```

#### 2. Add vercel.json
```json
{
  "builds": [
    {"src": "api/*.py", "use": "@vercel/python"}
  ],
  "routes": [
    {"src": "/api/(.*)", "dest": "/api/$1"}
  ]
}
```

#### 3. Deploy
```bash
vercel deploy
# Webhook URL: https://your-app.vercel.app/api/webhook
```

### Method 3: Connect GitHub (Auto-Deploy)
1. Go to vercel.com → "Import Project"
2. Connect GitHub repo
3. Every push to main → auto-deploys
4. Preview deploys on every PR

## Environment Variables
Vercel dashboard → Project → Settings → Environment Variables
Add all keys from `.env` there. They're injected at build + runtime.

## The Big Picture — Vercel as the Hub

```
[User Browser]
      |
      v
[Vercel Dashboard]  ← React/Next.js frontend
      |
  ┌───┴────┬──────────┬──────────┐
  v        v          v          v
GitHub   n8n       Koyeb      Modal
Actions  (webhook)  (bot API)  (AI tasks)
```

Vercel is the **control panel**. It calls your other services:
- Button click → triggers GitHub Actions workflow via API
- Form submit → sends data to n8n webhook
- Chat input → calls Koyeb bot API
- "Generate" button → calls Modal for AI processing

## Gotchas

1. **60-second function timeout** (free tier). Long tasks must be offloaded.
2. **No persistent processes.** Functions spin up per request, then die.
3. **Hobby plan = non-commercial.** For business use, upgrade to Pro ($20/mo).
4. **Python is Beta on Vercel.** Node.js/TypeScript is first-class.
5. **No WebSocket support** (free tier). Use polling or Server-Sent Events instead.

---

## Schema

### Inputs
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Path to the project |
| `framework` | string | No | nextjs, react, python (default: nextjs) |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `url` | string | Public URL (your-app.vercel.app) |
| `deployed` | boolean | Whether deployment succeeded |

### Credentials
| Name | Source |
|------|--------|
| All project `.env` keys | Vercel Dashboard → Environment Variables |

### Composable With
All other deployment skills — Vercel is the frontend, others are backends.

### Cost
Free (Hobby), $20/mo (Pro, commercial use)
