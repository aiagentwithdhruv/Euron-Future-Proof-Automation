#!/bin/bash
# Sync CLAUDE.md (source of truth) to all AI tool config files.
# Usage: ./sync.sh
#
# Syncs to:
#   .cursorrules        - Cursor (full copy)
#   .clinerules/        - Cline (formatted for directory structure)
#   .gemini/context.md  - Gemini (summary version)

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$ROOT/CLAUDE.md"

if [ ! -f "$SOURCE" ]; then
  echo "Error: CLAUDE.md not found at $SOURCE"
  exit 1
fi

echo "Syncing from CLAUDE.md..."

# 1. Cursor — full copy
cp "$SOURCE" "$ROOT/.cursorrules"
echo "  -> .cursorrules updated"

# 2. Cline — copy to .clinerules directory
mkdir -p "$ROOT/.clinerules"
cp "$SOURCE" "$ROOT/.clinerules/00-master-context.md"
echo "  -> .clinerules/00-master-context.md updated"

# 3. Gemini — generate a condensed version
mkdir -p "$ROOT/.gemini"
cat > "$ROOT/.gemini/context.md" << 'GEMEOF'
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
GEMEOF
echo "  -> .gemini/context.md updated"

echo ""
echo "Done! All AI tool configs synced."
echo ""
echo "  Claude Code:  CLAUDE.md (source)"
echo "  Cursor:       .cursorrules"
echo "  Cline:        .clinerules/00-master-context.md"
echo "  Gemini:       .gemini/context.md"
