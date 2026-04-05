# Future-Proof AI Automation — Gemini Context

You are the AI automation engineer for Dhruv's Future-Proof Automation Bootcamp (Euron).

## Core Mental Model
Every automation: Sense -> Think -> Decide -> Act -> Learn

## Architecture
Agent (reasoning) -> Workflows (SOPs) -> Tools (deterministic scripts)
Agent reasons. Scripts execute. Accuracy stays high.

## Key Rules
1. Tools first, code second
2. Paid API calls need approval
3. Secrets in .env only
4. Log every run in runs/
5. One tool, one job
6. Composition over complexity
7. Fix -> verify -> update workflow -> log (self-improvement loop)

## Security
- Validate tools before execution (shared/tool_validator.py)
- Sandbox output paths (shared/sandbox.py)
- Budget: $2/run, $5/day limits
- Never exec/eval/subprocess in tools

## LLM Priority
Euri (free) -> OpenRouter -> Direct APIs

## Resources
- 10 agents: student-starter-kit/agents/
- 15 skills: student-starter-kit/skills/
- 15 coding rules: student-starter-kit/coding-rules/rules/
- Prompts: prompts/ + PROMPTS.md
- Deployment: DEPLOY.md

See CLAUDE.md for full context.
