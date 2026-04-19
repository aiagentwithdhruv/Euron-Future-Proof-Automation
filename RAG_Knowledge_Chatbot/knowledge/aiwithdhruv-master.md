# AIwithDhruv — Master Knowledge Base

> Single source of truth the RAG chatbot answers from.
> Edit freely. After changes, re-run the ingestion workflow to refresh embeddings.
> Last updated: 2026-04-19

---

## About Dhruv Tomar

Dhruv Tomar is an **AI Architect, builder, and consultant**. He founded AIwithDhruv — a brand focused on building production AI systems and teaching people how to do the same.

- **Website:** aiwithdhruv.com
- **GitHub:** github.com/aiagentwithdhruv
- **LinkedIn:** linkedin.com/in/dhruvtomar
- **Location:** India (Delhi NCR)
- **Focus:** AI automation, agentic systems, RAG, voice AI, multi-agent orchestration

Dhruv built his career on a single rule: **don't use AI when rules work. Don't fine-tune when RAG works. Don't RAG when prompting works.** He teaches this discipline to every engineer and every student.

---

## What is AIwithDhruv?

AIwithDhruv is both a **personal brand** and a **product company**. The mission: turn complex AI engineering into practical, shippable systems that real businesses pay for.

Three pillars:

1. **Products** — IndianWhisper, QuotaHit, Angelina AI OS (full-stack AI products built in public)
2. **Teaching** — Euron courses, YouTube, LinkedIn content, bootcamps
3. **Consulting** — AI architecture, bootcamps for enterprises, implementation for clients

---

## Products Built by AIwithDhruv

### IndianWhisper
- **What:** On-device macOS voice transcription tool. Zero cloud, full privacy.
- **Who it's for:** Indian professionals, journalists, lawyers, founders who need private voice-to-text
- **Tech:** Whisper models running locally on Apple Silicon, SwiftUI interface
- **Status:** Community edition live. Commercial edition in 45-day launch plan (April–May 2026).
- **Pricing:** Community = free. Pro tier coming soon.

### QuotaHit
- **What:** AI Inbound Revenue Operating System. Not coaching — it's a full sales automation OS.
- **Who it's for:** B2B teams running inbound + outbound pipelines (India + international)
- **Scope:** 10 modules, global calling (India + US + Intl), 51-table schema, 7 autonomous agents
- **Status:** v3 architecture finalized April 2026. BRD in progress.

### Angelina AI OS
- **What:** Personal AI Operating System — 30+ tools, 5 agents, voice-first interface.
- **Tech:** Next.js (Vercel) + FastAPI backend + Supabase + integrations across Gmail, Calendar, LinkedIn, Notion, ClickUp.
- **Status:** Active development. Preparing multi-user launch.

### Euron Bootcamp — Future-Proof AI Automation
- **What:** 19-week bootcamp teaching AI automation from zero to production.
- **Platform:** Euron (euron.one)
- **Coverage:** 8 phases, 95+ subtopics, 18+ deployed projects (see syllabus below).

---

## The Future-Proof AI Automation Bootcamp

### Who it's for

- Developers tired of tutorials that never ship real products
- Freelancers and consultants who want to sell AI automations as services
- Founders who want to automate their business hands-off
- Students who want practical AI engineering skills, not theory

### 19-week structure (8 phases)

**Phase 1: Automation Thinking** (Weeks 1–2)
Map any business. Spot Rs.5L+ of automation opportunity. Design systems, not workflows. Learn the Agentic Loop: Sense → Think → Decide → Act → Learn.

**Phase 2: AI as Your System Designer** (Weeks 3–4)
AI-first mindset. Prompt engineering for architects (not chatting). Context documents. Rapid prototyping. Build your personal AI operating system.

**Phase 3: No-Code Automation Mastery** (Weeks 5–7)
Webhooks, APIs, data transformation, error handling. Multi-channel (email/WhatsApp/Slack/Telegram). CRM automation, database ops, scheduled jobs. Tool-agnostic.

**Phase 4: AI-Powered Autonomous Systems** (Weeks 8–10)
AI classification & routing. Self-correcting workflows. RAG systems. Goal-driven agents. Voice agents (inbound receptionist + outbound caller). Autonomous research agents.

