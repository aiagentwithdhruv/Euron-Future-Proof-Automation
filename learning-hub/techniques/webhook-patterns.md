# Webhook Patterns — Event-Driven Automation

> **Source:** Bootcamp Phase 3 + production experience
> **Applies to:** Any automation that needs real-time triggers
> **Last verified:** 2026-04-05

---

## Problem
Most automations need to react to events in real-time: form submission, payment received, email arrived, CRM status changed. Polling is wasteful. Webhooks are instant.

## Pattern: Universal Webhook Architecture

```
External Event --> Webhook URL (your endpoint)
  --> Validate (signature, schema)
    --> Route (classify event type)
      --> Process (run the right tool/workflow)
        --> Respond (acknowledge within timeout)
          --> Log (run log for observability)
```

## Key Rules

1. **Always respond fast** — webhook senders expect a 200 response within 5-30 seconds. Do heavy processing AFTER responding.
2. **Validate signatures** — most services sign webhooks (HMAC-SHA256). Always verify.
3. **Idempotency** — webhooks can be sent multiple times. Use an event ID to deduplicate.
4. **Queue heavy work** — receive webhook -> acknowledge -> push to queue -> process async.
5. **Log everything** — webhook payloads are your debug trail. Log (with secrets masked).

## Implementation Patterns

### Pattern A: Vercel Serverless (Free, instant)
```python
# api/webhook.py (Vercel serverless function)
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        # Process event
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
```

### Pattern B: FastAPI (Local or VPS)
```python
@app.post("/webhook/{service}")
async def receive_webhook(service: str, request: Request):
    body = await request.json()
    # Validate signature
    # Route to handler
    # Process async (background task)
    return {"status": "received"}
```

### Pattern C: n8n Webhook Node
- Create Webhook node -> get URL -> paste in external service
- n8n handles the heavy lifting (routing, processing, error handling)

## For Development: Local Tunnels

```bash
# Cloudflare Tunnel (free, stable)
cloudflared tunnel --url http://localhost:8000

# ngrok (free, quick)
ngrok http 8000
```

## Gotchas

- **Timeout kills:** If your processing takes >30s, the sender thinks it failed and retries. Process async.
- **No HTTPS = rejected:** Most services require HTTPS. Tunnels handle this automatically.
- **Rate limits:** Some services batch events or rate-limit webhook calls. Handle bursts.
- **Replay attacks:** Old webhooks resent maliciously. Check timestamp + signature.

## Related
- `deployment-patterns.md` — where to host webhook endpoints
- `api-integration.md` — REST patterns for calling back
