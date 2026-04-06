# AI News Telegram Bot — Agent Automation

You operate inside an **agentic workflow system** that separates reasoning from execution. You think. Code executes. That separation is what makes this reliable.

---

## What This Does

Fetches the latest AI news daily from multiple sources, uses an LLM to rank and summarize the top 5, and sends a formatted digest to Telegram. Fully automated — runs once and delivers.

```
[1] Fetch news from 3+ sources (NewsAPI, RSS feeds, Tavily)
        ↓
[2] LLM ranks & picks top 5 (via Euri API — free)
        ↓
[3] Format as Telegram message (clean, readable, linked)
        ↓
[4] Send to Telegram chat/channel (Bot API — free)
        ↓
[5] Log the run (what was sent, when, cost)
```

---

## Architecture: 3 Layers

```
┌─────────────────────────────────────────────────────┐
│  AGENT (You)                                         │
│  Read workflow → Pick tools → Execute → Observe      │
│  → Re-plan if failed → Log run → Deliver output      │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  WORKFLOWS  (workflows/*.md)                         │
│  Markdown SOPs — objective, inputs, steps, tools,    │
│  outputs, error handling, cost estimate              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  TOOLS  (tools/*.py)                                 │
│  Deterministic Python scripts. Each has a schema.    │
│  Inputs typed. Outputs typed. Errors handled.        │
└─────────────────────────────────────────────────────┘
```

---

## First Run Setup

When the user opens this project for the first time, check if `.env` exists. If it doesn't:

1. Copy `.env.example` to `.env`
2. Ask the user for their keys:
   - **Telegram Bot Token** — "Create a bot via @BotFather on Telegram, paste the token"
   - **Telegram Chat ID** — "Send a message to your bot, then visit https://api.telegram.org/bot<TOKEN>/getUpdates to find your chat_id"
   - **NewsAPI Key** — "Get it free at newsapi.org (100 requests/day)"
   - **Euri API Key** (optional) — "Get it free at euron.one for AI ranking (200K tokens/day)"
3. Write the keys into `.env`
4. Confirm: "Setup done. Run `python main.py` to get your first AI news digest."

---

## File Structure

```
AI_News_Telegram_Bot/
├── CLAUDE.md                 # These instructions (you're reading this)
├── .env                      # API keys (NEVER commit, NEVER log)
├── .env.example              # Template showing required keys
├── .gitignore
├── README.md                 # GitHub-facing docs
├── requirements.txt          # Python dependencies
├── main.py                   # CLI entry point
│
├── config/
│   ├── models.yaml           # LLM routing (Euri primary)
│   ├── settings.yaml         # Global settings (retries, limits)
│   └── credentials.yaml      # Tool → env var mapping
│
├── workflows/
│   ├── _template.md          # Template for new workflows
│   └── daily-ai-news.md      # Main workflow SOP
│
├── tools/
│   ├── _template.py          # Template for new tools
│   ├── registry.yaml         # Tool registry (schemas)
│   ├── fetch_news.py         # Fetch AI news from multiple sources
│   ├── rank_news.py          # LLM ranks & summarizes top 5
│   ├── format_message.py     # Format for Telegram markdown
│   └── send_telegram.py      # Send via Telegram Bot API
│
├── shared/
│   ├── __init__.py
│   ├── logger.py             # Structured logging (JSON, secret-masked)
│   ├── retry.py              # Retry with exponential backoff
│   ├── cost_tracker.py       # API cost tracking + budget limits
│   ├── env_loader.py         # Load and validate .env
│   ├── secrets.py            # Mask API keys in logs and output
│   ├── sanitize.py           # Input sanitization
│   ├── sandbox.py            # Restrict file write paths
│   └── tool_validator.py     # Scan tools for dangerous imports
│
├── runs/                     # Run logs (auto-generated)
└── .tmp/                     # Intermediate files (disposable)
```

---

## How You Operate

### 1. Receive a task
1. **Check if `.env` exists** — if not, run First Run Setup
2. **Check workflows/ first** — is there a workflow for this?
3. **If yes** — read the workflow, gather inputs, execute tools in sequence
4. **If no** — compose from existing tools or build new ones

### 2. Execute tools, don't do the work yourself

**CRITICAL RULE:** Never try to accomplish execution tasks (API calls, data processing, message sending) by writing code inline. Always use or create a tool in `tools/`.

```
BAD:  You write a 50-line script inline to call NewsAPI
GOOD: You run `python tools/fetch_news.py --sources newsapi,rss --limit 20`
```

### 3. Handle failures intelligently

When a tool fails:
1. **Read the full error** — don't guess
2. **Diagnose** — API issue, rate limit, auth problem, bad input?
3. **Fix the tool** — edit `tools/<name>.py`
4. **Re-run** — verify the fix
5. **Update the workflow** — add the edge case
6. **Log it** — append to `runs/`

### 4. Log every run

After completing a workflow, create:
```
runs/YYYY-MM-DD-daily-ai-news.md
```

---

## News Sources (Priority Order)

| Source | Type | Free Tier | Best For |
|--------|------|-----------|----------|
| **NewsAPI** | REST API | 100 req/day | Broad AI news from 80K+ sources |
| **RSS Feeds** | XML parsing | Unlimited | TechCrunch AI, The Verge, Ars Technica |
| **Tavily** | AI search | 1000 req/mo | Real-time AI-specific search |

Start with NewsAPI + RSS. Add Tavily only if the user has a key.

---

## LLM Routing

| Priority | Provider | Use For | Cost |
|----------|----------|---------|------|
| 1 | **Euri** (euron.one) | Rank & summarize news | Free 200K tokens/day |
| 2 | **OpenRouter** | Fallback if Euri is down | Pay-per-use |

If no LLM key is configured, fall back to a simple keyword-scoring algorithm (no AI needed).

---

## Security Guardrails

These rules are **non-negotiable**:

1. **Secrets stay in `.env`** — nowhere else, ever. Never log, print, or embed API keys.
2. **All logs are secret-masked** — the logger redacts API keys and tokens automatically.
3. **Validate every new tool before execution** — run `shared/tool_validator.py` first.
4. **Never use dangerous functions** — `exec()`, `eval()`, `os.system()` are BLOCKED.
5. **Sanitize all inputs** — use `shared/sanitize.py` before passing to tools.
6. **Budget enforcement** — daily limit $5, per-run limit $2. Check before paid API calls.
7. **Telegram messages are sanitized** — no raw HTML injection, escape user content.
8. **Rate limiting** — respect NewsAPI (100/day), Telegram (30 msgs/sec), Tavily (1000/mo).

---

## Rules

1. **Tools first, code second** — always check tools/ before writing inline
2. **Workflows are instructions** — don't delete or overwrite without asking
3. **Paid API calls need approval** — confirm before retrying tools that cost money
4. **Secrets stay in .env** — nowhere else, ever
5. **Log every run** — observability compounds over time
6. **Update on failure** — fix tool → verify → update workflow → log
7. **One tool, one job** — tools should do one thing well
8. **Composition over complexity** — chain simple tools, don't build mega-scripts
9. **Telegram formatting** — use MarkdownV2, escape special chars, keep messages under 4096 chars
10. **News deduplication** — same story from multiple sources = one entry

---

## Bottom Line

You sit between intent (workflows) and execution (tools). Your job: fetch news, rank it, format it, send it, log it. Every day. Reliably.

Think clearly. Execute precisely. Learn constantly.
