# Deployment Guide for Students

> How to deploy your automations so they run 24/7 in real-time.
> Verified April 2026 pricing. Organized: Free first, then cheap.

---

## Quick Decision Tree

```
What are you deploying?
|
+-- Webhook / API endpoint?
|   --> Koyeb (free, always-on) or Vercel Serverless (free)
|
+-- Bot (Telegram / Discord / WhatsApp)?
|   --> Koyeb (free, no sleep) or Railway ($5/mo)
|
+-- n8n workflows?
|   --> Oracle Cloud Free VPS or Hostinger VPS ($5/mo)
|
+-- Scheduled / cron job?
|   --> GitHub Actions (free) or cron-job.org (free)
|
+-- Full-stack app (frontend + backend)?
|   --> Vercel (frontend) + Koyeb (backend) -- both free
|
+-- AI API / serverless Python / GPU?
|   --> Modal ($30/mo free credit) or Hugging Face Spaces (free CPU)
|
+-- Local development with webhooks?
|   --> Cloudflare Tunnel (free, needs domain) or ngrok (free, URL changes)
|
+-- React / Next.js frontend only?
    --> Vercel Hobby (free, best-in-class)
```

---

## Free Tier Platforms (Verified April 2026)

### Koyeb -- Best Free Always-On Platform
- **Free:** 1 web service: 0.1 vCPU, 512MB RAM, 1GB bandwidth. No credit card. Never expires.
- **Best for:** Bots, webhook listeners, FastAPI APIs -- anything that needs to be always-on
- **Docker:** Yes
- **Key advantage:** No sleep mode. App runs 24/7. This is the #1 differentiator vs Render.
- **Limitations:** Only 1 service free. 512MB RAM tight for heavy Python. 1GB/mo bandwidth.
- **Deploy:** Connect GitHub repo or push Docker image
- **URL:** koyeb.com

### Railway
- **Free:** $5/mo subscription includes $5 compute credit (net $0 for light workloads)
- **Best for:** Bots, APIs, full-stack with database (one-click PostgreSQL/Redis)
- **Docker:** Yes
- **Key advantage:** Best developer experience. Billed by the second. A light bot ~$3-8/mo.
- **Limitations:** Not truly free -- $5/mo subscription required. Hobby plan.
- **Deploy:** Connect GitHub -> auto-deploy on push
- **URL:** railway.app

### Vercel
- **Free:** Hobby plan: 100GB bandwidth, 1M function invocations, 60s function timeout
- **Best for:** React/Next.js frontends, serverless API endpoints, static sites
- **Docker:** No (serverless only)
- **Key advantage:** Best-in-class for React/Next.js. Zero config deployment.
- **Limitations:** No persistent processes. 60s function timeout. Non-commercial use only. No WebSockets.
- **Deploy:** `vercel deploy` or connect GitHub
- **URL:** vercel.com

### Render
- **Free:** Web services (750 hrs/mo), static sites (unlimited)
- **Best for:** Static frontends, occasional-use APIs
- **Docker:** Yes
- **Key advantage:** Free PostgreSQL (90 days)
- **Limitations:** Web services sleep after 15 min inactivity. ~60s cold start. Not for webhooks/bots.
- **Workaround:** Use cron-job.org to ping every 14 minutes (fragile)
- **URL:** render.com

### Modal -- Best for AI/GPU Workloads
- **Free:** $30/month compute credit. No credit card to start.
- **Best for:** AI inference, RAG pipelines, voice agents, GPU Python functions, scheduled AI jobs
- **Docker:** Yes (custom containers)
- **Key advantage:** Sub-second cold starts. GPUs available (T4, A100, H100).
- **Limitations:** Python only. Not a web server host. $30 credit burns fast on GPUs.
- **Deploy:** `modal deploy app.py`
- **URL:** modal.com
- **Skill available:** `student-starter-kit/skills/modal-deploy/`

### Hugging Face Spaces
- **Free:** 2 CPU cores, 16GB RAM (basic tier). Docker supported.
- **Best for:** AI demo UIs (Gradio), model inference demos, RAG chatbot interfaces
- **Docker:** Yes
- **Limitations:** Ephemeral disk (lost on restart). Sleeps if unused. No persistent DB.
- **Deploy:** Push to HF repo -> auto-deploy
- **URL:** huggingface.co/spaces

