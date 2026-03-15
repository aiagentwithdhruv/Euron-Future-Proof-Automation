# Future-Proof AI Automation

> Production-grade AI automation framework by Dhruv — Antigravity / Euron.

---

## What's Here

```
Euron_Future_Proof_Automation/
├── CLAUDE.md                    # Master context (source of truth)
├── .cursorrules                 # Cursor context (synced from CLAUDE.md)
├── .clinerules/                 # Cline context (synced from CLAUDE.md)
├── .gemini/                     # Gemini context
├── prompts/                     # Global prompt library
│   ├── PROMPT_INDEX.md          # Index of all prompts
│   ├── automation/              # Workflow & pipeline prompts
│   ├── coding/                  # Code generation & review prompts
│   ├── content/                 # Content creation prompts
│   ├── research/                # Research & analysis prompts
│   └── templates/               # Template for creating new prompts
├── student-starter-kit/         # Distributable kit for learners
│   ├── agents/                  # 10 AI agent definitions
│   ├── skills/                  # 15 automation skills
│   ├── coding-rules/            # 15 engineering rules + docs
│   └── README.md                # Student setup guide
├── sync.sh                      # Sync CLAUDE.md to all tool configs
└── README.md                    # You are here
```

---

## Quick Start

### 1. Open in Any AI Tool

The context is already set up for:

| Tool | Config File | Auto-loads |
|------|-------------|-----------|
| **Claude Code** | `CLAUDE.md` | Yes (every conversation) |
| **Cursor** | `.cursorrules` | Yes (every session) |
| **Cline** | `.clinerules/` | Yes (every task) |
| **Gemini** | `.gemini/context.md` | Manual reference |

### 2. Keep Configs in Sync

After editing `CLAUDE.md`, run:

```bash
./sync.sh
```

This copies the master context to `.cursorrules` and `.clinerules/`.

### 3. Use Prompts

Browse `prompts/PROMPT_INDEX.md` for all available prompts. To add a new one:

```bash
# Copy the template
cp prompts/templates/PROMPT_TEMPLATE.md prompts/coding/my-new-prompt.md

# Edit it, then update the index
# Add entry to prompts/PROMPT_INDEX.md
```

### 4. Use Skills & Agents

Skills and agents live in `student-starter-kit/`. See the [student README](student-starter-kit/README.md) for setup.

---

## Architecture

**One source of truth:** `CLAUDE.md` contains all context — identity, tech stack, principles, available agents, skills, and coding rules. All other tool configs are synced from it.

**Prompt library:** Structured, reusable prompts with metadata, variables, and examples. Organized by category. Usable across any AI tool.

**Student starter kit:** Self-contained, distributable package with agents, skills, and coding rules that students can drop into their own projects.
