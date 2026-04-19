# Deployment Guide — Future-Proof AI Automation Bootcamp

> Two deployment paths. Both free. Pick the one that fits the automation.
> Every automation in this bootcamp deploys to ONE of these.

---

## The Decision Tree (90 seconds)

```
Does your automation need to run on a schedule (daily, weekly, hourly cron)?
├── YES → GitHub Actions (Path A)
└── NO  → Does it need to react to events / webhooks / chat in real-time?
          ├── YES → n8n (Path B)
          └── Still unsure? Default to n8n. It handles both.
```

### Rule of thumb

| Pattern | Path | Example |
|---------|------|---------|
| Fires on a clock (daily/weekly/monthly) | **GitHub Actions** | AI News Digest, Research Agent, Daily LinkedIn Post |
| Listens for webhook/event/user | **n8n** | RAG Chatbot, Signup onboarding, Shopify orders |
| Long-running or conversational | **n8n** | Chatbot, support ticket system |
| Batch processing, reports | **GitHub Actions** | CRM weekly report, lead scraping |
| Needs human approval in-flow | **n8n** | Ticket approval, content approval |

---

## Path A — GitHub Actions (for scheduled automations)

### Why

- **100% free** for public repos. Unlimited minutes.
- No infrastructure. No VPS. No Docker.
- Secrets managed in GitHub Settings → Secrets.
- Artifacts + logs retained 30 days automatically.
- Git push = new version live on next schedule.

### When

Anything time-based: daily news, weekly reports, hourly polls, monthly summaries. The workflow sleeps between runs — you pay nothing for idle time.

### Setup (5 minutes, one-time)

1. **Push your automation to a public GitHub repo** (private repos have minute limits — avoid for students).

2. **Create `.github/workflows/<name>.yml`** at the repo root. Example:
   ```yaml
   name: Weekly Research Report

   on:
     schedule:
       - cron: '0 3 * * 1'    # Mon 3 AM UTC = 8:30 AM IST
     workflow_dispatch:        # manual trigger button
       inputs:
         dry_run:
           type: boolean
           default: false

   permissions:
     contents: write           # if you commit state back

   jobs:
     run:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with: { python-version: '3.11' }
         - run: pip install -r Autonomous_Research_Agent/requirements.txt
         - run: python Autonomous_Research_Agent/tools/run_research.py
           env:
             EURI_API_KEY: ${{ secrets.EURI_API_KEY }}
             TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
             TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
   ```

3. **Add your secrets** → GitHub repo → Settings → Secrets and variables → Actions → New repository secret.

4. **Trigger manually** to test:
   ```bash
   gh workflow run "<Your Workflow Name>" -f dry_run=true --ref main
   gh run list --workflow="<Your Workflow Name>" --limit 1
   gh run view <run-id> --log
   ```

### What's already deployed on GitHub Actions

| Automation | Schedule | Workflow file |
|------------|----------|---------------|
| AI News Telegram Bot | Daily 9 AM UTC (2:30 PM IST) | `.github/workflows/daily-news.yml` |
| Daily LinkedIn Post | Daily 4:30 AM UTC (10 AM IST) | `.github/workflows/daily-linkedin.yml` |
| Weekly Research Report | Mon 3 AM UTC (8:30 AM IST) | `.github/workflows/weekly-research-report.yml` |

Use these as templates for new cron automations.

### Cron cheat sheet

```
# min hour day month day-of-week
'0 9 * * *'        → daily 9 AM UTC
'30 4 * * *'       → daily 4:30 AM UTC (10 AM IST)
'0 3 * * 1'        → every Monday 3 AM UTC
'*/15 * * * *'     → every 15 minutes (careful, uses minutes fast)
'0 0 1 * *'        → 1st of every month
```

