#!/bin/bash
# Create a new automation project from _template/
# Usage: bash scripts/new-automation.sh "My-Project-Name"
#
# Creates:
#   - Project folder with CLAUDE.md, PROMPTS.md, README.md, .env.example
#   - workflows/, tools/, runs/, .tmp/ directories
#   - Updates root PROMPTS.md with new project section
#   - Replaces {{PROJECT_NAME}} and {{DATE}} placeholders

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE_DIR="$ROOT/_template"

if [ -z "$1" ]; then
  echo "Usage: bash scripts/new-automation.sh \"Project-Name\""
  echo ""
  echo "Example: bash scripts/new-automation.sh \"AI-News-Bot\""
  exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="$ROOT/$PROJECT_NAME"
TODAY=$(date +%Y-%m-%d)

# Check if folder already exists
if [ -d "$PROJECT_DIR" ]; then
  echo "Error: Folder '$PROJECT_NAME' already exists at $PROJECT_DIR"
  exit 1
fi

# Check template exists
if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "Error: _template/ folder not found at $TEMPLATE_DIR"
  exit 1
fi

echo "Creating automation project: $PROJECT_NAME"
echo ""

# 1. Create project directory
mkdir -p "$PROJECT_DIR"

# 2. Copy template files
cp "$TEMPLATE_DIR/CLAUDE.md" "$PROJECT_DIR/CLAUDE.md"
cp "$TEMPLATE_DIR/PROMPTS.md" "$PROJECT_DIR/PROMPTS.md"
cp "$TEMPLATE_DIR/README.md" "$PROJECT_DIR/README.md"
cp "$TEMPLATE_DIR/.env.example" "$PROJECT_DIR/.env.example"

# 3. Create standard directories
mkdir -p "$PROJECT_DIR/workflows"
mkdir -p "$PROJECT_DIR/tools"
mkdir -p "$PROJECT_DIR/runs"
mkdir -p "$PROJECT_DIR/.tmp"

# 4. Replace placeholders in all files
for file in "$PROJECT_DIR/CLAUDE.md" "$PROJECT_DIR/PROMPTS.md" "$PROJECT_DIR/README.md"; do
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$file"
    sed -i '' "s/{{DATE}}/$TODAY/g" "$file"
  else
    sed -i "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$file"
    sed -i "s/{{DATE}}/$TODAY/g" "$file"
  fi
done

# 5. Create .gitignore for the project
cat > "$PROJECT_DIR/.gitignore" << 'GITIGNORE'
.env
.tmp/
__pycache__/
*.pyc
.DS_Store
GITIGNORE

# 6. Add project section to root PROMPTS.md
PROMPTS_FILE="$ROOT/PROMPTS.md"
if [ -f "$PROMPTS_FILE" ]; then
  # Add before the "Adding a New Prompt" section
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "/^## Adding a New Prompt/i\\
\\
### $PROJECT_NAME\\
| Prompt | Description |\\
|--------|-------------|\\
| _(no project-specific prompts yet)_ | |\\
" "$PROMPTS_FILE"
  else
    sed -i "/^## Adding a New Prompt/i\\
\\
### $PROJECT_NAME\\
| Prompt | Description |\\
|--------|-------------|\\
| _(no project-specific prompts yet)_ | |\\
" "$PROMPTS_FILE"
  fi
  echo "  -> Root PROMPTS.md updated"
fi

echo ""
echo "Project created at: $PROJECT_DIR"
echo ""
echo "Files:"
echo "  CLAUDE.md      - Project rules (fill in objectives)"
echo "  PROMPTS.md     - Project prompt tracker"
echo "  README.md      - Project description"
echo "  .env.example   - Required API keys"
echo "  .gitignore     - Ignore secrets and temp files"
echo "  workflows/     - Markdown SOPs"
echo "  tools/         - Python scripts"
echo "  runs/          - Execution logs"
echo "  .tmp/          - Intermediate files"
echo ""
echo "Next: Open CLAUDE.md and fill in the {{placeholders}}"
