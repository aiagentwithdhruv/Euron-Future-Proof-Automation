# Atlas — Client Acquisition System

> **Persona:** Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina.
> **Rule #0:** If unclear, STOP and ask Angelina.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules
2. `../learning-hub/ERRORS.md`
3. `../learning-hub/automations/CATALOG.md`
4. `../Scrape Data form Google Map/` — reuse lead scraping tools
5. `../Multi_Channel_Onboarding/tools/send_email.py` — reuse email sender
6. `../Social-Media-Automations/` — reuse LinkedIn poster for LinkedIn DM automation
7. `../CRM_Automation/` — reuse lead scoring + CRM client
8. `../student-starter-kit/agents/backend-builder.md` — persona

---

## Objective (one sentence)

**End-to-end outbound pipeline: scrape prospects → qualify → personalize outreach → book discovery call → generate proposal draft → track to close.**

---

## Agentic Loop

- **Sense:** ICP query (industry + location + size) OR manual prospect list upload
- **Think:** Scrape/enrich → score prospects for fit → LLM personalizes outreach per prospect
- **Decide:** Channel (email / LinkedIn DM / cold call) + message variant + timing
- **Act:** Send outreach → on reply, route to discovery call booking → on booking, generate proposal draft → update CRM
- **Learn:** Track reply rate + meeting rate + close rate per ICP segment + message variant → tune

---

## Build Contract

1. Modular pipeline — 6 stages, each a sub-module:
   - `stages/01_scrape/` — find prospects
   - `stages/02_enrich/` — add emails, LinkedIn, context
   - `stages/03_qualify/` — score fit
   - `stages/04_outreach/` — personalized email / LI DM
   - `stages/05_discovery/` — calendar booking + prep doc
   - `stages/06_proposal/` — generate proposal draft
2. Orchestrator: `tools/run_pipeline.py`
3. State persisted in Airtable (MVP) or Supabase
4. Cold outreach must follow CAN-SPAM / DPDP rules
5. Test full loop with 5 fake prospects → log
6. DO NOT deploy

---

## Tools to Build

### Stage 1 — Scrape
| Tool | Input | Output |
|------|-------|--------|
| `stages/01_scrape/google_maps.py` | query, location | prospects CSV |
| `stages/01_scrape/linkedin_search.py` | ICP params | prospects CSV |
| `stages/01_scrape/apollo_export.py` | filters | prospects CSV |

### Stage 2 — Enrich
| Tool | Input | Output |
|------|-------|--------|
| `stages/02_enrich/find_email.py` | name + domain | email (Hunter.io / Apollo) |
| `stages/02_enrich/linkedin_profile.py` | name + company | bio + role |
| `stages/02_enrich/company_context.py` | domain | website summary + tech stack |

### Stage 3 — Qualify
| Tool | Input | Output |
|------|-------|--------|
| `stages/03_qualify/score_fit.py` | prospect + ICP | fit_score 0-100 + reasoning |

### Stage 4 — Outreach
| Tool | Input | Output |
|------|-------|--------|
| `stages/04_outreach/personalize_email.py` | prospect + offer | email body + subject |
| `stages/04_outreach/send_email.py` | email | send receipt |
| `stages/04_outreach/linkedin_dm.py` | profile + msg | DM receipt (manual-review required) |
| `stages/04_outreach/followup_sequence.py` | prospect_id | schedule 3 followups |

### Stage 5 — Discovery
| Tool | Input | Output |
|------|-------|--------|
| `stages/05_discovery/booking_link.py` | prospect | Calendly/Cal.com link |
| `stages/05_discovery/prep_brief.py` | prospect | pre-call brief doc |

### Stage 6 — Proposal
| Tool | Input | Output |
|------|-------|--------|
| `stages/06_proposal/generate_draft.py` | call_notes + offer | proposal markdown/PDF |

### Orchestrator
| Tool | Purpose |
|------|---------|
| `tools/run_pipeline.py --icp config/icp.yaml` | Full cycle |
| `tools/dashboard.py` | Pipeline metrics CLI |

---

## Workflow SOPs

- `workflows/pipeline-flow.md` — full 6-stage SOP
- `workflows/outreach-templates.md` — email + DM templates by ICP
- `workflows/discovery-call-script.md` — discovery framework (BANT+)

---

## APIs / Tools

| API | Free Tier | Used For |
|-----|-----------|----------|
| Apify / Outscraper | Free trial | Scraping |
| Hunter.io | 25/mo free | Email find |
| Apollo | Free 50 credits | Enrichment |
| Euri | 200K tokens/day | LLM |
| Resend | 100/day | Email |
| Calendly / Cal.com | Free | Booking |
| Airtable / Supabase | Free | Pipeline state |

---

## Env Vars

```
# Scrape
APIFY_API_TOKEN=
OUTSCRAPER_API_KEY=

# Enrich
HUNTER_API_KEY=
APOLLO_API_KEY=

# LLM
EURI_API_KEY=

# Outreach
RESEND_API_KEY=
EMAIL_FROM=
EMAIL_UNSUBSCRIBE_URL=

# LinkedIn
LINKEDIN_ACCESS_TOKEN=
LINKEDIN_PERSON_URN=

# Calendar
CALCOM_API_KEY=
BOOKING_URL=

# State
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
AIRTABLE_PIPELINE_TABLE=Pipeline

# Notify
SLACK_WEBHOOK_URL=

# ICP
ICP_CONFIG=./config/icp.yaml
```

---

## Rules of Engagement

- **Doubt = STOP.** Questions:
  - "Which ICP? (industry, geography, company size, role)?"
  - "Which offer? (service, price range, deliverable)?"
  - "Outreach channels — email only, or email + LinkedIn DM?"
  - "Which scraper — Apify, Outscraper, or Apollo?"
- **CAN-SPAM / DPDP compliance** — unsubscribe link in every email.
- **LinkedIn DM = manual-review-required** v1. LinkedIn does NOT officially support DM automation. Draft + copy to clipboard → human sends.
- **Rate limits respected** — max 50 emails/day per sender, 1 email per prospect per 3 days.
- **No spray-and-pray.** Every message personalized (company-specific hook).

---

## Test Command

```bash
cd Client_Acquisition_System
python tools/run_pipeline.py --icp config/icp.yaml --limit 5 --dry-run
```

---

## When Done

Update catalog + techniques file. Ping Angelina.
