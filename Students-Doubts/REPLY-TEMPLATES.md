# Reply Templates — Future-Proof AI Automation Bootcamp

> Copy-paste WhatsApp replies for common student doubts.
> Dhruv's voice: direct, practical, no fluff, 3-5 lines max.
> Claude adds new templates here as new patterns emerge.

---

## PRE-BATCH

### No Coding Experience
```
No coding needed. You design the system — AI writes the code.
We use Claude + Cursor to generate everything.
Your job is to think like an architect, not a programmer.
```

### Which Tool to Learn First
```
Tool-agnostic bootcamp — we don't teach n8n or Make specifically.
We teach the patterns: triggers, conditions, data flow, error handling.
Those patterns work on any platform. Tool is just the implementation.
```

### Will I Get a Certificate?
```
Yes — official Euron Certificate of Completion.
Plus access to Euron Job Portal + internship opportunities.
But more valuable: 18+ deployed projects in your portfolio.
```

### Can I Watch Recordings?
```
Yes — lifetime access to all session recordings.
But show up live if you can — doubt clearing after each session is where the real learning happens.
```

### Is Rs.5,000 the Final Price?
```
Yes, Rs.5,000 all-in (includes taxes).
If you're on Euron Plus — it's already included.
```

---

## PHASE 1 — Automation Thinking

### "What is the Agentic Loop?"
```
Sense → Think → Decide → Act → Learn.
Every system we build in this bootcamp maps to this loop.
Automation has no loop. An agent does.
```

### "How do I audit a business?"
```
Map their operations: Sales → Ops → Support → Finance → Growth.
Find where humans repeat the same thing 3+ times/week.
That's your automation opportunity. We cover this in Week 1.
```

### "What if I can't find a business to audit?"
```
Use a hypothetical — pick any local business you know.
Restaurant, gym, coaching academy — anything with repetitive ops.
The framework works the same either way.
```

---

## PHASE 3 — No-Code Automation

### "How do I connect Gmail in n8n?"
```
In n8n: Add a Gmail node → Credentials → OAuth2 → Follow the Google auth flow.
No custom code needed. n8n handles the OAuth handshake.
If you get a "redirect URI" error — make sure n8n's callback URL is whitelisted in your Google Cloud project.
```

### "Webhook not triggering — what do I check?"
```
3 things to check:
1. Is the webhook URL live and listening? (n8n must be in "waiting" mode)
2. Is the sender hitting the correct URL? (copy from n8n, don't retype)
3. Check the Content-Type header — most APIs send JSON, make sure n8n expects JSON.
```

### "What's the difference between n8n cloud and self-hosted?"
```
Cloud = managed by n8n team, easier setup, paid after free tier.
Self-hosted = you run it on your VPS, free, full control.
For learning: cloud is fine. For production/clients: self-hosted on VPS (we cover this in Phase 5).
```

---

## PHASE 4 — AI-Powered Systems

### "Euri API key not working"
```
Euri key ≠ OpenAI key. Two different things.
1. Get your Euri API key from Euri dashboard
2. Set base_url = https://api.euron.one/api/v1/euri
3. Use Euri model IDs (not gpt-4 or gpt-3.5)
If still failing — check key activation + copy-paste without spaces.
```

### "Which LLM should I use for my project?"
```
For most bootcamp projects: Euri API (already have access, affordable).
For production: Claude for reasoning/writing, GPT-4o for multimodal, Gemini for large context.
Start cheap, upgrade when you hit limits.
```

### "Agent vs Automation — what's the difference?"
```
Automation = fixed recipe. Same inputs → same steps → same output.
Agent = goal-driven. Senses the situation → decides what to do → acts → learns.
Agentic Loop: Sense → Think → Decide → Act → Learn.
An agent can choose from multiple tools. An automation can't.
```

### "What is RAG and when do I need it?"
```
RAG = make AI know YOUR business data.
By default, AI doesn't know your product catalog, policies, or internal docs.
RAG: you store your docs in a vector DB → AI searches them before answering.
Use RAG when: chatbot needs to answer from specific docs/data. Phase 9 covers this fully.
```

### "LangChain vs LangGraph — which one?"
```
LangChain = building blocks for LLM apps (chains, RAG, tools).
LangGraph = orchestration for multi-agent systems with loops and state.
Start with LangChain (Phase 4). Use LangGraph when your agent needs memory + multi-step decision loops.
```

---

## PHASE 5 — Deployment

### "Which VPS should I buy?"
```
Wait until Phase 5 (Week 11) before buying anything.
For learning: Hostinger (~$4-6/mo) is fine.
For production: DigitalOcean or AWS free tier.
I'll guide you through setup live in class.
```

### "Docker is confusing — how do I think about it?"
```
Docker = shipping container for your app.
Same app, any machine, no "works on my machine" problems.
Think: Dockerfile = recipe. Image = packaged recipe. Container = running instance.
You don't need to master Docker — just enough to deploy your projects. We cover this step-by-step.
```

### "SSL certificate — how do I add HTTPS?"
```
Use Certbot + Let's Encrypt (free).
Nginx handles the reverse proxy and SSL termination.
Full setup: Nginx → Certbot → point your domain → done.
We do this live in Week 11.
```

---

## PHASE 7 — AI Personal Assistant (Capstone)

### "Is this the same as Angelina?"
```
Angelina is Dhruv's personal AI assistant — the template model.
You'll build your own version with the same architecture.
Same backend, same dashboard, connected to your own Gmail, Calendar, LinkedIn.
Customized for your life, sellable to clients for Rs.1L-5L.
```

### "What do I need to start Phase 7?"
```
Phases 3-5 done: automation patterns, API integrations, VPS setup.
Access to: Gmail API, Google Calendar API, LinkedIn API (we get these in class).
Tools ready: Cursor, VS Code, GitHub account.
Everything else gets built in class — don't overthink setup before we get there.
```

---

## PHASE 8 — Career & Business

### "How do I price my automation services?"
```
3 models:
1. Project-based: Rs.20K-2L depending on complexity (use our ROI calculator)
2. Retainer: Rs.15-40K/month for ongoing automation support
3. Hybrid: fixed project + monthly maintenance
Start with project-based. Move to retainer once trust is established. Week 19 covers this fully.
```

### "How do I find clients?"
```
3 channels we cover in Week 19:
1. LinkedIn outreach (AI-assisted, personalized)
2. Referrals from first 2-3 clients (fastest)
3. Cold email with value-first approach
Don't overthink channel — pick one and go deep. We build the full outreach system in class.
```

---

## GENERAL

### "Claude Code — only Desktop?"
```
Claude Code works on: CLI, Claude Desktop, VS Code, SSH.
Not supported on: claude.ai web or mobile.
Worktrees need Git + local environment.
```

### "I missed a session — what do I do?"
```
Watch the recording — lifetime access on Euron platform.
If you have a doubt from the session — drop it in WhatsApp, I'll cover it next doubt clearing.
```

### "Is the WhatsApp group active?"
```
Yes — active during sessions and doubt clearing hours.
Post your question + screenshot/error so we can help faster.
```

---

*Templates: 30+ | Last updated: 2026-03-08*