**Phase 5: Deployment & Production Operations** (Week 11–12)
VPS from scratch, Docker, Nginx, SSL, self-hosted AI. Cost optimization, monitoring, logging, scaling.

**Phase 6: Industry Playbooks** (Weeks 13–14)
E-commerce/D2C suite. Service businesses, real estate, healthcare, construction. Industry audit framework.

**Phase 7: Build Your AI Operator — Full-Stack Capstone** (Weeks 15–17)
A full AI Personal Assistant. Backend + frontend + deployed. Sellable as Rs.1L–5L per client deployment.

**Phase 8: Career, Clients & Building a Business** (Weeks 18–19)
Positioning, portfolio, pricing, discovery calls, cold outreach, scaling to agency.

### Career tracks this bootcamp qualifies you for

| Role | Why |
|------|-----|
| AI Automation Engineer | Designs + deploys autonomous systems end-to-end |
| AI Solutions Architect | Audits businesses, architects solutions, sells outcomes |
| AI Consultant | Discovery → ROI → delivery → recurring revenue |
| Agentic AI Engineer | Builds goal-driven agents with memory, tools, autonomous execution |

### What's different about this bootcamp

- **Tool-agnostic systems thinking.** Platforms change. Patterns don't.
- **Every week ships a real project.** 18+ deployed automations by the end.
- **Production-grade.** We deploy to real infra (GitHub Actions, n8n, VPS, Koyeb), not just localhost.
- **The Diamond.** A self-learning system where every error fixed = a rule we never break again. Built into every project.
- **AI-first delivery.** You design, AI builds. You think, AI executes. You verify, AI ships.

---

## Key Concepts Students Ask About

### The Agentic Loop
Every automation follows: **Sense → Think → Decide → Act → Learn.**

- Sense: trigger, event, input
- Think: LLM reads context, plans, classifies
- Decide: pick the action
- Act: call tools, deliver output
- Learn: log outcome, feed back to prompt

This is the mental model behind every project in the bootcamp.

### 3-Layer Architecture
```
AGENT (LLM)        → reasoning, planning, decisions
WORKFLOWS (.md)    → instructions, SOPs
TOOLS (.py)        → deterministic execution
```

Why it matters: if the LLM does every step, 90% accuracy compounds to 59% after 5 steps. Offload execution to scripts → 90% × 100% × 100% × 100% × 100% = 90%.

**Agent reasons. Scripts execute. Accuracy stays high.**

### Automation vs AI vs Software
- **Automation:** Rules-based. If X then Y.
- **AI:** Decisions with judgment. "Does this email sound angry?"
- **Software:** Custom logic, stateful systems, UI.

Most problems are solved with automation. AI is added only where judgment is needed.

### RAG vs Fine-tuning vs Prompting
Decision tree:
1. Can prompting + context injection solve it? → Use prompting.
2. Does it need up-to-date domain knowledge? → Use RAG.
3. Does it need behavior/style changes? → Fine-tune.

Fine-tuning is rarely the right first answer. RAG wins 80% of the time.

---

## Teaching Methodology

### Every class is live-coded
No slides. No pre-recorded demos. Dhruv builds the automation in front of students in 30–45 minutes, deploys it, and it runs before the class ends.

### Every project is checked into GitHub
Students see the real commit history. They fork, modify, deploy their own.

### The Diamond (self-learning loop)
Every error hit during the build becomes a rule logged to `ERRORS.md`. Next session, the rule is read first. The system compounds intelligence over time.

### Lean delivery (inspired by Nate Herk)
- 30-second hook
- One tool at a time
- Build in 5 minutes
- Numbered steps
- Zero filler

---

## How to Join / Work with AIwithDhruv

### Join the Bootcamp
- **Platform:** Euron (euron.one)
- **Link:** Search "Future-Proof AI Automation" on euron.one
- **Price:** Check Euron listing for current tier

### Hire Dhruv for Consulting
- **Services:** AI architecture review, implementation, team training
- **Engagement:** Project-based, retainer, or hybrid
- **Contact:** aiwithdhruv@gmail.com

### Work with the AIwithDhruv Team
- **For agencies/enterprises:** Angelina-OS team can be deployed for client work
- **Team:** 7-agent structure (backend, frontend, content, sales, ops) + human operator
- **Stack:** Next.js, FastAPI, Supabase, n8n, MCP, LangChain, Euri, Claude

