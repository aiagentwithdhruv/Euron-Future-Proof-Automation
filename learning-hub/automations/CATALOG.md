# Automation Catalog

> Registry of every automation built in this bootcamp.
> Updated after each build session. Used for: teaching, reuse, portfolio, client demos.

---

## Complete Automations

### 1. AI News Telegram Bot
| Field | Detail |
|-------|--------|
| **Folder** | `AI_News_Telegram_Bot/` |
| **What** | Fetches top 5 AI news daily, ranks with LLM, delivers to Telegram |
| **Phase** | 3 (No-Code Automation) |
| **Agentic Loop** | Sense: RSS/NewsAPI feeds -> Think: LLM ranks relevance -> Decide: Top 5 stories -> Act: Format + send to Telegram -> Learn: _(future: track engagement)_ |
| **Tech** | Python, requests, feedparser, OpenAI SDK (Euri), Telegram Bot API |
| **APIs** | NewsAPI (free), Euri (free), Telegram (free), Tavily (optional) |
| **Deploy** | Local cron, GitHub Actions, or n8n |
| **Status** | Complete |
| **Reusable Parts** | News fetching tool, LLM ranking prompt, Telegram delivery tool |

### 2. Salesforce PDF Filler
| Field | Detail |
|-------|--------|
| **Folder** | `Salesforce_PDF_Filler/` |
| **What** | Reads Salesforce data, auto-fills PDF forms. CLI + API + n8n modes. |
| **Phase** | 4 (AI-Powered Autonomous Systems) |
| **Agentic Loop** | Sense: Salesforce data change -> Think: Map fields to PDF -> Decide: Fill + validate -> Act: Generate PDF + upload -> Learn: Log mapping accuracy |
| **Tech** | Python, fillpdf, simple-salesforce, FastAPI, Click CLI, n8n |
| **APIs** | Salesforce REST API (OAuth2), PDF AcroForm |
| **Deploy** | CLI, FastAPI service, n8n workflow, Docker |
| **Status** | Complete — dual-method (code + n8n) |
| **Reusable Parts** | Salesforce client, PDF filler, field mapper, FastAPI template |

### 3. Blotato Social Media Repurposer
| Field | Detail |
|-------|--------|
| **Folder** | `Blotato_Social_Media/` |
| **What** | Transforms YouTube videos into platform-optimized social posts with AI visuals |
| **Phase** | 6 (Industry Playbooks — Marketing) |
| **Agentic Loop** | Sense: YouTube URL -> Think: Extract content, choose platform styles -> Decide: Generate copy + visuals per platform -> Act: Publish or save drafts -> Learn: Track engagement |
| **Tech** | Python, requests, YAML config |
| **APIs** | Blotato API v2 (extraction, visual gen, publishing) |
| **Deploy** | Local CLI, cron scheduled |
| **Status** | Complete |
| **Reusable Parts** | YouTube extractor, multi-platform publisher, prompt templates |

### 4. Google Maps Lead Scraper
| Field | Detail |
|-------|--------|
| **Folder** | `Scrape Data form Google Map/` |
| **What** | Scrapes business leads from Google Maps by industry + location, enriches with email |
| **Phase** | 3 (No-Code Automation — Data) |
| **Agentic Loop** | Sense: Search query (industry + city) -> Think: Build optimal search -> Decide: Apify or Outscraper -> Act: Scrape + enrich + export Excel -> Learn: Track hit rates |
| **Tech** | Python, apify-client, outscraper, pyhunter, pandas, openpyxl, gspread |
| **APIs** | Apify ($5 free credits), Outscraper (500 free), Hunter.io (25 free/mo), Google Sheets |
| **Deploy** | Local CLI, batch processing |
| **Status** | Complete |
| **Reusable Parts** | Query builder, multi-scraper fallback pattern, Excel exporter |

### 5. Agentic Workflow Engine
| Field | Detail |
|-------|--------|
| **Folder** | `Agentic Workflow for Students/` |
| **What** | Code-first framework for building AI automations. Foundation for all other projects. |
| **Phase** | 2 (AI as System Designer — Infrastructure) |
| **Agentic Loop** | Sense: User task -> Think: Check workflows/tools -> Decide: Execute or build new -> Act: Run tools -> Learn: Log run + update on failure |
| **Tech** | Python, FastAPI, YAML config, shared security modules |
| **APIs** | Euri, OpenRouter, OpenAI/Anthropic (configurable) |
| **Deploy** | Local, VPS, Docker, cron/GitHub Actions |
| **Status** | Active framework — all projects build on this |
| **Reusable Parts** | Everything — tool validator, sandbox, cost tracker, logger, retry, templates |

---

## Demo / Educational Projects

### 6. Futuristic Space Shooter
| Field | Detail |
|-------|--------|
| **Folder** | `Futuristic_Space_Shooter/` |
| **What** | Browser-based arcade game. Demonstrates AI-assisted code generation. |
| **Phase** | Educational |
| **Tech** | HTML5, CSS3, JavaScript, GSAP, Canvas API |
| **Deploy** | Static hosting (GitHub Pages, Vercel) |
| **Status** | Complete |

---

## Reusable Components Across Projects

| Component | Found In | Reuse For |
|-----------|----------|-----------|
| Telegram delivery tool | AI_News_Telegram_Bot | Any bot that sends to Telegram |
| LLM ranking/scoring | AI_News_Telegram_Bot | Content curation, lead scoring |
| Salesforce client | Salesforce_PDF_Filler | Any CRM integration |
| PDF fill + flatten | Salesforce_PDF_Filler | Document automation |
| Multi-platform publisher | Blotato_Social_Media | Social media automation |
| Web scraper with fallback | Google Maps Scraper | Any data collection |
| Excel/Sheets exporter | Google Maps Scraper | Any data pipeline |
| Tool validator | Agentic Workflow | Every project (security) |
| Cost tracker | Agentic Workflow | Every project (budget) |
| Sandbox | Agentic Workflow | Every project (security) |
| Retry with backoff | Agentic Workflow | Every API integration |

---

## Phase Coverage

| Phase | Automations Built | Gap |
|-------|------------------|-----|
| 1 - Automation Thinking | _(design phase, no code)_ | N/A |
| 2 - AI System Designer | Agentic Workflow Engine | None |
| 3 - No-Code Automation | News Bot, Maps Scraper | Need: CRM workflow, email sequence |
| 4 - AI-Powered Systems | Salesforce PDF Filler | Need: RAG chatbot, voice agent |
| 5 - Deployment | _(all projects deploy)_ | Need: dedicated deployment demo |
| 6 - Industry Playbooks | Blotato Social Media | Need: E-commerce, healthcare |
| 7 - AI Operator Capstone | _(not started)_ | Full AI Personal Assistant |
| 8 - Career & Business | _(not started)_ | Portfolio, outreach system |

---

**Total Automations:** 6 (5 production + 1 demo)
**Last Updated:** 2026-04-05