### Oracle Cloud Always Free -- Most Powerful Free VPS
- **Free:** Up to 4 ARM VMs (4 OCPUs, 24GB RAM total) + 2 AMD VMs. 200GB storage. 10TB bandwidth. **Free forever, not a trial.**
- **Best for:** Self-hosting n8n, Docker stacks, bots, databases, full control
- **Docker:** Yes (full Linux VPS)
- **Key advantage:** 24GB RAM free is extraordinary. Run everything on one server.
- **Limitations:** Signup is notoriously difficult -- "Out of Capacity" errors common. Try less popular regions (Monterrey, Osaka, Marseille). Requires credit card (not charged).
- **URL:** oracle.com/cloud/free

### PythonAnywhere
- **Free:** 1 web app, scheduled tasks, Bash console
- **Best for:** Simple Python bots, scripts, basic web apps
- **Docker:** No
- **Limitations:** 1 web app only. Outbound HTTP to allowlisted sites only (free tier).
- **URL:** pythonanywhere.com

### Cloudflare Workers
- **Free:** 100,000 requests/day, 10ms CPU time per request
- **Best for:** Webhook ingestion, API routing, lightweight middleware
- **Docker:** No (JavaScript/TypeScript only, Python via experimental WASM)
- **Limitations:** 10ms CPU limit. Not for Python AI logic. Not for bots.
- **URL:** workers.cloudflare.com

---

## Scheduling (Free)

### GitHub Actions
- **Free:** Unlimited minutes (public repos). 2,000 min/mo (private repos).
- **Best for:** Daily scrapers, weekly reports, cron jobs, data pipelines
- **Minimum interval:** Every 5 minutes
- **Limitations:** Max 6 hours per job. Scheduled runs may be delayed under load.
- **Example:**
  ```yaml
  on:
    schedule:
      - cron: '0 8 * * *'  # Daily at 8 AM UTC
  ```
- **URL:** github.com/features/actions

### cron-job.org
- **Free:** Unlimited cron jobs, 1-minute minimum interval
- **Best for:** Keeping free-tier apps alive (anti-sleep pings), triggering webhooks on schedule
- **Limitations:** Only makes HTTP requests (no code execution). 30s timeout.
- **URL:** cron-job.org

---

## Local Development Tunnels (Free)

### Cloudflare Tunnel (Recommended)
- **Free:** Unlimited bandwidth, no session timeouts, stable URL
- **Best for:** Permanent webhook URLs, exposing local n8n, sharing local dev
- **Requirement:** Domain managed by Cloudflare (domains cost $5-10/yr)
- **Setup:**
  ```bash
  brew install cloudflared
  cloudflared tunnel --url http://localhost:8000
  ```
- **Key advantage:** Once configured, URL is permanent. No restarts needed.

### ngrok
- **Free:** 1 tunnel, random URL (changes on restart)
- **Best for:** Quick one-off webhook testing
- **Limitations:** URL changes every restart. 1GB/mo bandwidth. Browser warning page.
- **Setup:**
  ```bash
  brew install ngrok && ngrok http 8000
  ```

---

## Paid (Low-Cost) Options

### Hostinger VPS
- **Cost:** ~$5-6/month (1 vCPU, 4GB RAM, 50GB NVMe, 4TB bandwidth)
- **Best for:** n8n self-hosting (1-click templates), beginners wanting managed setup
- **Docker:** Yes
- **Key advantage:** n8n-optimized templates. Kodee AI assistant. 4GB RAM at entry tier.
- **URL:** hostinger.com

### DigitalOcean
- **Cost:** $4/mo (512MB) or $6/mo (1GB RAM, recommended)
- **Student deal:** $200 free credit for 1 year via GitHub Student Developer Pack
- **Best for:** Production deployments, n8n hosting, full-stack apps
- **Docker:** Yes (1-click image available)
- **Key advantage:** Best documentation. Familiar Ubuntu/Debian. The $200 student credit = 2+ years of free hosting.
- **URL:** digitalocean.com

### Hetzner
- **Cost:** ~$5-5.50/month (2 vCPU, 4GB RAM, 40GB SSD) -- prices increased ~30% in April 2026
- **Best for:** Cost-sensitive production, EU data residency
- **Docker:** Yes
- **Key advantage:** Best price-to-performance ratio even after increase
- **URL:** hetzner.com

