---
name: modal-deploy
description: Deploy serverless Python functions and AI workloads to Modal. Use when user needs GPU, AI inference, serverless Python, or scheduled AI tasks.
argument-hint: "[script-path]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Modal Deployment (Serverless Python + GPU)

## Goal
Deploy Python functions to Modal for serverless execution. $30/month free credit. GPU available for AI tasks.

## When to Use
- AI/ML inference (LLM calls, embeddings, image generation)
- Serverless Python functions (run on demand, scale to zero)
- GPU workloads (T4, A100, H100)
- Scheduled AI tasks (daily RAG ingestion, batch processing)
- Webhook endpoints for AI processing

## When NOT to Use
- Always-on bots (use Koyeb)
- Frontend/dashboard (use Vercel)
- Visual workflows (use n8n)

## Prerequisites
- Modal account (modal.com — free, $30/mo credit)
- `pip install modal`
- `modal setup` (one-time auth)

## Step-by-Step

### 1. Install and authenticate
```bash
pip install modal
modal setup
# Opens browser for auth — click approve
```

### 2. Create a Modal app
```python
# app.py
import modal

app = modal.App("my-automation")

@app.function()
def generate_post(topic: str) -> str:
    """Generate a social media post using AI."""
    from openai import OpenAI
    import os

    client = OpenAI(
        base_url="https://api.euron.one/api/v1/euri",
        api_key=os.environ["EURI_API_KEY"],
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Write a LinkedIn post about {topic}"}],
    )
    return response.choices[0].message.content

# Webhook endpoint (callable via HTTP)
@app.function()
@modal.web_endpoint(method="POST")
def webhook(data: dict):
    topic = data.get("topic", "AI automation")
    post = generate_post.remote(topic)
    return {"post": post}

# Scheduled task (runs daily)
@app.function(schedule=modal.Cron("0 9 * * *"))
def daily_post():
    post = generate_post.remote("AI automation trends")
    # Post to LinkedIn, etc.
    print(f"Generated: {post[:100]}...")
```

### 3. Add secrets
```bash
# Add secrets via Modal dashboard or CLI
modal secret create my-secrets \
  EURI_API_KEY=your-key \
  LINKEDIN_ACCESS_TOKEN=your-token
```

Then reference in code:
```python
@app.function(secrets=[modal.Secret.from_name("my-secrets")])
def generate_post(topic: str):
    ...
```

### 4. Deploy
```bash
# Test locally first
modal run app.py

# Deploy to cloud (persistent)
modal deploy app.py
```

### 5. Call your endpoint
```bash
curl -X POST https://your-app--webhook.modal.run \
  -H "Content-Type: application/json" \
  -d '{"topic": "AI in 2026"}'
```

## GPU Functions

```python
@app.function(gpu="T4")  # or "A100", "H100"
def run_inference(prompt: str):
    # GPU-accelerated inference
    ...
```

GPU pricing:
- T4: $0.000164/sec (~$0.59/hr)
- A100: $0.00044/sec (~$1.58/hr)
- H100: $0.001097/sec (~$3.95/hr)

$30 free credit = ~50 hours of T4 time.

## Gotchas

1. **Cold starts** — first call after idle takes 2-5 seconds. Use `keep_warm=1` for critical endpoints.
2. **$30 credit burns fast on GPU** — use CPU for non-ML tasks.
3. **Secrets are separate** — not read from `.env`. Use Modal dashboard or `modal secret create`.
4. **Python only** — no Node.js, no Docker (Modal has its own container system).
5. **modal deploy vs modal run** — `run` is one-time test, `deploy` is persistent.

---

## Schema

### Inputs
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `script` | file_path | Yes | Python file to deploy |
| `gpu` | string | No | GPU type: T4, A100, H100 (default: none/CPU) |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `url` | string | Webhook endpoint URL |
| `deployed` | boolean | Whether deployment succeeded |

### Credentials
| Name | Source |
|------|--------|
| `MODAL_TOKEN_ID` | `modal setup` (automatic) |
| `MODAL_TOKEN_SECRET` | `modal setup` (automatic) |
| App secrets | Modal Dashboard or `modal secret create` |

### Composable With
`vercel-deploy` (Vercel frontend → calls Modal backend), `github-actions-deploy` (cron triggers Modal)

### Cost
Free ($30/mo credit), then pay-per-second compute