Use [crontab.guru](https://crontab.guru) to build custom schedules.

### Cost

**$0 on public repos.** Private repos: 2,000 free min/mo, then $0.008/min.
Most bootcamp automations run 1-3 min per execution. Daily cron = ~90 min/mo.

### Gotchas (already logged in `learning-hub/ERRORS.md`)

1. **Workflows must live at repo root `.github/workflows/`** — not inside subfolders.
2. **Support both .env files (local) AND env vars (CI).** Check `os.getenv("GITHUB_ACTIONS")` before requiring a .env file.
3. **Grant `permissions: contents: write`** if the workflow commits state (e.g. snapshot diffs).
4. **Use `persist-credentials: true`** on checkout if you push back from the workflow.

---

## Path B — n8n (for event-driven automations)

### Why

- Visual workflow — students SEE the pipeline node-by-node.
- Always-on, no cold starts.
- Built-in chat widget (langchain ChatTrigger).
- Built-in webhook receiver.
- 400+ node integrations — no custom API wrappers.
- Swap nodes, re-run, iterate in seconds.

### When

Anything that reacts: webhooks, chat, form submits, Slack buttons, Telegram messages, signup events. Also ANY automation where you want students to SEE the flow live.

### Bootcamp default

We use the bootcamp n8n instance: **`https://n8n.aiwithdhruv.cloud`**. Students get credentials in the bootcamp. For your own: self-host on Hostinger ($5/mo) or Oracle Cloud (free forever VPS).

### Setup (workflow via API — no UI clicks)

You can build n8n workflows programmatically from Claude Code:

```python
import json, urllib.request

N8N_URL = "https://n8n.aiwithdhruv.cloud"
API_KEY = "<your n8n API key>"

workflow = {
    "name": "My Automation",
    "nodes": [ ... ],            # define nodes
    "connections": { ... },       # wire them
    "settings": {"executionOrder": "v1"}
}

req = urllib.request.Request(
    f"{N8N_URL}/api/v1/workflows",
    data=json.dumps(workflow).encode(),
    headers={"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"},
    method="POST"
)
print(json.loads(urllib.request.urlopen(req).read()))
```

Full example: see `RAG_Knowledge_Chatbot/` — the chatbot is built entirely via the n8n API.

### Setup (workflow via UI)

1. Open `https://n8n.aiwithdhruv.cloud`
2. New Workflow → name it
3. Drag nodes: Trigger → Logic → Action
4. Save → Activate

### Common node patterns

| Pattern | Nodes |
|---------|-------|
| Webhook receiver | Webhook trigger → Code → Respond to Webhook |
| Chat bot | Chat Trigger (public) → Code → HTTP Request (LLM) → Format → auto-return |
| Schedule | Schedule trigger → ... → action |
| Telegram notify | Any trigger → Telegram (with credential) |
| RAG | Chat Trigger → Embed (HTTP) → Vector search (HTTP to Supabase) → LLM (HTTP) |

### What's already deployed on n8n

| Automation | Type | URL |
|------------|------|-----|
| AIwithDhruv RAG Chatbot | Public chat | `https://n8n.aiwithdhruv.cloud/webhook/aiwithdhruv-chat/chat` |

Many other workflows run in the bootcamp instance — check "Active workflows" in the dashboard.

### Cost

- **n8n instance:** self-hosted = $5/mo VPS or free on Oracle Cloud
- **Bootcamp:** shared instance provided
- **LLM calls from n8n:** pay-per-call (Euri free tier, OpenAI, Claude, etc.)

### Gotchas

1. **Chat Trigger mode must be `hostedChat`** to serve the widget UI (not `webhook`).
2. **Chat Trigger responseMode = `lastNode`** — otherwise needs a Respond node.
3. **Supabase service_role key blocks browser User-Agents** — use a non-browser UA like `AIwithDhruv/1.0` in HTTP Request nodes.
4. **HTTP Request on array response** — each array element becomes a separate n8n item. Use `$input.all()` to collect.

---

## Path Selection for Every Bootcamp Project

| Project | Path | Why |
|---------|------|-----|
| `AI_News_Telegram_Bot` | **GH Actions** ✅ deployed | Daily cron |
| `Social-Media-Automations` (daily LinkedIn) | **GH Actions** ✅ deployed | Daily cron |
| `Autonomous_Research_Agent` | **GH Actions** ✅ deployed | Weekly cron |
| `Autonomous_Research_Agent` | **GH Actions** ✅ deployed | Weekly cron |
| `RAG_Knowledge_Chatbot` | **n8n** ✅ deployed | Live chat widget |
| `Multi_Channel_Onboarding` | **n8n** | Webhook trigger from signup |
| `CRM_Automation` | Either (use GH for weekly report, n8n for real-time lead webhook) | Mixed |
| `AI_Support_Ticket_System` | **n8n** | Polls inbox / IMAP / webhook |
| `AI_Voice_Agent` | **n8n** OR Koyeb-alternative | FastAPI tool endpoints, needs always-on. Use self-hosted n8n with webhook receiver OR Hugging Face Spaces (free). |
| `D2C_Ecommerce_Suite` | **n8n** | Shopify/Woo webhooks |
| `Client_Acquisition_System` | **n8n** (outreach) + **GH Actions** (weekly batch scrape) | Hybrid |
| `Salesforce_PDF_Filler` | Either | Works as GH Actions batch OR n8n webhook trigger |

---

## Secrets Management

### GitHub Actions
- Settings → Secrets and variables → Actions → New repository secret
- Access in workflow: `${{ secrets.MY_KEY }}`
- Already set in this repo: `EURI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `NEWSAPI_KEY`, `TAVILY_API_KEY`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PERSON_URN`

### n8n
- Workflow → node → Credentials → Create New
- Stored encrypted in n8n database
- Reference by credential ID in node config (what we do when we create workflows via API)

### Local development
- Copy `.env.example` → `.env`, fill keys
- `.env` is gitignored
- Scripts auto-detect CI vs local via `GITHUB_ACTIONS` env var

---

## Keys + Where to Get Them

| Key | Where | Free Tier |
|-----|-------|-----------|
| `EURI_API_KEY` | euron.one → Dashboard → API | 200K tokens/day |
| `GOOGLE_API_KEY` (Gemini) | ai.google.dev → Get API key | 1500 req/day |
| `SUPABASE_SERVICE_KEY` | Supabase project → Settings → API | Free up to 500MB |
| `TELEGRAM_BOT_TOKEN` | Telegram @BotFather → /newbot | Free |
| `NEWSAPI_KEY` | newsapi.org | 100/day (dev) |
| `TAVILY_API_KEY` | tavily.com | 1000/mo free |
| `LINKEDIN_ACCESS_TOKEN` | developer.linkedin.com (OAuth flow) | Free |
| `RESEND_API_KEY` | resend.com | 100 emails/day |

---

## Deploying a New Automation — End-to-End Checklist

1. **Decide the path** — schedule → GH Actions. Event/chat → n8n.
2. **Build locally first** — pass dry-run tests. NEVER deploy untested code.
3. **Store secrets in the platform** — GitHub Secrets or n8n credentials. Never in code.
4. **Write the workflow file** (GH Actions) OR **push workflow via n8n API**.
5. **Manual trigger / test** — `gh workflow run` or click in n8n.
6. **Check logs** — `gh run view --log` or n8n executions panel.
7. **Log any errors** to `learning-hub/ERRORS.md` with Error → Cause → Fix → Rule.
8. **Update `learning-hub/automations/CATALOG.md`** — mark as deployed with URL.
9. **Tell the user** — the URL, the schedule, what it does.

---

## What We DON'T Use (and why)

- **Koyeb** — free tier was removed. Now requires card + $30/mo. Not worth it when n8n handles the same use cases.
- **Railway** — no more free tier.
- **Vercel serverless Python** — 10 sec timeout breaks RAG + long jobs.
- **Render free tier** — sleeps after 15 min idle. Breaks always-on bots.
- **Heroku** — no free tier since 2022.
- **AWS/GCP/Azure** — overkill for bootcamp projects. Revisit at Phase 5 when deploying for paying clients.

---

**Summary:**

```
Schedule?  → GitHub Actions
Reacts?    → n8n
Unsure?    → n8n
```

That's it. Two paths. Both free. Every automation in this bootcamp fits one of them.
