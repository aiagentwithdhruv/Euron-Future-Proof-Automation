# Future-Proof AI Automation Bootcamp

A self-learning automation factory for the **Future-Proof AI Automation Bootcamp** on [Euron](https://euron.one).
Every automation in this repo is **built with AI, deployed to free infrastructure, and production-grade.**

Built by [Dhruv Tomar (AIwithDhruv)](https://aiwithdhruv.com).

---

## What This Repo Is

A complete, self-contained learning environment:

- **15 real automations** — from AI news bots to RAG chatbots to e-commerce suites
- **Two deployment paths** — GitHub Actions (cron) + n8n (event-driven)
- **Self-learning system** — every error logged, every fix becomes a rule
- **Reusable agents + skills + prompts** — drop them into any new project
- **Works in Claude Code, Cursor, Cline, Gemini** — same rules everywhere

Works on: Mac · Linux · Windows (WSL). Python 3.11+. No paid infra.

---

## Student Quickstart (15 minutes)

```bash
# 1. Clone
git clone https://github.com/aiagentwithdhruv/Euron-Future-Proof-Automation.git
cd Euron-Future-Proof-Automation

# 2. Open in Claude Code / Cursor
#    The CLAUDE.md file loads automatically. Rules are active.

# 3. Read these 3 files (in order)
#    - CLAUDE.md            → the system's rules
#    - DEPLOY.md            → two deployment paths (GH Actions + n8n)
#    - SYLLABUS.md          → the 8-phase bootcamp structure

# 4. Pick a project to run
#    Each project has its own README.md + ATLAS-PROMPT.md (the AI build brief)
#    Copy .env.example → .env, fill keys, then run the dry-run command

# 5. Build your first new automation
bash scripts/new-automation.sh "My-First-Bot"
```

**Golden rule:** read `CLAUDE.md` at the root, then each project's `ATLAS-PROMPT.md`. That's how every AI assistant (Claude/Cursor/Cline) stays aligned.

---

## The 15 Automation Projects

### ✅ Already Deployed (learn from these first)

| # | Project | Deployed To | What It Does |
|---|---------|-------------|--------------|
| 1 | [AI News Telegram Bot](AI_News_Telegram_Bot/) | **GitHub Actions** | Daily AI news digest → Telegram |
| 2 | [Social Media Automations](Social-Media-Automations/) | **GitHub Actions** | Daily LinkedIn post with AI content |
| 3 | [Autonomous Research Agent](Autonomous_Research_Agent/) | **GitHub Actions** | Weekly competitor report → Telegram |
| 4 | [RAG Knowledge Chatbot](RAG_Knowledge_Chatbot/) | **n8n** | Public chat widget with cited answers |

### 🛠 Built & Tested — Ready to Deploy

| # | Project | Recommended Deploy | What It Does |
|---|---------|-------------------|--------------|
| 5 | [Multi-Channel Onboarding](Multi_Channel_Onboarding/) | n8n | Signup → Email + WhatsApp + Slack + follow-ups |
| 6 | [CRM Automation](CRM_Automation/) | n8n + GH Actions | Score leads → route → follow-up → weekly report |
| 7 | [AI Support Ticket System](AI_Support_Ticket_System/) | n8n | Email → AI classify + draft → human approve → send |
| 8 | [AI Voice Agent](AI_Voice_Agent/) | n8n / Vapi | Inbound receptionist + outbound caller |
| 9 | [D2C E-Commerce Suite](D2C_Ecommerce_Suite/) | n8n | Orders + support + cart recovery + reviews + inventory |
| 10 | [Client Acquisition System](Client_Acquisition_System/) | n8n + GH Actions | Scrape → enrich → qualify → outreach → proposal |

### 📚 Reference Projects (pre-built teaching examples)

| # | Project | Phase | What It Teaches |
|---|---------|-------|-----------------|
| 11 | [Salesforce PDF Filler](Salesforce_PDF_Filler/) | 4 | CRM integration + document automation |
| 12 | [Blotato Social Media](Blotato_Social_Media/) | 6 | YouTube → multi-platform repurposer |
| 13 | [Google Maps Lead Scraper](Scrape%20Data%20form%20Google%20Map/) | 3 | Data scraping with enrichment fallback |
| 14 | [Agentic Workflow Engine](Agentic%20Workflow%20for%20Students/) | 2 | Shared security + tooling framework |
| 15 | [Futuristic Space Shooter](Futuristic_Space_Shooter/) | Edu | Browser game (AI-assisted coding demo) |

---

## Every Project Has These 5 Files

Open any project folder, you'll find:

```
<Project>/
├── ATLAS-PROMPT.md         # The AI build brief — paste into Claude Code to rebuild this
├── CLAUDE.md               # Project-specific rules (inherits root)
├── README.md               # What + setup + run + deploy
├── PROMPTS.md              # All prompts used (indexed)
├── .env.example            # Required API keys (copy → .env, fill)
│
├── workflows/              # Markdown SOPs the agent reads
├── tools/                  # Atomic Python CLIs
├── runs/                   # Execution logs
└── .tmp/                   # Disposable intermediate files
```

**The ATLAS-PROMPT.md is the key file.** It tells any AI (you, Claude Code, Cursor) exactly what to build, what to reuse, what rules to follow. Students can rebuild any project from its ATLAS-PROMPT.md alone.

---

## Deployment (2 Paths, Both Free)

```
Schedule?  → GitHub Actions
Reacts?    → n8n
Unsure?    → n8n
```

That's the whole mental model. Full guide in [`DEPLOY.md`](DEPLOY.md).

| Path | Best For | Free Tier |
|------|----------|-----------|
| **GitHub Actions** | Cron jobs, batch work, scheduled reports | Unlimited on public repos |
| **n8n** | Chatbots, webhooks, event-driven, real-time | Self-host Oracle Cloud (free) or bootcamp instance |

**No Koyeb. No Railway. No Vercel serverless.** These either charge now or break our use cases. Two paths, both actually free, actually working in production.

---

## The Agentic Loop (core mental model)

Every automation in this bootcamp follows this pattern:

```
Sense → Think → Decide → Act → Learn
```

- **Sense:** trigger fires (webhook, schedule, event)
- **Think:** LLM reads context, plans
- **Decide:** picks the action
- **Act:** calls tools (email, CRM, API)
- **Learn:** logs outcome, feeds back to next run

Applied across 19 weeks of the bootcamp. From business audits (Phase 1) to AI Personal Assistant capstone (Phase 7).

---

## 3-Layer Architecture (why our automations work)

```
AGENT (LLM)          → reasons, plans, decides
  ↓
WORKFLOWS (.md SOPs) → instructions
  ↓
TOOLS (.py CLIs)     → deterministic execution
```

**Why this matters:** if the LLM does every step, 90% accuracy compounds to 59% after 5 steps. Offload execution to scripts: 90% × 100% × 100% × 100% × 100% = 90%. **Agent reasons. Scripts execute. Accuracy stays high.**

---

## The Diamond — Self-Learning System

Every error becomes a rule. Every rule prevents the same mistake next time.

```
Agent builds → hits error → fixes it
  → Logs to learning-hub/ERRORS.md
    → Next session reads it
      → Never repeats the same mistake
```

- **12+ errors logged** — Blotato quirks, LinkedIn upload fix, API version expiry, dict.get None trap, and more
- **Technique files** — webhooks, deployment, bots, API integration, cost optimization
- **Automation catalog** — every project indexed with tech + phase + reusable parts + deploy status

Read [`learning-hub/ERRORS.md`](learning-hub/ERRORS.md) before building — you'll skip a week of debugging.

---

## Agents (10)

Reusable AI agent definitions in [`student-starter-kit/agents/`](student-starter-kit/agents/). Each has a markdown persona file.

| Agent | Use For |
|-------|---------|
| **backend-builder** | FastAPI APIs, Python services |
| **frontend-builder** | Next.js, React, Tailwind |
| **code-reviewer** | Bug & security review |
| **test-runner** | Run/write tests |
| **deployer** | GitHub Actions, n8n, Docker, CI/CD |
| **db-architect** | Schema, migrations, RLS |
| **mcp-builder** | MCP servers for any API |
| **api-integrator** | OAuth, webhooks, REST/GraphQL |
| **security-auditor** | OWASP Top 10, secrets audit |
| **researcher** | Codebase exploration |

---

## Skills (15)

Reusable automation skills in [`student-starter-kit/skills/`](student-starter-kit/skills/).

| Category | Skills |
|----------|--------|
| **Content & Media** | video-edit, image-to-video, nano-banana-images, handdrawn-diagram, excalidraw-diagram, excalidraw-visuals, gamma-presentation |
| **Deployment** | github-actions-deploy, n8n-deploy, local-server |
| **Browser & Voice** | ghost-browser, whisper-voice |
| **Security & Meta** | guardrail-pipeline, skill-builder, add-webhook |

---

## Coding Rules (15)

Production standards in [`student-starter-kit/coding-rules/rules/`](student-starter-kit/coding-rules/rules/).

| # | Rule | Enforces |
|---|------|----------|
| 00 | Global Architect | Clean architecture |
| 10 | Backend FastAPI | Thin routes → services → repositories |
| 20 | Frontend Next.js | TypeScript, server components |
| 30 | Database PostgreSQL | Migrations, indexes, constraints |
| 35 | API Contracts | Versioned APIs, typed schemas |
| 40 | Cache Redis | Intentional TTLs |
| 45 | Environment Config | Validate at startup |
| 50 | RAG System | Separate ingestion/retrieval/generation |
| 55 | Data Versioning | Reproducible runs |
| 60 | Agents | Modular, validated tool calls |
| 70 | Security | No hardcoded secrets |
| 80 | Testing | Critical path tests |
| 85 | Observability | Structured errors, tracing |
| 90 | DevOps | GitHub Actions + n8n, rollback-safe |
| 99 | Response Style | Production code only |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python (FastAPI when needed) |
| Frontend | Next.js + React + Tailwind (optional) |
| Database | Supabase (PostgreSQL + pgvector) |
| LLMs | Euri (free) → OpenRouter → Claude/OpenAI/Gemini |
| Embeddings | Gemini (free, 768 / 1536 / 3072 dims) |
| Scheduling | GitHub Actions |
| Event-driven | n8n |
| Voice | Vapi / Bland / Retell |
| Editor | Claude Code, Cursor, Cline |

---

## Bootcamp Structure

8 phases · 19 weeks · 18+ deployed projects. Full details: [`SYLLABUS.md`](SYLLABUS.md).

- **Instructor:** Dhruv Tomar ([AIwithDhruv](https://aiwithdhruv.com))
- **Platform:** [Euron](https://euron.one/course/future-proof-ai-automation-bootcamp)
- **Schedule:** Sat & Sun, 8-10 PM IST
- **Certificate:** Every project deployed = your real portfolio

---

## Directory Layout

```
.
├── CLAUDE.md                        # Master rules
├── README.md                        # You are here
├── DEPLOY.md                        # Two deployment paths
├── SYLLABUS.md                      # 19-week structure
├── COURSE-CONTEXT.md                # Bootcamp details
├── PROMPTS.md                       # Master prompt index
│
├── .github/workflows/               # LIVE GitHub Actions deploys
│   ├── daily-news.yml
│   ├── daily-linkedin.yml
│   └── weekly-research-report.yml
│
├── learning-hub/                    # The Diamond self-learning system
│   ├── ERRORS.md
│   ├── LEARNINGS.md
│   ├── techniques/
│   └── automations/CATALOG.md
│
├── _template/                       # Project scaffold (auto-used by new-automation.sh)
│
├── <project folders>/               # 15 projects, each self-contained
│   └── ATLAS-PROMPT.md              # The build brief for each
│
├── student-starter-kit/
│   ├── agents/                      # 10 AI agent personas
│   ├── skills/                      # 15 reusable skills
│   └── coding-rules/                # 15 engineering standards
│
├── Agentic Workflow for Students/   # Shared security + tooling framework
├── prompts/                         # Global reusable prompts (12+)
└── scripts/
    ├── new-automation.sh            # Scaffold a new project
    └── sync-obsidian.sh             # Sync learning hub to Obsidian
```

---

## How Students Use This Repo

### Week 1 (you just cloned it)
1. Read `CLAUDE.md` + `DEPLOY.md` + `SYLLABUS.md`
2. Run ONE deployed project's dry-run (pick `AI_News_Telegram_Bot` — smallest)
3. Read its `ATLAS-PROMPT.md` to see the build brief
4. Read its `workflows/*.md` to see the SOP
5. Read its `tools/*.py` to see the code

### Week 2+
1. Pick a project from the "Built & Tested" list
2. Copy `.env.example` → `.env`, fill the keys
3. Run the dry-run command from the README
4. Modify, deploy, share

### When stuck
1. Check `learning-hub/ERRORS.md` — someone hit this before
2. Check `learning-hub/techniques/` — pattern files
3. Open an issue on this repo

### When you build your own automation
1. `bash scripts/new-automation.sh "My-Bot"`
2. Fill in the ATLAS-PROMPT.md (the AI build brief)
3. Claude Code reads it and builds
4. Deploy to GitHub Actions OR n8n
5. Add an entry to `learning-hub/automations/CATALOG.md`

---

## License

MIT — use, modify, teach, sell. Credit appreciated but not required.

---

**Questions? Stuck?** Open an issue, email aiwithdhruv@gmail.com, or DM on LinkedIn.

**Want the bootcamp itself?** [euron.one/course/future-proof-ai-automation-bootcamp](https://euron.one/course/future-proof-ai-automation-bootcamp)
