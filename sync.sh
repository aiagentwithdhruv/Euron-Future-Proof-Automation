#!/bin/bash
# Sync CLAUDE.md (source of truth) to all AI tool config files.
# Usage: ./sync.sh
#
# Syncs to:
#   .cursorrules        — Cursor (full copy)
#   .clinerules/        — Cline (formatted for directory structure)
#   .gemini/context.md  — Gemini (summary version)

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
echo "  → .cursorrules updated"

# 2. Cline — copy to .clinerules directory
mkdir -p "$ROOT/.clinerules"
cp "$SOURCE" "$ROOT/.clinerules/00-master-context.md"
echo "  → .clinerules/00-master-context.md updated"

# 3. Gemini — already has its own context.md (manual, shorter version)
echo "  → .gemini/context.md (not auto-synced — update manually if needed)"

echo ""
echo "Done! All AI tool configs synced from CLAUDE.md."
echo ""
echo "Files updated:"
echo "  Claude Code:  CLAUDE.md (source)"
echo "  Cursor:       .cursorrules"
echo "  Cline:        .clinerules/00-master-context.md"
echo "  Gemini:       .gemini/context.md (manual)"
