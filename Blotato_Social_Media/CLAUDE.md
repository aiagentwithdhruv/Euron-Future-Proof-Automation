# repurpose-youtube-video

Turn any YouTube video into platform-optimized social media posts for LinkedIn, Instagram, and X — with custom visuals — powered by the Blotato API.

---

## Architecture

```
Blotato_Social_Media/
├── CLAUDE.md               # This file — skill rules for Claude Code
├── prompt.md               # All prompt templates (for iteration)
├── run.py                  # CLI entry point
├── requirements.txt        # Python dependencies
├── .env                    # BLOTATO_API_KEY (gitignored)
├── .gitignore
│
├── src/                    # Core Python package
│   ├── __init__.py
│   ├── config.py           # Environment, paths, constants
│   ├── client.py           # Blotato API client (HTTP + polling)
│   ├── prompts.py          # All prompt templates (editable)
│   ├── extractor.py        # YouTube content extraction
│   ├── generator.py        # Post text + visual generation
│   ├── publisher.py        # Publishing to platforms
│   └── logger.py           # Posts log (MD + JSON)
│
└── data/                   # Runtime data (logs, drafts)
    ├── posts_log.md        # Published posts log (markdown table)
    ├── posts_log.json      # Published posts log (JSON)
    └── drafts.json         # Generated drafts for review (gitignored)
```

---

## Workflow

```
YouTube URL
    |
    v
[1] EXTRACT (src/extractor.py)
    Blotato /source-resolutions-v3 --> title + transcript + tags
    |
    v
[2] GENERATE POSTS (src/generator.py)
    Prompt templates from src/prompts.py
    ├── LinkedIn: professional, insightful, 1300 chars, hashtags
    ├── X: punchy, bold, 280 chars max
    └── Instagram: visual-first, short caption, 15-20 hashtags
    |
    v
[3] GENERATE VISUALS (src/generator.py)
    Blotato /videos/from-templates
    ├── LinkedIn: 1200x627, navy/white, clean
    ├── X: 1600x900, high contrast, bold
    └── Instagram: 1080x1080, vibrant, aesthetic
    |
    v
[4a] DRAFT MODE (default)
     Save to data/drafts.json --> user reviews --> python run.py --publish-drafts

[4b] AUTO-PUBLISH (--publish flag)
     Blotato /posts --> poll status --> log to data/posts_log.md
```

---

## Usage

```bash
# Install
pip install -r requirements.txt

# Draft mode (review before publishing)
python run.py https://www.youtube.com/watch?v=VIDEO_ID

# Publish reviewed drafts
python run.py --publish-drafts

# Auto-publish directly
python run.py https://www.youtube.com/watch?v=VIDEO_ID --publish

# Specific platforms only
python run.py https://www.youtube.com/watch?v=VIDEO_ID --platforms linkedin,x

# Schedule for later
python run.py https://www.youtube.com/watch?v=VIDEO_ID --publish --schedule "2026-03-25T15:00:00Z"
```

---

## Blotato API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/users/me` | GET | Verify API key |
| `/users/me/accounts` | GET | List connected social accounts |
| `/users/me/accounts/{id}/subaccounts` | GET | Get LinkedIn page IDs |
| `/source-resolutions-v3` | POST | Extract YouTube video content |
| `/source-resolutions-v3/{id}` | GET | Poll extraction status |
| `/videos/templates` | GET | List visual templates |
| `/videos/from-templates` | POST | Generate platform visuals |
| `/videos/creations/{id}` | GET | Poll visual generation status |
| `/posts` | POST | Create/publish/schedule posts |
| `/posts/{id}` | GET | Poll publishing status |

Auth: `blotato-api-key` header. Base URL: `https://backend.blotato.com/v2`

---

## Rules for Claude Code

1. **Never expose or log the API key** — it lives only in `.env`
2. **All prompts live in `src/prompts.py`** — edit there, not scattered across files
3. **Logs go to `data/`** — never write runtime data to project root
4. **Draft-first by default** — only auto-publish when `--publish` is explicit
5. **Platform names**: use `linkedin`, `x`, `instagram` (lowercase) throughout
6. **Blotato scheduling**: `scheduledTime` goes at payload root, NOT inside `post` object
7. **Polling is required** — all Blotato operations are async; always poll for completion
8. **LinkedIn pages**: fetch subaccounts for company page posting; omit `pageId` for personal
