# Social Media Automations

> Post to LinkedIn, X, Instagram, and YouTube from one command — with AI content generation and image creation.

---

## What It Does

AI-powered social media automation that generates platform-optimized content, creates images, and posts to 4 platforms simultaneously. Supports both AI-generated and manual content with a draft-approve-post workflow.

- **LinkedIn** — Direct API v2 (text + images via OAuth2)
- **X / Twitter** — Blotato API (text + images)
- **Instagram** — Blotato API (images + reels/videos)
- **YouTube** — Blotato API (video uploads with title/description)

## Agentic Loop

- **Sense:** User provides topic, text, image, or video
- **Think:** AI generates platform-optimized posts (Euri API, free)
- **Decide:** User reviews drafts and approves
- **Act:** Posts to all platforms via direct APIs + Blotato
- **Learn:** Errors logged to learning hub, never repeated

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys (see .env.example for instructions)
```

### Required Keys

| Key | Where to Get | Free? |
|-----|-------------|-------|
| `EURI_API_KEY` | euron.one → Dashboard → API Key | Yes (200K tokens/day) |
| `LINKEDIN_*` | linkedin.com/developers/apps | Yes |
| `BLOTATO_API_KEY` | blotato.com | Freemium |
| `BLOTATO_*_ID` | Blotato dashboard → account IDs | — |

## Usage

### Post to All Platforms (One Command)

```bash
python tools/post_all.py \
  --linkedin "Your LinkedIn post text" \
  --x "Your tweet (280 chars)" \
  --instagram "Your caption (max 5 hashtags)" \
  --youtube-title "Video Title" \
  --youtube-desc "Video description" \
  --image /path/to/image.png \
  --video /path/to/video.mp4
```

### AI Content Generation

```bash
# Generate posts from a topic
python tools/content_engine.py --topic "AI automation in 2026" --platforms linkedin,x,instagram

# Adapt your text for each platform
python tools/content_engine.py --text "Your raw content" --platforms linkedin,x
```

### Draft → Approve → Post

```bash
# Generate drafts
python tools/content_engine.py --topic "Your topic" --platforms linkedin,x

# Review
python tools/draft_manager.py --list
python tools/draft_manager.py --show <draft_id>

# Approve and post
python tools/draft_manager.py --approve <draft_id>
python tools/draft_manager.py --post <draft_id>
```

### Direct Platform Posting

```bash
# LinkedIn (direct API)
python tools/linkedin_poster.py --text "Hello LinkedIn!" --image photo.jpg

# X/Twitter (Blotato)
python tools/blotato_poster.py --platform x --text "Hello X!"

# Instagram (Blotato + video)
python tools/blotato_poster.py --platform instagram --text "Caption" --video reel.mp4

# YouTube (Blotato + video)
python tools/blotato_poster.py --platform youtube --text "Description" --video video.mp4 --title "Title"
```

## Architecture

```
User Input (topic / text + media)
  |
  v
Content Engine --> AI generates platform-optimized posts (Euri, free)
  |
  v
Draft Storage --> Review and edit before posting
  |
  v
Platform Connectors:
  ├── LinkedIn  → Direct API v2 (curl for image upload)
  ├── X/Twitter → Blotato API (platform: "twitter")
  ├── Instagram → Blotato API (max 5 hashtags, needs media URL)
  └── YouTube   → Blotato API (needs title + privacyStatus + video URL)
  |
  v
Post Log --> Results saved to runs/
```

## File Structure

```
Social-Media-Automations/
├── tools/
│   ├── post_all.py          # One command, all 4 platforms
│   ├── content_engine.py    # AI content generation
│   ├── draft_manager.py     # Draft → approve → post flow
│   ├── linkedin_poster.py   # LinkedIn direct API
│   ├── x_poster.py          # X direct API (OAuth 1.0a)
│   ├── instagram_poster.py  # Instagram Graph API
│   ├── youtube_uploader.py  # YouTube Data API
│   └── blotato_poster.py    # Blotato unified poster
├── config/
│   └── platforms.yaml       # Platform specs (char limits, image sizes)
├── workflows/
│   └── post-to-all.md       # Step-by-step SOP
├── .env.example             # All required API keys
├── requirements.txt
└── CLAUDE.md                # AI assistant rules
```

## Key Learnings (Baked In)

- LinkedIn image uploads need `curl`, not Python `requests` (timeout issue)
- Blotato API lives at `backend.blotato.com/v2`, auth via `blotato-api-key` header
- Blotato uses `"twitter"` not `"x"` as platform name
- Instagram max 5 hashtags via Blotato
- YouTube needs `title`, `privacyStatus`, `shouldNotifySubscribers` in target
- Blotato needs public URLs for media — use tmpfiles.org to host local files
- Poll with `postSubmissionId` from Blotato response
- LinkedIn API version: `202603` (versions expire every few months)

---

**Part of:** [Future-Proof AI Automation Bootcamp](https://euron.one/course/future-proof-ai-automation-bootcamp) by Dhruv Tomar (AIwithDhruv)

**Built:** 2026-04-05
