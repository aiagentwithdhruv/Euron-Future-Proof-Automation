---
name: koyeb-deploy
description: Deploy always-on bots and APIs to Koyeb for free. Use when user needs 24/7 uptime, persistent bots (Telegram, Discord), or always-on API endpoints.
argument-hint: "[project-path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Koyeb Deployment (Free, Always-On)

## Goal
Deploy bots and APIs that run 24/7 without sleeping. Free tier: 1 service, 0.1 vCPU, 512MB RAM. No credit card needed.

## When to Use
- Telegram/Discord/WhatsApp bots that need to respond instantly
- API endpoints that must be always available (no cold starts)
- Webhook receivers that can't afford to sleep
- ANY service that needs 24/7 uptime at $0

## Why Koyeb Over Render/Railway
- **Render free tier sleeps after 15 min** — bots stop responding
- **Railway costs $5/mo** — not free
- **Koyeb free tier: no sleep, no credit card, runs forever**

## Prerequisites
- Koyeb account (koyeb.com — free, no credit card)
- Project with a `Dockerfile` or GitHub repo
- Koyeb CLI (optional): `curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh`

## Step-by-Step

### 1. Create a Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### 2. Create Procfile (alternative to Dockerfile)
```
web: python main.py
```

### 3. Deploy via Koyeb Dashboard (Easiest)
1. Go to app.koyeb.com
2. Click "Create App"
3. Select "GitHub" → connect your repo
4. Set:
   - **Builder:** Dockerfile (or Buildpack)
   - **Region:** Washington (closest free region)
   - **Instance:** Free (0.1 vCPU, 512MB RAM)
   - **Environment Variables:** Add all keys from `.env`
5. Click "Deploy"

### 4. Deploy via CLI (Advanced)
```bash
# Login
koyeb login

# Create service from GitHub
koyeb app create my-bot
koyeb service create my-bot/main \
  --git github.com/username/repo \
  --git-branch main \
  --instance-type free \
  --env EURI_API_KEY=your-key \
  --env TELEGRAM_BOT_TOKEN=your-token \
  --port 8000:http
```

### 5. Add Health Check (Recommended)
Add a `/health` endpoint to your app:
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

Set health check in Koyeb: path = `/health`, port = `8000`

### 6. Custom Domain (Optional)
Koyeb gives you: `your-app-username.koyeb.app`
For custom domain: Settings → Domains → Add your domain + CNAME record

## For Telegram Bot on Koyeb

```python
# main.py — Telegram bot with webhook mode (production)
import os
from fastapi import FastAPI, Request
import requests

app = FastAPI()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.post(f"/webhook/{TOKEN}")
async def webhook(request: Request):
    update = await request.json()
    chat_id = update["message"]["chat"]["id"]
    text = update["message"]["text"]
    # Process and reply
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                  json={"chat_id": chat_id, "text": f"You said: {text}"})
    return {"ok": True}

@app.get("/health")
def health():
    return {"status": "ok"}

# Set webhook on startup
@app.on_event("startup")
async def set_webhook():
    url = f"https://your-app.koyeb.app/webhook/{TOKEN}"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/setWebhook", json={"url": url})
```

## Gotchas

1. **Free tier = 1 service only.** Choose your most important always-on service.
2. **512MB RAM limit.** Heavy ML models won't fit. Use Modal for AI tasks instead.
3. **1GB bandwidth/month.** Fine for bots, tight for high-traffic APIs.
4. **No persistent disk.** Don't store files locally — use Supabase/S3 for storage.
5. **Redeploys on every git push.** Make sure your main branch is stable.

---

## Schema

### Inputs
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Path to the project |
| `github_repo` | string | Yes | GitHub repo URL |
| `port` | integer | No | Port to expose (default: 8000) |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `url` | string | Public URL (your-app.koyeb.app) |
| `deployed` | boolean | Whether deployment succeeded |

### Credentials
| Name | Source |
|------|--------|
| All project `.env` keys | Koyeb Dashboard → Environment Variables |

### Composable With
`github-actions-deploy` (for cron tasks alongside always-on bot)

### Cost
Free (1 service, no credit card)