### PikaPods (Managed n8n)
- **Cost:** ~$3.80/month
- **Best for:** Students who want n8n without managing a VPS
- **Key advantage:** Handles updates, SSL, backups. Zero DevOps.
- **URL:** pikapods.com

### Fly.io (No Longer Free)
- **Cost:** ~$5-10/month minimum (no free tier for new users since Oct 2024)
- **Docker:** Yes (Firecracker microVMs)
- **Key advantage:** Global edge deployment. Docker-native.
- **Limitations:** Hidden costs: dedicated IPv4 ($2/mo), storage ($0.15/GB), egress ($0.02/GB)
- **URL:** fly.io
- **Note:** Skip unless you specifically need global edge deployment

---

## Recommended Stack by Project Type

### Telegram/Discord Bot
```
Free:   Koyeb (always-on, no sleep, no credit card)
Paid:   Railway ($5/mo) or Hostinger VPS ($5/mo)
Deploy: Docker container with auto-restart
```

### Webhook Pipeline (Form -> CRM -> Email -> Slack)
```
Free:   Koyeb (webhook receiver) + GitHub Actions (scheduled processing)
Or:     n8n self-hosted on Oracle Cloud Free VPS
Paid:   n8n on Hostinger VPS ($5/mo)
```

### AI Chatbot (RAG + Vector DB)
```
Free:   Modal (AI backend, $30/mo credit) + Vercel (frontend) + Supabase (pgvector, free tier)
Paid:   Same stack scales to paid tiers
Deploy: modal deploy + vercel deploy
```

### n8n Self-Hosted Workflow Engine
```
Free:   Oracle Cloud Free Tier (ARM VM, if you can get it)
Cheap:  PikaPods ($3.80/mo managed) or Hostinger VPS ($5/mo)
Better: DigitalOcean ($6/mo) with GitHub Student Pack ($200 credit)
Deploy: Docker Compose (n8n + PostgreSQL + Nginx + SSL)
```

### Full-Stack AI Personal Assistant (Capstone)
```
Free:   Vercel (frontend) + Koyeb (backend) + Supabase (DB)
Cheap:  DigitalOcean droplet ($6/mo) -- everything on one server
Deploy: Docker Compose with Nginx reverse proxy + SSL via Certbot
```

### Scheduled Research Agent
```
Free:   GitHub Actions (cron trigger) + Modal (AI processing)
Cheap:  VPS cron + local scripts
Deploy: .github/workflows/research.yml with schedule trigger
```

---

## Docker Compose Template (VPS Deployment)

For self-hosting n8n + your automations on any VPS:

```yaml
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASS}
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

  app:
    build:
      context: .
      args:
        - BUILDPLATFORM=linux/amd64
    ports:
      - "8000:8000"
    env_file: .env
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - n8n
      - app
    restart: unless-stopped

volumes:
  n8n_data:
```

**ALWAYS remember:** `docker build --platform linux/amd64` on M-series Mac.

---

## AWS CLI Deployment (Advanced)

For production-grade AWS deployment:

```bash
# 1. Build + push to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build --platform linux/amd64 -t my-app .
docker tag my-app:latest <account>.dkr.ecr.us-east-1.amazonaws.com/my-app:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/my-app:latest

# 2. Deploy to ECS Fargate
aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment

# 3. Or deploy as Lambda (serverless)
aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip
```

**Architecture:** Frontend on Amplify, Backend on ECS Fargate, DB on RDS (same VPC), CI/CD via GitHub Actions.

---

## Cost Summary for Students

| Setup | Monthly Cost | What You Get |
|-------|-------------|--------------|
| **100% Free** | $0 | Koyeb (backend) + Vercel (frontend) + GitHub Actions (cron) + Supabase (DB) |
| **Near-Free** | $0-5 | Railway ($5 incl credit) or PikaPods n8n ($3.80) |
| **Minimal VPS** | $4-6 | DigitalOcean/Hostinger VPS -- full control, Docker, self-host everything |
| **Comfortable** | $10 | VPS + domain + monitoring (UptimeRobot free) |
| **Professional** | $20-30 | VPS + n8n + custom domain + SSL + monitoring |

**Rule:** Start free. Move to VPS when you need 24/7 uptime or self-hosted n8n. Use the GitHub Student Developer Pack for $200 DigitalOcean credit.

---

*Verified: April 2026 | Sources: Official docs + community reports*
