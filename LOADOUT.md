# Future-Proof AI Automation Bootcamp

> Euron's flagship live bootcamp. Dhruv is the instructor.

---

## Quick Reference

| Field | Value |
|-------|-------|
| **Platform** | Euron (euron.one) |
| **URL** | https://euron.one/course/future-proof-ai-automation-bootcamp |
| **Instructor** | Dhruv Tomar (AIwithDhruv) |
| **Duration** | ~4.5 Months (19 weeks) |
| **Schedule** | Sat & Sun, 8-10 PM IST (2hr live + 1hr doubt clearing) |
| **Starts** | 8th March, 2026 |
| **Price** | Rs.5,000 (incl. taxes) |
| **Structure** | 8 Phases, 19 Weeks, ~95 Subtopics, 18+ Deployed Projects |
| **Capstone** | Full-stack AI Personal Assistant (Phase 7) |
| **Booking** | calendly.com/aiwithdhruv/makeaiworkforyou |

---

## Core Philosophy

**The Agentic Loop:** Sense -> Think -> Decide -> Act -> Learn

**Architecture:** Agent (reasoning) -> Workflows (SOPs) -> Tools (deterministic scripts)

**Tagline:** "This is not a course to learn tools. This is a system to become indispensable in the AI era."

---

## Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Master automation rules (source of truth for all AI tools) |
| `PROMPTS.md` | Master prompt index across all projects |
| `DEPLOY.md` | Student deployment guide (free + paid options) |
| `LOADOUT.md` | This manifest |
| `COURSE-CONTEXT.md` | Full course context for AI assistants |
| `SYLLABUS.md` | Detailed week-by-week syllabus |
| `sync.sh` | Sync CLAUDE.md -> .cursorrules, .clinerules, .gemini |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/new-automation.sh` | Create new project folder from template |
| `sync.sh` | Sync rules to all AI tool configs |

```bash
# Create new automation project
bash scripts/new-automation.sh "My-Bot-Name"

# Sync rules after editing CLAUDE.md
./sync.sh

# Sync learning hub to Obsidian AI Second Brain
bash scripts/sync-obsidian.sh
```

---

## Framework Resources

| Resource | Location | Count |
|----------|----------|-------|
| AI Agents | `student-starter-kit/agents/` | 10 |
| Automation Skills | `student-starter-kit/skills/` | 15 |
| Coding Rules | `student-starter-kit/coding-rules/rules/` | 15 |
| Prompt Templates | `prompts/` | 12+ |
| Agentic Engine | `Agentic Workflow for Students/` | Full framework |
| Project Template | `_template/` | Auto-scaffold |
| **Learning Hub** | `learning-hub/` | Self-learning system |
| Error Log | `learning-hub/ERRORS.md` | Never repeat mistakes |
| Improvement Log | `learning-hub/LEARNINGS.md` | What worked |
| Techniques | `learning-hub/techniques/` | 5+ reusable patterns |
| Automation Catalog | `learning-hub/automations/CATALOG.md` | All projects indexed |

---

## 8 Phases Overview

| Phase | Name | Weeks | Focus |
|-------|------|-------|-------|
| 1 | Automation Thinking | 1-2 | Business audit, systems design, Agentic Loop |
| 2 | AI as System Designer | 3-4 | AI-first dev, prompt engineering, rapid prototyping |
| 3 | No-Code Automation | 5-7 | APIs, webhooks, multi-channel, CRM, databases |
| 4 | AI-Powered Systems | 8-10 | AI routing, RAG, agents, voice AI |
| 5 | Deployment & Production | 11-12 | VPS, Docker, monitoring, cost optimization |
| 6 | Industry Playbooks | 13-14 | E-commerce, healthcare, real estate packages |
| 7 | AI Operator Capstone | 15-17 | Full-stack AI Personal Assistant |
| 8 | Career & Business | 18-19 | Portfolio, clients, pricing, scaling |

---

## Active Automation Projects

| Project | Folder | Phase | Status |
|---------|--------|-------|--------|
| AI News Telegram Bot | `AI_News_Telegram_Bot/` | 3-4 | Active |
| Blotato Social Media | `Blotato_Social_Media/` | 3 | Active |
| Salesforce PDF Filler | `Salesforce_PDF_Filler/` | 3 | Active |
| Google Maps Scraper | `Scrape Data form Google Map/` | 6 | Active |
| Space Shooter Game | `Futuristic_Space_Shooter/` | 2 | Active |

---

## Deployment Options (Summary)

| Budget | Stack | Monthly Cost |
|--------|-------|-------------|
| **Free** | Railway + Vercel + GitHub Actions + Supabase | $0 |
| **Minimal** | Hostinger/DO VPS + Docker | $3-4/mo |
| **Comfortable** | VPS + domain + monitoring | $10/mo |
| **Professional** | VPS + n8n Cloud + SSL + monitoring | $20-30/mo |

Full details: `DEPLOY.md`

---

## Skills Library Mapping

| Bootcamp Phase | Relevant Skills |
|---------------|----------------|
| Phase 1 (Thinking) | `create-proposal`, `generate-report` |
| Phase 3 (No-Code) | `gmail-inbox`, `gmail-label`, `instantly-campaigns`, `welcome-email` |
| Phase 4 (AI Agents) | `classify-leads`, `skool-rag`, `literature-research` |
| Phase 5 (Deploy) | `modal-deploy`, `add-webhook`, `local-server` |
| Phase 6 (Playbooks) | `scrape-leads`, `gmaps-leads`, `onboarding-kickoff` |
| Phase 7 (Capstone) | Full Angelina system -- `design-website` + custom |
| Phase 8 (Clients) | `upwork-apply`, `create-proposal`, `instantly-campaigns` |

---

## Student Resources

| Resource | Location |
|----------|----------|
| Student Doubts System | `Students-Doubts/` |
| Doubt Log | `Students-Doubts/DOUBTS-LOG.md` |
| Reply Templates | `Students-Doubts/REPLY-TEMPLATES.md` |
| Starter Kit (downloadable) | `resources/student-starter-kit.zip` |

---

## Self-Update Rules

- Update LOADOUT.md when: batch dates change, syllabus updates, new resources added
- Update PROMPTS.md when: any prompt is created or used
- Update DEPLOY.md when: new platforms discovered or pricing changes
- Log student doubts via `Students-Doubts/` system
- After editing CLAUDE.md, run `./sync.sh`

---

*Last verified: 2026-04-05 | Version: 2.0*
