# Bot Deployment — Telegram, Discord, WhatsApp

> **Source:** AI News Telegram Bot + Bootcamp Phase 3
> **Applies to:** Any bot automation
> **Last verified:** 2026-04-05

---

## Problem
Bots need to run 24/7, handle concurrent users, restart on crashes, and cost nothing for students.

## Pattern: Bot Lifecycle

```
Create bot (API token) --> Write handler code --> Test locally
  --> Containerize (Docker) --> Deploy (Railway/VPS)
    --> Add auto-restart --> Add monitoring --> Production
```

## Telegram Bot

### Setup
```bash
# 1. Create bot via @BotFather on Telegram
# 2. Get token: 123456789:ABCdefGHIjklMNOpqrstUVwxyz

# 3. Two modes:
#    Polling (simple, good for dev) — bot asks Telegram for updates
#    Webhook (production) — Telegram pushes updates to your URL
```

### Polling Mode (Development)
```python
import requests
import time

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=0):
    return requests.get(f"{BASE}/getUpdates", params={"offset": offset}).json()

def send_message(chat_id, text):
    requests.post(f"{BASE}/sendMessage", json={"chat_id": chat_id, "text": text})

# Simple polling loop
offset = 0
while True:
    updates = get_updates(offset)
    for update in updates.get("result", []):
        # Handle update
        offset = update["update_id"] + 1
    time.sleep(1)
```

### Webhook Mode (Production)
```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post(f"/webhook/{TOKEN}")
async def telegram_webhook(request: Request):
    update = await request.json()
    # Handle update
    return {"ok": True}

# Set webhook on startup
# POST https://api.telegram.org/bot{TOKEN}/setWebhook
# Body: {"url": "https://your-domain.com/webhook/{TOKEN}"}
```

### Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
# Railway (easiest free option)
railway link && railway up

# VPS with Docker
docker build --platform linux/amd64 -t my-bot .
docker run -d --restart unless-stopped --env-file .env my-bot
```

## Discord Bot

### Key Differences from Telegram
- Uses WebSocket (gateway) instead of HTTP polling
- Library: `discord.py` handles the connection
- Requires "bot" OAuth2 scope + intents
- Free hosting same as Telegram

## WhatsApp Bot

### Key Differences
- Requires WhatsApp Business API (not free for sending)
- Meta Cloud API: free for receiving, paid for sending templates
- Alternative: Twilio WhatsApp Sandbox (free for dev)
- Webhook-based (no polling)

## Gotchas

- **Bot token = password:** Never commit it. Always `.env`.
- **Telegram rate limits:** Max 30 messages/second to different chats, 1 msg/sec to same chat.
- **Crash recovery:** Always `--restart unless-stopped` in Docker. Always `try/except` in handlers.
- **Long polling timeout:** Set `timeout=30` in getUpdates to avoid busy-waiting.
- **Webhook SSL:** Telegram requires HTTPS. Use Cloudflare or Let's Encrypt.

## Related
- `deployment-patterns.md` — where to host bots
- `webhook-patterns.md` — webhook mode specifics
