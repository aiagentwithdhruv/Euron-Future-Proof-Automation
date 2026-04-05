#!/bin/bash
# Sync learning hub content to Obsidian AI Second Brain vault.
# Usage: bash scripts/sync-obsidian.sh
#
# Syncs:
#   techniques/*.md     --> Obsidian 03-Resources/automation-techniques/
#   ERRORS.md           --> Obsidian 03-Resources/error-logs/
#   LEARNINGS.md        --> Obsidian 03-Resources/learning-logs/
#   automations/CATALOG.md --> Obsidian 01-Projects/
#
# Does NOT sync: .env, .tmp/, runs/ (too verbose/sensitive)

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HUB="$ROOT/learning-hub"
OBSIDIAN="/Users/apple/Aiwithdhruv/AI Development/Claude/ai-second-brain"

# Check Obsidian vault exists
if [ ! -d "$OBSIDIAN" ]; then
  echo "Error: Obsidian vault not found at $OBSIDIAN"
  echo "Skipping Obsidian sync."
  exit 0
fi

echo "Syncing learning hub to Obsidian..."

# 1. Techniques
TECH_DIR="$OBSIDIAN/03-Resources/automation-techniques"
mkdir -p "$TECH_DIR"
if [ -d "$HUB/techniques" ]; then
  cp "$HUB/techniques/"*.md "$TECH_DIR/" 2>/dev/null || true
  echo "  -> techniques/ synced to Obsidian"
fi

# 2. Error log
ERR_DIR="$OBSIDIAN/03-Resources/error-logs"
mkdir -p "$ERR_DIR"
if [ -f "$HUB/ERRORS.md" ]; then
  cp "$HUB/ERRORS.md" "$ERR_DIR/automation-errors.md"
  echo "  -> ERRORS.md synced to Obsidian"
fi

# 3. Learnings
LEARN_DIR="$OBSIDIAN/03-Resources/learning-logs"
mkdir -p "$LEARN_DIR"
if [ -f "$HUB/LEARNINGS.md" ]; then
  cp "$HUB/LEARNINGS.md" "$LEARN_DIR/automation-learnings.md"
  echo "  -> LEARNINGS.md synced to Obsidian"
fi

# 4. Automation catalog
PROJ_DIR="$OBSIDIAN/01-Projects"
mkdir -p "$PROJ_DIR"
if [ -f "$HUB/automations/CATALOG.md" ]; then
  cp "$HUB/automations/CATALOG.md" "$PROJ_DIR/automation-catalog.md"
  echo "  -> CATALOG.md synced to Obsidian"
fi

echo ""
echo "Done! Learning hub synced to Obsidian at:"
echo "  $OBSIDIAN"
echo ""
echo "Tip: If obsidian-git plugin is active, changes will auto-commit."
