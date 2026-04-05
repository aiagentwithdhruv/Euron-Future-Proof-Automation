# Prompt Library — Master Index

> Every prompt created or used across ALL automation projects is tracked here.
> When you create a prompt anywhere in this repo, add it here.

---

## How This Works

1. **Global prompts** live in `prompts/` (reusable across projects)
2. **Project prompts** live inside each project's `PROMPTS.md` (project-specific)
3. **This file** indexes everything — one line per prompt, grouped by project

---

## Global Prompts (`prompts/`)

### Automation
| Prompt | File | Description |
|--------|------|-------------|
| n8n Workflow Builder | `prompts/automation/n8n-workflow-builder.md` | Generate n8n workflow JSON from natural language |
| Webhook Orchestrator | `prompts/automation/webhook-orchestrator.md` | Design event-driven webhook pipelines |
| Batch Processor | `prompts/automation/batch-processor.md` | Process files/data in batch with error handling |

### Coding
| Prompt | File | Description |
|--------|------|-------------|
| FastAPI CRUD Generator | `prompts/coding/fastapi-crud-generator.md` | Generate full CRUD API with FastAPI |
| Code Review Checklist | `prompts/coding/code-review-checklist.md` | Structured code review with security focus |
| Refactor to Clean Arch | `prompts/coding/refactor-to-clean-arch.md` | Refactor messy code to clean architecture |
| Systematic Debug | `prompts/coding/debug-systematic.md` | Systematic debugging with hypothesis testing |

### Content
| Prompt | File | Description |
|--------|------|-------------|
| YouTube Script Writer | `prompts/content/youtube-script-writer.md` | Write engaging YouTube tutorial scripts |
| LinkedIn Post Generator | `prompts/content/linkedin-post-generator.md` | Create LinkedIn posts with hooks and CTAs |
| Course Module Designer | `prompts/content/course-module-designer.md` | Design structured course modules with exercises |

### Research
| Prompt | File | Description |
|--------|------|-------------|
| Tech Comparison | `prompts/research/tech-comparison.md` | Compare technologies with pros/cons matrix |
| Codebase Explorer | `prompts/research/codebase-explorer.md` | Explore and document an unfamiliar codebase |
| Market Research | `prompts/research/market-research.md` | Research market landscape for a product/service |

---

## Project Prompts

<!-- When a new automation project is created, add a section here -->

### AI_News_Telegram_Bot
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

### Blotato_Social_Media
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

### Salesforce_PDF_Filler
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

### Scrape Data from Google Map
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

### Futuristic_Space_Shooter
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

---


### Social-Media-Automations
| Prompt | Description |
|--------|-------------|
| _(no project-specific prompts yet)_ | |

## Adding a New Prompt

```
1. Write the prompt file using the template:
   cp prompts/templates/PROMPT_TEMPLATE.md prompts/<category>/<name>.md

2. Add it to this file under the right section

3. If it's project-specific, also add it to the project's own PROMPTS.md
```

---

**Total Prompts:** 12 global + 0 project-specific
**Last Updated:** 2026-04-05
