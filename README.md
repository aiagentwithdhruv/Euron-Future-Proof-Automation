# Future-Proof AI Automation

A self-learning automation factory — agents, skills, coding rules, prompt library, learning hub, and production automation projects. Works across **Claude Code, Cursor, Cline, and Gemini**.

Built by [Dhruv Tomar (AIwithDhruv)](https://aiwithdhruv.com) for the [Future-Proof AI Automation Bootcamp](https://euron.one/course/future-proof-ai-automation-bootcamp) on Euron.

---

## Core Idea

```
Sense --> Think --> Decide --> Act --> Learn
```

Every automation follows the **Agentic Loop**. The system separates reasoning from execution — AI thinks, deterministic scripts execute. This keeps accuracy at 90% instead of compounding errors.

Edit one file (`CLAUDE.md`), run `./sync.sh`, and every AI tool gets the same context.

---

## What's Inside

```
.
├── CLAUDE.md                        # Master rules (source of truth)
├── PROMPTS.md                       # Master prompt index
├── DEPLOY.md                        # Deployment guide (free + paid)
├── LOADOUT.md                       # Workspace manifest
│
├── learning-hub/                    # Self-learning system (The Diamond)
│   ├── ERRORS.md                    # Error log — never repeat mistakes
│   ├── LEARNINGS.md                 # What worked, patterns confirmed
│   ├── SELF-UPDATE.md               # Auto-update protocol
│   ├── techniques/                  # Reusable automation patterns (5+)
│   └── automations/CATALOG.md       # Registry of everything built
│
├── Social-Media-Automations/        # Post to LinkedIn, X, Instagram, YouTube
│   ├── tools/post_all.py            # One command, all 4 platforms
│   ├── tools/content_engine.py      # AI content generation
│   ├── tools/linkedin_poster.py     # LinkedIn direct API
│   ├── tools/blotato_poster.py      # X + Instagram + YouTube via Blotato
│   └── ...
│
├── AI_News_Telegram_Bot/            # Daily AI news digest to Telegram
├── Salesforce_PDF_Filler/           # Auto-fill PDFs from CRM data
├── Blotato_Social_Media/            # YouTube → social media repurposer
├── Scrape Data form Google Map/     # Google Maps lead scraper
│
├── _template/                       # Auto-scaffold for new projects
├── scripts/
│   ├── new-automation.sh            # Create new project from template
│   └── sync-obsidian.sh             # Sync learning hub to Obsidian
│
├── student-starter-kit/             # Distributable kit
│   ├── agents/                      # 10 AI agent definitions
│   ├── skills/                      # 15 automation skills
│   └── coding-rules/               # 15 engineering standards
│
├── Agentic Workflow for Students/   # Agentic engine framework
│   ├── shared/                      # Security modules (validator, sandbox, cost tracker)
│   ├── config/                      # LLM routing, settings
│   └── tools/                       # Tool + workflow templates
│
├── prompts/                         # Global prompt library (12+)
├── .cursorrules                     # Cursor (synced)
├── .clinerules/                     # Cline (synced)
├── .gemini/                         # Gemini (synced)
└── sync.sh                          # Sync CLAUDE.md to all tool configs
```

---

## Automation Projects

| # | Project | What It Does | Tech |
|---|---------|-------------|------|
| 1 | [**Social-Media-Automations**](Social-Media-Automations/) | Post to LinkedIn, X, Instagram, YouTube from one command with AI content + image generation | Python, LinkedIn API, Blotato, Euri (Nano Banana 2) |
| 2 | [**AI News Telegram Bot**](AI_News_Telegram_Bot/) | Daily AI news digest — fetches, ranks with LLM, delivers to Telegram | Python, NewsAPI, Euri, Telegram Bot API |
| 3 | [**Salesforce PDF Filler**](Salesforce_PDF_Filler/) | Auto-fill PDF forms from Salesforce data (CLI + API + n8n) | Python, FastAPI, simple-salesforce, fillpdf |
| 4 | [**Blotato Social Media**](Blotato_Social_Media/) | YouTube video → platform-optimized posts with custom visuals | Python, Blotato API |
| 5 | [**Google Maps Lead Scraper**](Scrape%20Data%20form%20Google%20Map/) | Scrape business leads by industry + location, enrich with email | Python, Apify, Outscraper, Hunter.io |

---

## Learning Hub (The Diamond)

The system learns from its own mistakes:

```
Agent builds --> hits error --> fixes it
  --> Logs to learning-hub/ERRORS.md
    --> Next session reads it
      --> Never repeats the same mistake
```

- **9 errors logged** — Blotato API quirks, LinkedIn upload fix, API version expiry
- **5 technique files** — webhooks, deployment, bots, API integration, cost optimization
- **Full automation catalog** — every project indexed with tech, phase, reusable parts

---

## Agents (10)

| Agent | Use For |
|-------|---------|
| **backend-builder** | FastAPI APIs, Python services |
| **frontend-builder** | Next.js, React, Tailwind |
| **code-reviewer** | Bug & security review |
| **test-runner** | Run/write tests |
| **deployer** | Vercel, AWS, Docker, CI/CD |
| **db-architect** | Schema, migrations, RLS |
| **mcp-builder** | MCP servers for any API |
| **api-integrator** | OAuth, webhooks, REST/GraphQL |
| **security-auditor** | OWASP Top 10, secrets audit |
| **researcher** | Codebase exploration |

## Skills (15)

| Category | Skills |
|----------|--------|
| **Content & Media** | video-edit, image-to-video, nano-banana-images, handdrawn-diagram, excalidraw-diagram, excalidraw-visuals, gamma-presentation |
| **Infrastructure** | modal-deploy, add-webhook, local-server, design-website |
| **Browser & Voice** | ghost-browser, whisper-voice |
| **Security & Meta** | guardrail-pipeline, skill-builder |

## Coding Rules (15)

| # | Rule | Enforces |
|---|------|----------|
| 00 | Global Architect | Clean architecture, separation of concerns |
| 10 | Backend FastAPI | Thin routes, services, repositories |
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
| 90 | DevOps | Docker, CI/CD, rollback-safe |
| 99 | Response Style | Production code only |

---

## Deployment Guide

Full free + paid options in [`DEPLOY.md`](DEPLOY.md):

| Use Case | Free Option | Paid Option |
|----------|------------|-------------|
| Bots | Koyeb (always-on) | Railway ($5/mo) |
| Webhooks/APIs | Koyeb, Vercel | Railway |
| n8n Self-Hosted | Oracle Cloud Free | Hostinger ($5/mo) |
| Scheduled Tasks | GitHub Actions | Any VPS |
| AI/GPU | Modal ($30/mo credit) | Modal Pro |
| Frontend | Vercel Hobby | Vercel Pro |

---

## Quick Start

```bash
# Clone
git clone https://github.com/aiagentwithdhruv/Euron-Future-Proof-Automation.git
cd Euron-Future-Proof-Automation

# Open in Claude Code / Cursor / Cline — CLAUDE.md loads automatically

# Create a new automation project
bash scripts/new-automation.sh "My-Bot-Name"

# Sync rules to all AI tools
./sync.sh

# Sync learning hub to Obsidian
bash scripts/sync-obsidian.sh
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), async-first |
| Frontend | Next.js + React + Tailwind CSS |
| Database | PostgreSQL / Supabase |
| AI Models | Euri (free), OpenRouter, Claude, OpenAI, Gemini |
| Automation | n8n, MCP, Blotato |
| Deployment | Vercel, Koyeb, Railway, Modal, AWS |

---

## Bootcamp

This repo powers the **Future-Proof AI Automation Bootcamp** on [Euron](https://euron.one):

- 8 Phases | 19 Weeks | 18+ deployed projects
- Instructor: Dhruv Tomar ([AIwithDhruv](https://aiwithdhruv.com))
- Sat & Sun, 8-10 PM IST

---

## License

MIT