### Follow the Content
- **LinkedIn:** linkedin.com/in/dhruvtomar — daily posts
- **YouTube:** search "AIwithDhruv" — weekly tutorials
- **X/Twitter:** @aiwithdhruv
- **Instagram:** @aiwithdhruv

---

## Tech Stack We Teach & Use

| Layer | Tool |
|-------|------|
| Backend | FastAPI (Python) |
| Frontend | Next.js + React + TypeScript + Tailwind |
| Database | PostgreSQL via Supabase |
| Vector DB | Supabase pgvector |
| LLM routing | Euri (free) → OpenRouter → Claude/OpenAI direct |
| Embeddings | Gemini text-embedding-004 |
| Automation | n8n, GitHub Actions |
| Agent protocols | MCP, A2A |
| Deploy | GitHub Actions, Koyeb, Vercel, VPS (Hostinger/Oracle) |
| Editor | Claude Code, Cursor |
| Voice | Vapi, Bland, Retell, Whisper |

---

## Common Questions Students Ask

**Q: Do I need to know Python before starting?**
A: Basic familiarity helps, but the bootcamp is AI-first. You describe what you want, AI writes most of the code. You focus on systems thinking. By week 4, you're shipping working automations.

**Q: Is this no-code or code?**
A: Both. Phase 3 is no-code (n8n, Make). Phase 4 onwards is code (but AI-assisted). You learn when to use each.

**Q: What if I want to build my own AI agency after the bootcamp?**
A: Phase 8 (Weeks 18–19) covers exactly this. Positioning, pricing, cold outreach, closing deals. You leave with a client acquisition system.

**Q: How much can I earn as an AI Automation Engineer?**
A: Entry ~ Rs.8–15L/year in India. Senior/consultant ~ Rs.25L–1Cr. International remote ~ $80K–$200K. Project-based freelance ~ Rs.50K–5L per deployment.

**Q: What's the placement support?**
A: Portfolio + case studies + LinkedIn optimization + resume prep + live demos. The bootcamp output IS the portfolio. No certificates that nobody reads — deployed projects that clients can evaluate.

**Q: Do you use no-code platforms like Make.com or Zapier?**
A: We mention them, but we lean heavily on **n8n** (more flexible, self-hostable) and **Claude Code / Python** (full control, no platform lock-in).

**Q: Why do you not teach LangChain heavily?**
A: LangChain is one tool. We teach the underlying patterns (tool calling, RAG, agents) directly so you can use any framework. Pattern > framework.

**Q: What's MCP (Model Context Protocol)?**
A: A standard way for AI agents to call external tools. Instead of writing custom integrations, you write one MCP server and any MCP-compatible AI (Claude, Cursor, etc.) can use it. Covered in Week 10.

**Q: Will this bootcamp be outdated in 6 months?**
A: Tools change. Patterns don't. The Agentic Loop, 3-layer architecture, RAG, tool calling — these are foundational. You learn how to learn the next tool, not just today's tool.

---

## Active AIwithDhruv Projects (as of April 2026)

- **Million Dollar Voice** — 45-day plan to grow IndianWhisper from $0 → $12K–18K MRR
- **90-Day Revenue Engine** — $20K–$100K target via 9 channels
- **Social Media Agent** — automated LinkedIn + X + Instagram + YouTube posting
- **Portfolio** — aiwithdhruv.com (live)
- **Clients** — 7 active consulting engagements (Security AI, HomeJarvis, XLwear, others)

---

## The Diamond — Self-Learning Philosophy

Every error this system ever hits gets logged. Every fix becomes a rule. Every rule prevents the same mistake next time.

This is why our automations get faster to build, more reliable, and cheaper over time. It's not magic — it's structured learning compounded session after session.

**"The factory that learns from its own mistakes is the factory that never stops improving."**

---

## Contact Summary

- **Email:** aiwithdhruv@gmail.com
- **Website:** aiwithdhruv.com
- **LinkedIn:** linkedin.com/in/dhruvtomar
- **GitHub:** github.com/aiagentwithdhruv
- **Teaching:** euron.one
- **Products:** IndianWhisper (live), QuotaHit (v3 building), Angelina AI OS (multi-user prep)

Ask this bot anything about the above. If the bot doesn't know, it'll say so and escalate to Dhruv directly.
