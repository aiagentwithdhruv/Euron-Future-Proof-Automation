---
name: github-actions-deploy
description: Deploy any automation to run on schedule using GitHub Actions. Use when user asks to deploy with cron, schedule an automation, run code automatically, or deploy for free.
argument-hint: "[project-path] [schedule]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# GitHub Actions Deployment

## Goal
Deploy any Python automation to run on a schedule (cron) using GitHub Actions. Free for public repos. No server needed.

## When to Use
- Daily/hourly/weekly automated tasks (social media posting, news digest, scraping, reports)
- Anything that runs, does its job, and exits (not a persistent bot)
- Student-friendly: $0 cost, no infrastructure

## Prerequisites
- GitHub account
- Project in a git repo
- `requirements.txt` in the project

## Step-by-Step

### 1. Create the workflow file
```bash
mkdir -p .github/workflows
```

### 2. Write the workflow
Create `.github/workflows/automate.yml`:

```yaml
name: Run Automation

on:
  schedule:
    # Runs daily at 9:00 AM UTC (2:30 PM IST)
    - cron: '0 9 * * *'
  workflow_dispatch:  # Manual trigger button in GitHub UI

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run automation
        run: python tools/post_all.py --linkedin "$LINKEDIN_TEXT"
        env:
          EURI_API_KEY: ${{ secrets.EURI_API_KEY }}
          LINKEDIN_ACCESS_TOKEN: ${{ secrets.LINKEDIN_ACCESS_TOKEN }}
          LINKEDIN_PERSON_URN: ${{ secrets.LINKEDIN_PERSON_URN }}
          BLOTATO_API_KEY: ${{ secrets.BLOTATO_API_KEY }}
          BLOTATO_X_ID: ${{ secrets.BLOTATO_X_ID }}
          BLOTATO_INSTAGRAM_ID: ${{ secrets.BLOTATO_INSTAGRAM_ID }}
          BLOTATO_YOUTUBE_ID: ${{ secrets.BLOTATO_YOUTUBE_ID }}
```

### 3. Add secrets to GitHub
Go to: Repo → Settings → Secrets and variables → Actions → New repository secret

Add each key from `.env` as a secret. NEVER hardcode keys in the workflow file.

### 4. Push to GitHub
```bash
git add .github/workflows/automate.yml
git commit -m "Add GitHub Actions deployment"
git push origin main
```

### 5. Test manually
Go to: Repo → Actions tab → "Run Automation" → "Run workflow" button

### 6. Verify
Check the Actions tab for green checkmark. Check the target platform (LinkedIn, Telegram, etc.) for output.

## Common Cron Schedules

| Schedule | Cron Expression |
|----------|----------------|
| Every hour | `0 * * * *` |
| Daily at 9 AM UTC | `0 9 * * *` |
| Twice daily (9 AM + 6 PM UTC) | `0 9,18 * * *` |
| Every Monday at 9 AM | `0 9 * * 1` |
| Every 15 minutes | `*/15 * * * *` |
| First of every month | `0 0 1 * *` |

## Gotchas

1. **Cron is UTC only** — convert to your timezone. IST = UTC + 5:30.
2. **Minimum interval is 5 minutes** — GitHub doesn't support faster.
3. **Schedule can be delayed** — GitHub may delay runs by 5-15 min during peak load.
4. **Max 6 hours per job** — if your automation takes longer, split it.
5. **Public repos = unlimited minutes** — private repos get 2,000 min/month free.
6. **Secrets are NOT available in forks** — only in the original repo.

## Debugging

```bash
# Check logs: Repo → Actions → click the failed run → click the job → read logs
# Re-run: Click "Re-run all jobs" button
# Test locally first: python tools/post_all.py (always test before pushing)
```

---

## Schema

### Inputs
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_path` | string | No | Path to the project (default: current directory) |
| `schedule` | string | No | Cron expression (default: daily at 9 AM UTC) |
| `script` | string | Yes | Python script to run (e.g., `tools/post_all.py`) |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `workflow_file` | file_path | Created `.github/workflows/automate.yml` |
| `deployed` | boolean | Whether push to GitHub succeeded |

### Credentials
| Name | Source |
|------|--------|
| All project `.env` keys | GitHub Repo → Settings → Secrets |

### Composable With
Any automation project — Social Media, Telegram Bot, Scraper, PDF Filler, etc.

### Cost
Free (public repos), 2,000 min/month (private repos)
