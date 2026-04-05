# {{PROJECT_NAME}} — Automation Rules

> This file inherits from the parent `CLAUDE.md` at project root.
> Project-specific overrides and context go here.

---

## Project

- **Name:** {{PROJECT_NAME}}
- **Objective:** {{One sentence — what this automation does}}
- **Phase:** {{Bootcamp phase this belongs to}}
- **Status:** In Progress

---

## Architecture

```
Sense --> Think --> Decide --> Act --> Learn
```

### What This Automation Does
1. **Sense:** {{What triggers it / what data does it watch?}}
2. **Think:** {{What decisions does the AI make?}}
3. **Decide:** {{What action gets chosen?}}
4. **Act:** {{What gets executed?}}
5. **Learn:** {{How does it improve over time?}}

---

## Tech Used

| Layer | Choice |
|-------|--------|
| **Backend** | {{FastAPI / n8n / etc.}} |
| **AI Model** | {{euri/gpt-4o-mini / etc.}} |
| **Database** | {{Supabase / Google Sheets / etc.}} |
| **Deploy** | {{See DEPLOY.md for options}} |
| **APIs** | {{List external APIs used}} |

---

## Environment Variables

See `.env.example` for required keys. Copy to `.env` and fill in.

---

## Inherited Rules

This project follows ALL rules from the parent `CLAUDE.md`:
- Agentic Loop architecture
- 3-layer separation (Agent -> Workflows -> Tools)
- 10 Operational Rules
- Security Guardrails (14 non-negotiable)
- Budget Protection ($2/run, $5/day)
- Self-Improvement Loop (fix -> verify -> update -> log)
- Tool-first execution (no inline code for API calls)

---

## Project-Specific Rules

<!-- Add any rules specific to this project -->

---

## Files

```
{{PROJECT_NAME}}/
├── CLAUDE.md          # This file
├── PROMPTS.md         # Prompts used in this project
├── README.md          # Project description
├── .env.example       # Required API keys
├── .env               # Actual keys (never commit)
├── workflows/         # Markdown SOPs
├── tools/             # Python scripts
├── runs/              # Execution logs
└── .tmp/              # Intermediate files
```
