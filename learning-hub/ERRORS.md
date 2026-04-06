# Error Log — Mistakes That Made Us Smarter

> Every error fixed = a mistake we never repeat.
> **Who writes:** Every session, every agent, every build.
> **When to write:** Immediately after fixing any error. Don't wait.

---

## How to Log

```
### [DATE] — [SHORT TITLE]
**Error:** What went wrong
**Cause:** Why it happened
**Fix:** What solved it
**Rule:** One-line rule to prevent this forever
**Applies to:** [project/everyone/specific-tool]
**Category:** [API | Deployment | AI/LLM | Frontend | Backend | Database | Security | n8n | Bots | General]
```

---

## Deployment

### 2026-04-05 — Docker ARM vs AMD64 mismatch
**Error:** `exec format error` — container crashes on cloud deployment
**Cause:** Built Docker image on M-series Mac (ARM64), cloud runs AMD64
**Fix:** `docker build --platform linux/amd64 -t my-app .`
**Rule:** ALWAYS use `--platform linux/amd64` on every Docker build from Mac. No exceptions.
**Applies to:** Everyone
**Category:** Deployment

---

## API

### 2026-04-05 — Blotato platform name is "twitter" not "x"
**Error:** `body.post.content.platform must be one of: "twitter", "instagram", "linkedin"...`
**Cause:** Used `"x"` as platform name. Blotato API still uses `"twitter"`.
**Fix:** Change platform value to `"twitter"` in both `content.platform` and `target.targetType`.
**Rule:** Blotato uses `"twitter"` everywhere. Never use `"x"` in API calls.
**Applies to:** Social-Media-Automations, any Blotato integration
**Category:** API

### 2026-04-05 — Instagram max 5 hashtags via Blotato
**Error:** `Instagram allows a maximum of 5 hashtags per post.`
**Cause:** Sent 7+ hashtags in the caption.
**Fix:** Limit to 5 hashtags max when posting through Blotato.
**Rule:** Blotato enforces max 5 hashtags for Instagram. Count before posting.
**Applies to:** Social-Media-Automations
**Category:** API

### 2026-04-05 — YouTube Blotato target needs title + privacyStatus + shouldNotifySubscribers
**Error:** `body.post.target must have required property 'title'` then `'shouldNotifySubscribers'`
**Cause:** YouTube target object needs 3 extra fields beyond `targetType`.
**Fix:** Add `title`, `privacyStatus` ("public"/"private"), and `shouldNotifySubscribers` (bool) to target.
**Rule:** Blotato YouTube posts require: `{targetType, title, privacyStatus, shouldNotifySubscribers}`.
**Applies to:** Social-Media-Automations
**Category:** API

### 2026-04-05 — LinkedIn image upload needs curl, not Python requests
**Error:** `ReadTimeoutError` on PUT to `www.linkedin.com/dms-uploads/`
**Cause:** Python requests library times out on LinkedIn's upload endpoint. Network/SSL issue.
**Fix:** Use `subprocess.run(["curl", ...])` for the image upload step only.
**Rule:** Always use curl for LinkedIn image uploads. Python requests hangs indefinitely.
**Applies to:** Social-Media-Automations, linkedin_poster.py
**Category:** API

### 2026-04-05 — Blotato base URL is backend.blotato.com, not app.blotato.com
**Error:** DNS resolution failed for `app.blotato.com`
**Cause:** Used wrong domain. Blotato API lives at `backend.blotato.com/v2`.
**Fix:** Use `https://backend.blotato.com/v2` as base URL.
**Rule:** Blotato API = `backend.blotato.com/v2`. Auth header = `blotato-api-key` (not Bearer).
**Applies to:** All Blotato integrations
**Category:** API

### 2026-04-05 — Blotato needs public URLs for media, not local files
**Error:** No file upload endpoint exists on Blotato API
**Cause:** Blotato only accepts URLs in `mediaUrls`, has no `/media/upload` endpoint.
**Fix:** Upload local files to tmpfiles.org first, then pass the direct URL to Blotato.
**Rule:** Host files on tmpfiles.org (free) before passing to Blotato. Use `/dl/` URL format.
**Applies to:** Social-Media-Automations, any Blotato video/image posting
**Category:** API

### 2026-04-05 — Blotato returns postSubmissionId, not id
**Error:** Polling with empty ID returned no meaningful status
**Cause:** Response key is `postSubmissionId`, not `id`.
**Fix:** Use `resp.json().get("postSubmissionId")` for polling.
**Rule:** Poll Blotato posts with `postSubmissionId` from the create response.
**Applies to:** Social-Media-Automations
**Category:** API

### 2026-04-05 — LinkedIn API version 202404 expired
**Error:** `NONEXISTENT_VERSION` for version 20240401
**Cause:** LinkedIn API versions expire. 202404 and 202512 no longer active.
**Fix:** Use `202603` (active as of April 2026).
**Rule:** Check LinkedIn API version every few months. Use format YYYYMM.
**Applies to:** linkedin_poster.py
**Category:** API

---

### 2026-04-06 — GitHub Actions workflows must be at repo ROOT .github/workflows/
**Error:** `could not find any workflows` — workflow file wasn't detected
**Cause:** Placed workflow at `AI_News_Telegram_Bot/.github/workflows/`. GitHub only reads from root `.github/workflows/`.
**Fix:** Always put workflow files at `<repo-root>/.github/workflows/`, never inside subfolders.
**Rule:** GitHub Actions ONLY reads `.github/workflows/` at repo root. Period.
**Applies to:** All GitHub Actions deployments
**Category:** Deployment

### 2026-04-06 — env_loader crashes in CI because no .env file exists
**Error:** `ERROR: .env file not found` in GitHub Actions
**Cause:** `load_env()` called `sys.exit(1)` when `.env` missing. In CI, secrets are env vars, not files.
**Fix:** Check `os.getenv("GITHUB_ACTIONS")` — if set, skip `.env` file requirement.
**Rule:** Always support both `.env` files (local) AND environment variables (CI). Check for `GITHUB_ACTIONS` or `CI` env var.
**Applies to:** Any project deployed to GitHub Actions
**Category:** Deployment

---

## AI/LLM

_(No entries yet)_

---

## Bots

_(No entries yet)_

---

## n8n

_(No entries yet)_

---

## Security

_(No entries yet)_

---

## Backend

_(No entries yet)_

---

## Frontend

_(No entries yet)_

---

## Database

_(No entries yet)_

---

## General

_(No entries yet)_

---

## Stats

| Metric | Count |
|--------|-------|
| Total errors logged | 11 |
| Categories covered | 2/10 |
| Last updated | 2026-04-06 |
