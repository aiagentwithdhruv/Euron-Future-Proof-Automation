# Deployment Patterns — Getting Automations Running 24/7

> **Source:** Bootcamp Phase 5 + production experience + DEPLOY.md
> **Applies to:** Every automation that needs to run in production
> **Last verified:** 2026-04-05

---

## Problem
Students build locally. Automations need to run 24/7 without a laptop open. Deployment must be cheap/free and reliable.

## Decision Matrix

```
Is it a one-time/scheduled task?
  YES --> GitHub Actions (cron) or cron-job.org
  NO  --> Does it need to receive webhooks?
            YES --> Vercel serverless or Railway
            NO  --> Does it run continuously (bot)?
                      YES --> Railway or VPS
                      NO  --> Modal (serverless Python)
```

## Pattern 1: Serverless (Webhooks + APIs)

**When:** Your automation responds to HTTP requests (webhooks, API calls)
**Where:** Vercel (free), Cloudflare Workers (free), Modal (free)
**Pro:** Zero ops, auto-scales, free
**Con:** Cold starts, timeout limits, no persistent state

```bash
# Vercel deployment (Next.js or Python)
vercel deploy

# Modal deployment (Python)
modal deploy app.py
```

## Pattern 2: Container on PaaS (Bots + Workers)

**When:** Your automation runs continuously (Telegram bot, Discord bot, background worker)
**Where:** Railway (free $5/mo), Render (free with sleep), Fly.io (free 3 VMs)
**Pro:** Easy deploy from GitHub, Docker support
**Con:** Free tiers have limits (sleep, hours)

```bash
# Railway (connect GitHub repo, auto-deploy)
railway link
railway up

# Docker on any PaaS
docker build --platform linux/amd64 -t my-bot .
```

## Pattern 3: VPS (Full Control)

**When:** You need 24/7 uptime, self-hosted n8n, multiple services, or a database
**Where:** Oracle Cloud Free (free forever), Hostinger ($3/mo), DigitalOcean ($4/mo)
**Pro:** Full control, run anything, cheapest at scale
**Con:** You manage the server (updates, security, backups)

```bash
# VPS setup (once)
ssh root@your-vps
apt update && apt install docker.io docker-compose nginx certbot

# Deploy with Docker Compose
docker-compose up -d

# SSL certificate (free, auto-renewing)
certbot --nginx -d your-domain.com
```

## Pattern 4: Scheduled (Cron Jobs)

**When:** Your automation runs on a schedule (daily report, weekly research, hourly check)
**Where:** GitHub Actions (free), cron-job.org (free), VPS cron
**Pro:** Zero cost, reliable
**Con:** Not real-time, max 6hr per job (GitHub Actions)

```yaml
# .github/workflows/daily-task.yml
name: Daily Automation
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC daily
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          EURI_API_KEY: ${{ secrets.EURI_API_KEY }}
```

## Pattern 5: AWS CLI Deployment

**When:** Production-grade deployment with full AWS infrastructure
**Where:** AWS (ECS Fargate, Lambda, EC2)
**Pro:** Enterprise-grade, scalable, lots of free tier
**Con:** Complex, requires AWS knowledge

```bash
# AWS CLI — deploy to ECS Fargate
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build --platform linux/amd64 -t my-app .
docker tag my-app:latest <account>.dkr.ecr.<region>.amazonaws.com/my-app:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/my-app:latest
aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment

# AWS Lambda (serverless)
aws lambda update-function-code --function-name my-function --zip-file fileb://function.zip
```

## Gotchas

- **ARM vs AMD64:** ALWAYS `--platform linux/amd64` when building Docker on M-series Mac
- **Secrets in CI/CD:** Use GitHub Secrets, never commit `.env` files
- **Free tier sleep:** Railway/Render free tiers sleep after inactivity. Use cron-job.org to keep alive.
- **Domain/SSL:** Cloudflare free tier handles DNS + SSL + CDN. Always use it.
- **Monitoring:** Always add a health check endpoint (`/health`) and an uptime monitor (UptimeRobot free)

## Related
- `webhook-patterns.md` — what runs on these deployments
- `cost-optimization.md` — keeping deployment costs down
