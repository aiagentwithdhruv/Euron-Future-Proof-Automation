# AI News Telegram Bot

Get the top 5 AI news stories delivered to your Telegram — every day, fully automated. Zero cost.

```
NewsAPI + RSS feeds + Tavily  →  LLM ranks top 5  →  Telegram message
```

---

## What You'll Learn

This project teaches the **agentic workflow pattern** — the same architecture used in production AI automation systems:

1. **Separation of reasoning and execution** — AI thinks, Python scripts execute
2. **Tool composition** — small, reusable scripts chained together
3. **Config-driven design** — change behavior without changing code
4. **Security by default** — secret masking, input sanitization, budget limits
5. **Observability** — every run is logged automatically

> This is not a toy script. It's a production-grade automation built the way real systems are built.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  AGENT (Claude Code / Cursor / You)                  │
│  Reads workflow → Picks tools → Executes → Observes  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  WORKFLOW  (workflows/daily-ai-news.md)              │
│  Markdown SOP — steps, tools, error handling, cost   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  TOOLS  (tools/*.py)                                 │
│  4 deterministic Python scripts — typed I/O, errors  │
└─────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
[1] fetch_news.py    →  NewsAPI + 4 RSS feeds + Tavily  →  .tmp/raw_news.json (30+ articles)
        ↓
[2] rank_news.py     →  Euri LLM ranks top 5 (or keyword fallback)  →  .tmp/ranked_news.json
        ↓
[3] format_message.py →  Telegram MarkdownV2 with links  →  .tmp/telegram_message.txt
        ↓
[4] send_telegram.py  →  Bot API delivery  →  Your Telegram
```

---

## Quick Start

### Step 1: Clone

```bash
git clone https://github.com/aiagentwithdhruv/ai-news-telegram-bot.git
cd ai-news-telegram-bot
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Get Your API Keys (All Free)

| # | Service | What For | Free Tier | Where to Get |
|---|---------|----------|-----------|-------------|
| 1 | **Telegram Bot** | Send messages | Unlimited | Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` |
| 2 | **NewsAPI** | Fetch AI news | 100 requests/day | [newsapi.org](https://newsapi.org) → Sign up → Copy key |
| 3 | **Euri** (optional) | AI-powered ranking | 200K tokens/day | [euron.one](https://euron.one) → Dashboard → API Key |
| 4 | **Tavily** (optional) | Extra news source | 1000 requests/month | [tavily.com](https://tavily.com) → Sign up → Copy key |

### Step 4: Set Up Your `.env`

```bash
cp .env.example .env
```

Open `.env` and paste your keys:

```env
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id
NEWSAPI_KEY=your-newsapi-key
EURI_API_KEY=your-euri-key          # optional
TAVILY_API_KEY=your-tavily-key      # optional
```

**How to find your Telegram Chat ID:**
1. Send any message to your bot on Telegram
2. Open this URL in your browser: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"chat":{"id": 123456789}` — that number is your chat ID

### Step 5: Run

```bash
python main.py
```

Check your Telegram. Done.

---

## CLI Options

```bash
python main.py                          # Full pipeline — fetch, rank, format, send
python main.py --sources newsapi,rss    # Only these sources (skip Tavily)
python main.py --top 3                  # Top 3 instead of top 5
python main.py --no-llm                 # Skip AI ranking, use keyword scoring
python main.py --dry-run                # Preview message without sending
python main.py --plain                  # Send as plain text (no markdown)
```

---

## Project Structure

```
ai-news-telegram-bot/
│
├── main.py                   ← Run this (orchestrates the full pipeline)
├── CLAUDE.md                 ← Agent instructions (the brain)
├── README.md                 ← You are here
├── requirements.txt          ← Python dependencies
├── .env.example              ← Template for API keys
├── .gitignore                ← Keeps secrets and temp files out of git
│
├── tools/                    ← One script per job (the hands)
│   ├── fetch_news.py         ← Fetch from NewsAPI + RSS + Tavily
│   ├── rank_news.py          ← LLM ranking or keyword fallback
│   ├── format_message.py     ← Telegram MarkdownV2 formatting
│   ├── send_telegram.py      ← Send via Telegram Bot API
│   ├── registry.yaml         ← Tool schemas (inputs/outputs/cost)
│   └── _template.py          ← Template for creating new tools
│
├── workflows/                ← Markdown SOPs (the plan)
│   ├── daily-ai-news.md      ← Step-by-step workflow for this automation
│   └── _template.md          ← Template for creating new workflows
│
├── shared/                   ← Security & infrastructure (the shield)
│   ├── env_loader.py         ← Load + validate .env
│   ├── logger.py             ← JSON logging with secret masking
│   ├── secrets.py            ← API key redaction
│   ├── sanitize.py           ← Input sanitization
│   ├── sandbox.py            ← Restrict file write paths
│   ├── tool_validator.py     ← Block dangerous code (eval, exec, os.system)
│   ├── retry.py              ← Exponential backoff for transient errors
│   └── cost_tracker.py       ← Budget enforcement ($5/day, $2/run)
│
├── config/                   ← Configuration (the settings)
│   ├── models.yaml           ← LLM routing (Euri → OpenRouter → keyword)
│   ├── settings.yaml         ← News sources, categories, limits
│   └── credentials.yaml      ← Which tool needs which API key
│
├── runs/                     ← Auto-generated run logs (the memory)
└── .tmp/                     ← Intermediate files (disposable)
```

---

## News Sources

| Source | Type | Articles | What It Covers |
|--------|------|----------|----------------|
| **NewsAPI** | REST API | ~10-20/day | 80,000+ sources — broad AI coverage |
| **TechCrunch AI** | RSS feed | ~5/day | Startups, funding, product launches |
| **The Verge AI** | RSS feed | ~5/day | Consumer AI, big tech moves |
| **Ars Technica** | RSS feed | ~5/day | Deep technical analysis |
| **MIT Tech Review** | RSS feed | ~5/day | Research, policy, long-term trends |
| **Tavily** | AI search | ~10/day | Real-time AI-specific search |

---

## How Ranking Works

### With Euri API (recommended — free)
The LLM reads all fetched articles and picks the top 5 based on:
- Importance and impact on the AI industry
- Recency and timeliness
- Source credibility
- Diversity of topics (avoids 5 articles about the same thing)

Each pick gets a 1-2 sentence summary written for a tech-savvy audience.

### Without Euri (keyword fallback)
Articles are scored using:
- Keyword frequency (AI terms like "LLM", "GPT", "deployment", etc.)
- Source authority (MIT Tech Review scores higher than unknown blogs)
- Recency (articles with timestamps get a boost)

Both methods work. The LLM version is smarter.

---

## Security (Built In)

| Protection | What It Does |
|------------|-------------|
| **Secret masking** | API keys are auto-redacted in all logs |
| **`.env` only** | Secrets never appear in code, output, or git |
| **Tool validation** | New tools are scanned for `eval()`, `exec()`, `os.system()` before running |
| **Input sanitization** | Shell metacharacters stripped from all inputs |
| **File sandboxing** | Tools can only write to `.tmp/` and `runs/` — nowhere else |
| **Budget limits** | $5/day, $2/run — prevents accidental API cost overruns |
| **Telegram sanitization** | No HTML/script injection in messages |

You don't configure any of this. It works out of the box.

---

## Make It Run Daily (Scheduling)

### Option 1: Cron (macOS / Linux)

```bash
crontab -e
```

Add this line (runs every day at 9 AM):

```
0 9 * * * cd /path/to/ai-news-telegram-bot && python3 main.py >> /tmp/ai-news.log 2>&1
```

### Option 2: n8n / Make / Zapier

Set up a scheduled trigger that runs `python main.py` on your server at your preferred time.

### Option 3: GitHub Actions (Free)

Add a workflow file to run it on a schedule from the cloud — no server needed.

---

## Extending This Project

### Add a new news source
1. Edit `tools/fetch_news.py` — add a new fetch function
2. Update `config/settings.yaml` with the source config
3. Update `config/credentials.yaml` if it needs an API key

### Change the number of articles
```bash
python main.py --top 3    # or --top 10
```

### Send to a Telegram channel instead of chat
1. Create a channel on Telegram
2. Add your bot as admin
3. Set `TELEGRAM_CHAT_ID=@yourchannel` in `.env`

### Add a new tool
```bash
cp tools/_template.py tools/my_new_tool.py
# Edit it, then add schema to tools/registry.yaml
```

### Create a new workflow
```bash
cp workflows/_template.md workflows/my-workflow.md
# Define objective, inputs, steps, tools, outputs, error handling
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NEWSAPI_KEY is required` | Add your key to `.env` |
| `Telegram 403 Forbidden` | Send `/start` to your bot first, then re-check chat ID |
| `Telegram 400 Bad Request` | Markdown parsing issue — try `--plain` flag |
| `NewsAPI 429 Too Many Requests` | Free tier limit (100/day) — wait 24 hours or use `--sources rss` only |
| `LLM timeout` | Euri might be slow — add `--no-llm` to use keyword ranking |
| `No articles found` | Check your internet connection, or try different `--sources` |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| News fetching | `requests` + `feedparser` |
| LLM ranking | OpenAI SDK → Euri API (free) |
| Telegram | Bot API (free, unlimited) |
| Config | `.env` + YAML files |
| Security | Custom `shared/` modules |

---

## What's Next

This is the base version. In the next class, we'll add:
- More news sources and categories
- Scheduled deployment on a server
- Multi-channel support (Telegram + Email + Slack)
- Historical tracking and trend analysis

---

Built with [Claude Code](https://claude.ai/claude-code) as part of the **[Future-Proof AI Automation Bootcamp](https://euron.one)** by [AIwithDhruv](https://github.com/aiagentwithdhruv).

## License

MIT
