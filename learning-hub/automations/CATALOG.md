# Automation Catalog

> Registry of every automation built in this bootcamp.
> Updated after each build session. Used for: teaching, reuse, portfolio, client demos.

---

## 🚀 Live Deployments (as of 2026-04-19)

| # | Automation | Platform | URL / Trigger |
|---|-----------|----------|---------------|
| 1 | AI News Telegram Bot | **GitHub Actions** | Daily 9 AM UTC → Telegram chat `637313836` |
| 2 | Social Media — Daily LinkedIn | **GitHub Actions** | Daily 4:30 AM UTC → LinkedIn (AIwithDhruv) |
| 3 | Autonomous Research Agent | **GitHub Actions** | Mon 3 AM UTC → Telegram |
| 4 | AIwithDhruv RAG Chatbot | **n8n** | `n8n.aiwithdhruv.cloud/webhook/aiwithdhruv-chat/chat` (public chat widget) |

All four are FREE — zero hosting cost. GitHub Actions on public repo = unlimited. n8n = bootcamp instance.

---

## Complete Automations

### 1. AI News Telegram Bot
| Field | Detail |
|-------|--------|
| **Folder** | `AI_News_Telegram_Bot/` |
| **What** | Fetches top 5 AI news daily, ranks with LLM, delivers to Telegram |
| **Phase** | 3 (No-Code Automation) |
| **Agentic Loop** | Sense: RSS/NewsAPI feeds -> Think: LLM ranks relevance -> Decide: Top 5 stories -> Act: Format + send to Telegram -> Learn: _(future: track engagement)_ |
| **Tech** | Python, requests, feedparser, OpenAI SDK (Euri), Telegram Bot API |
| **APIs** | NewsAPI (free), Euri (free), Telegram (free), Tavily (optional) |
| **Deploy** | Local cron, GitHub Actions, or n8n |
| **Status** | Complete |
| **Reusable Parts** | News fetching tool, LLM ranking prompt, Telegram delivery tool |

### 2. Salesforce PDF Filler
| Field | Detail |
|-------|--------|
| **Folder** | `Salesforce_PDF_Filler/` |
| **What** | Reads Salesforce data, auto-fills PDF forms. CLI + API + n8n modes. |
| **Phase** | 4 (AI-Powered Autonomous Systems) |
| **Agentic Loop** | Sense: Salesforce data change -> Think: Map fields to PDF -> Decide: Fill + validate -> Act: Generate PDF + upload -> Learn: Log mapping accuracy |
| **Tech** | Python, fillpdf, simple-salesforce, FastAPI, Click CLI, n8n |
| **APIs** | Salesforce REST API (OAuth2), PDF AcroForm |
| **Deploy** | CLI, FastAPI service, n8n workflow, Docker |
| **Status** | Complete — dual-method (code + n8n) |
| **Reusable Parts** | Salesforce client, PDF filler, field mapper, FastAPI template |

### 3. Blotato Social Media Repurposer
| Field | Detail |
|-------|--------|
| **Folder** | `Blotato_Social_Media/` |
| **What** | Transforms YouTube videos into platform-optimized social posts with AI visuals |
| **Phase** | 6 (Industry Playbooks — Marketing) |
| **Agentic Loop** | Sense: YouTube URL -> Think: Extract content, choose platform styles -> Decide: Generate copy + visuals per platform -> Act: Publish or save drafts -> Learn: Track engagement |
| **Tech** | Python, requests, YAML config |
| **APIs** | Blotato API v2 (extraction, visual gen, publishing) |
| **Deploy** | Local CLI, cron scheduled |
| **Status** | Complete |
| **Reusable Parts** | YouTube extractor, multi-platform publisher, prompt templates |

### 4. Google Maps Lead Scraper
| Field | Detail |
|-------|--------|
| **Folder** | `Scrape Data form Google Map/` |
| **What** | Scrapes business leads from Google Maps by industry + location, enriches with email |
| **Phase** | 3 (No-Code Automation — Data) |
| **Agentic Loop** | Sense: Search query (industry + city) -> Think: Build optimal search -> Decide: Apify or Outscraper -> Act: Scrape + enrich + export Excel -> Learn: Track hit rates |
| **Tech** | Python, apify-client, outscraper, pyhunter, pandas, openpyxl, gspread |
| **APIs** | Apify ($5 free credits), Outscraper (500 free), Hunter.io (25 free/mo), Google Sheets |
| **Deploy** | Local CLI, batch processing |
| **Status** | Complete |
| **Reusable Parts** | Query builder, multi-scraper fallback pattern, Excel exporter |

### 5. Agentic Workflow Engine
| Field | Detail |
|-------|--------|
| **Folder** | `Agentic Workflow for Students/` |
| **What** | Code-first framework for building AI automations. Foundation for all other projects. |
| **Phase** | 2 (AI as System Designer — Infrastructure) |
| **Agentic Loop** | Sense: User task -> Think: Check workflows/tools -> Decide: Execute or build new -> Act: Run tools -> Learn: Log run + update on failure |
| **Tech** | Python, FastAPI, YAML config, shared security modules |
| **APIs** | Euri, OpenRouter, OpenAI/Anthropic (configurable) |
| **Deploy** | Local, VPS, Docker, cron/GitHub Actions |
| **Status** | Active framework — all projects build on this |
| **Reusable Parts** | Everything — tool validator, sandbox, cost tracker, logger, retry, templates |

---

---

## Dispatched to Atlas (2026-04-19)

> Scaffolded with ATLAS-PROMPT.md + CLAUDE.md + PROMPTS.md + README.md + .env.example.
> Multi_Channel_Onboarding = DONE (see below). 8 remaining in queue.

### 7. Multi-Channel Onboarding — BUILT (2026-04-19)
| Field | Detail |
|-------|--------|
| **Folder** | `Multi_Channel_Onboarding/` |
| **What** | One signup → personalized Email + WhatsApp + Slack alert + Day 2 / Day 5 follow-up drip. Driven by one CLI trigger, AI-personalized copy with template fallback. |
| **Phase** | 3 |
| **Owner** | Atlas |
| **Agentic Loop** | Sense: signup JSON (webhook/batch) → Think: Euri gpt-4o-mini personalizes per channel → Decide: sequence based on segment + available fields (skips WA if no phone) → Act: email → WA → Slack + queue follow-ups → Learn: run log per signup, channel-level pass/fail tracked |
| **Tech** | Python stdlib + `openai` SDK + `requests`. Engine `shared/` imported via sys.path. |
| **APIs** | Euri (free 200K/day, optional), Resend (free 100/day), Twilio WhatsApp, Slack Incoming Webhook |
| **Tools** | `receive_signup.py`, `personalize_copy.py`, `send_email.py`, `send_whatsapp.py`, `send_slack.py`, `schedule_followup.py`, `run_onboarding.py` (orchestrator) |
| **Queue** | JSON file at `.tmp/followup_queue.json` (MVP) — swap for cron/n8n/Redis in prod |
| **Test** | `python tools/run_onboarding.py --signup .tmp/fake_signup.json --dry-run` → 4 tests passed (happy path, missing email, invalid email, no phone). See `runs/2026-04-19-test.md`. |
| **Deploy** | NOT deployed — awaiting Angelina dispatch |
| **Status** | Built + locally tested — ready for deploy dispatch |
| **Reusable Parts** | Personalization prompt (3-channel one-shot), file-based follow-up queue pattern, dry-run-first orchestrator, graceful channel degradation |

### 8. CRM Automation — BUILT (2026-04-19)
| Field | Detail |
|-------|--------|
| **Folder** | `CRM_Automation/` |
| **What** | Lead score → route → follow-up → stage advance → weekly report. **Pluggable across HubSpot · Zoho · Airtable · Mock behind one `CRMClient` interface — switch backends with `--source`, no tool changes.** |
| **Phase** | 3 |
| **Owner** | Atlas |
| **Status** | **Built + tested 2026-04-19 with mock backend (7 leads → 2 hot / 3 warm / 2 cold; idempotent re-run = 0 new). Ready for deploy dispatch (NOT deployed).** |
| **Agentic Loop** | Sense: new leads since `.tmp/last_run.json` → Think: LLM scores 0-100 (Euri gpt-4o-mini, heuristic fallback) → Decide: round-robin owner from `config/owners.yaml` + track from band + next stage → Act: CRM update + first-touch email (Resend) + owner task + stage advance → Learn: weekly health report to Slack + markdown |
| **Tech** | Python · OpenAI SDK (Euri-compatible) · pyairtable · requests · PyYAML · python-dotenv |
| **APIs** | Euri (LLM, free 200K/day) · HubSpot Private App · Zoho OAuth2 (cached access token) · Airtable PAT · Resend (free 100/day) · Slack incoming webhook |
| **Tools (8)** | `fetch_leads`, `score_lead`, `route_lead`, `update_crm`, `send_followup`, `advance_stage`, `weekly_report`, `run_crm_cycle` (orchestrator) |
| **Workflow** | `workflows/lead-lifecycle.md` (9-step SOP — written FIRST per build contract) + `workflows/scoring-prompt-v1.md` (versioned LLM rubric — fork to v2 when materially changed) |
| **Idempotency** | `.tmp/last_run.json` advances only on success · `processed_lead_ids[source]` filters duplicates within the time window · crash mid-run = no state advance, re-run picks up cleanly |
| **Pluggable CRM** | `crm/base.py` defines `CRMClient` interface (5 methods). 4 concrete impls + `crm/factory.py::get_client(source)`. Tools never import a concrete backend. |
| **Routing** | ≥ 90 → hot → `first_call_24h` + sales round-robin · 60-89 → warm → `nurture_5_email` + sales round-robin · < 60 → cold → `long_drip_monthly` + nurture bot. Owner pool capacity-capped via `config/owners.yaml::capacity_limit`. |
| **Guardrails** | $5 daily / $2 per-run cost cap (BudgetExceededError never silently caught) · `do_not_contact` flag forces score=0 · personal-email domains capped at 55 · all writes blocked in `--dry-run` · sandbox-restricted file writes · secret masking in all logs |
| **Test** | `python tools/run_crm_cycle.py --source mock --dry-run --no-llm` → `{"status":"success","leads_processed":7,"hot":2,"warm":3,"cold":2,...}`. Run log: `runs/2026-04-19-063156-lead-lifecycle.md`. Weekly report: `runs/2026-W16-crm-health.md`. |
| **Deploy** | Later — n8n cron (15 min) OR GitHub Actions (hourly). Do NOT deploy until at least one real CRM is wired and a sandbox cycle passes end-to-end with creds. |
| **Reusable Parts** | `crm/base.py` + `crm/factory.py` (pluggable backend pattern) · idempotent `last_run.json` state file · round-robin owner pool with capacity cap · versioned LLM scoring prompt + matching heuristic fallback · mock-backend pattern (offline tests for any CRM/API project) · `tracks.yaml` (multi-touch email cadence config) |

### 9. AI Support Ticket System — Built 2026-04-19
| Field | Detail |
|-------|--------|
| **Folder** | `AI_Support_Ticket_System/` |
| **What** | Email in → AI classify (intent/priority/sentiment/team) → KB-grounded draft → 6-layer guardrail → approval queue → human approve → Resend send |
| **Phase** | 4 |
| **Owner** | Atlas |
| **Status** | **Built + tested 2026-04-19 — ready for deploy dispatch (NOT deployed).** Dry-run verified with 6 fixture emails. |
| **Agentic Loop** | Sense: IMAP poll or fixtures → Think: LLM classify (euri/gpt-4o-mini) + keyword fallback → Decide: KB match + LLM draft + template fallback → Act: guardrail strip/block + ticket store + Slack notify → Wait: human approval via CLI → Send: Resend w/ thread headers → Learn: `.tmp/draft_edits.jsonl` captures every operator edit for future prompt tuning |
| **Tech** | Python · OpenAI SDK (Euri-compat) · stdlib imaplib + email · Airtable REST (optional) · Resend REST · Slack webhook |
| **APIs** | Euri (free) · IMAP Gmail App Password (free) · Resend 100/day free · Airtable free · Slack webhook free |
| **Guardrail** | 6-layer regex + Luhn — strips PII (SSN, phone, credit card, DOB, account#), blocks pricing, commitments, guarantees, code/SQL leakage, external URLs. Stress-tested with a toxic draft: 7/7 flags raised, text replaced with safe fallback. |
| **Human-in-the-loop** | MANDATORY v1 — nothing sends without `approval_queue.py --approve`. Approve re-runs guardrail on final text; blocks re-flag. Reject + spam paths tested. |
| **Tested** | 6 fixtures (billing/outage/refund/feedback/spam/question) → 6 tickets → 5 drafts (spam skipped) → 5 Slack notifs → 1 approve-send + 1 reject verified. Toxic-edit guardrail stress: all 7 patterns blocked. Phone-format regex patched after first test (paren format). |
| **Deploy** | NOT deployed per Phase-4 contract. Koyeb/cron every 2–5 min when credentials are provisioned. |
| **Reusable Parts** | `tools/guardrail.py` (6-layer + Luhn — reusable in any outbound-text agent) · `tools/approval_queue.py` (CLI pattern for human-in-the-loop) · keyword-fallback classifier · intent→team routing table · template-fallback drafter |

### 10. RAG Knowledge Chatbot
| Field | Detail |
|-------|--------|
| **Folder** | `RAG_Knowledge_Chatbot/` |
| **What** | One AI brain across website + WhatsApp with cited sources. Strict rule-50 separation — ingestion / retrieval / generation are 3 standalone layers; `tools/ask.py` is the only composer. |
| **Phase** | 4 |
| **Owner** | Atlas |
| **Status** | **Built 2026-04-19 — ready for deploy dispatch (NOT deployed)** |
| **Agentic Loop** | Sense: web/WhatsApp query → Think: Gemini embed + pgvector top-k → Decide: confidence gate (0.6) + citation gate → Act: cited reply OR escalate → Learn: `/feedback` logs verdict |
| **Tech** | Python · FastAPI · Supabase pgvector · Gemini text-embedding-004 (768d) · Euri gpt-4o-mini · Meta WhatsApp Cloud |
| **Gates** | (1) top similarity < 0.6 → escalate · (2) zero valid citations from LLM → escalate (no-cite-no-send) |
| **Rule-50 Audit** | AST scan: PASS — zero cross-imports between ingestion/retrieval/generation |
| **Tested** | Dry test on ingestion stages 1+2: 3 docs → 6 chunks, all metadata preserved. Full E2E pending Supabase + Gemini + Euri creds. |
| **Reusable Parts** | `_shared/embeddings.py` (Gemini client), `_shared/supabase_client.py` (pgvector REST wrapper), `answer_with_cite_v1` prompt, two-gate pattern |

### 11. AI Voice Agent
| Field | Detail |
|-------|--------|
| **Folder** | `AI_Voice_Agent/` |
| **What** | Inbound receptionist + outbound follow-up caller (Vapi) — FastAPI tool endpoints the voice platform calls |
| **Phase** | 4 |
| **Owner** | Atlas |
| **Status** | **Built + smoke-tested 2026-04-19 — ready for deploy dispatch (NOT deployed).** Full Vapi test call pending `.env` credentials. |
| **Agentic Loop** | Sense: inbound call / outbound queue task → Think: LLM intent + script branch → Decide: tool to call → Act: calendar + CRM + SMS + email + escalate → Learn: `/webhook/call_ended` → `post_call_summary` → Supabase `call_logs` |
| **Tech** | Python 3.11+ · FastAPI · Pydantic v2 · httpx · openai (Euri-compatible) · google-api-python-client · Supabase PostgREST · Twilio + Resend (direct REST) |
| **APIs** | Vapi (voice pipeline) · Euri (free LLM for summaries) · Google Calendar (service account) · Supabase (CRM + call_logs) · Twilio (SMS) · Resend (email) |
| **Endpoints** | 6 tool endpoints (`/tool/check_availability`, `/tool/book_appointment`, `/tool/capture_lead`, `/tool/lookup_customer`, `/tool/escalate_to_human`, `/tool/send_confirmation`) + `/webhook/call_ended` + `/webhook/status` + `/healthz` |
| **Smoke Test** | 9/9 pass — auth gate (401 on no-key/bad-key), Vapi envelope ↔ direct-body adapter, all 6 tools degrade cleanly when external services unconfigured, webhook returns 200 fast with background summary task |
| **Deploy** | Later — Koyeb (FastAPI always-on) + Vapi assistant pointing at Koyeb URL. Do NOT deploy until inbound + outbound test calls pass end-to-end. |
| **Compliance** | Consent mandatory for outbound (enforced in `tools/queue_outbound.py`, no `--force` flag) · DNC list check · time-of-day window · max 3 attempts · recording disclosure scripted · "talk to human" always honored · every call logged |
| **Reusable Parts** | Vapi tool-call adapter (`api/models.py::parse_tool_arguments`, `_extract_args`), shared-secret auth (`api/auth.py`), graceful service-degrade pattern, Supabase PostgREST client, consent-gated outbound queue script |

### 12. Autonomous Research Agent
| Field | Detail |
|-------|--------|
| **Folder** | `Autonomous_Research_Agent/` |
| **What** | Weekly competitor/market research report (no human trigger). For each competitor: fetch site + news + social → diff vs last week's snapshot → LLM classifies + ranks changes → writes markdown digest → delivers to Slack + Email + Telegram → saves new snapshot as next week's baseline. |
| **Phase** | 4 |
| **Owner** | Atlas |
| **Status** | **Built 2026-04-19 — tested dry-run on n8n + Lindy, ready for deploy dispatch (NOT deployed)** |
| **Agentic Loop** | Sense: weekly cron + competitor list → Think: fetch → diff → classify/rank → Decide: top N findings → Act: render markdown + deliver 3 channels → Learn: snapshot persisted as next cycle's baseline |
| **Tech** | Python · requests · bs4 + lxml · feedparser · OpenAI SDK (Euri → OpenRouter) · PyYAML · Resend · Telegram Bot API · Slack webhook |
| **APIs** | NewsAPI (free) · Tavily (free) · Euri LLM (free) · OpenRouter (fallback) · Slack/Resend/Telegram (free) |
| **Tools (8)** | `fetch_competitor`, `fetch_news`, `fetch_social`, `snapshot_diff`, `analyze_changes`, `write_report`, `deliver_report`, `run_research` (orchestrator) |
| **Workflow** | `workflows/research-cycle.md` (8-step SOP — written FIRST per build contract) |
| **Guardrails** | robots.txt honored · 3s rate-limit per domain · PII stripped (emails/phones/SSN) before snapshot save · $1/run hard cap · snapshot-diff = source of truth (LLM never re-analyzes full content) · dry-run mode skips delivery · missing delivery creds skip channel (not fail) |
| **Prompts** | `classify_change_v1`, `rank_findings_v1`, `write_report_v1` — rule-based + deterministic-template fallbacks when no LLM key |
| **Test Run** | 2026-04-19 dry-run with 2 competitors (n8n, Lindy). n8n blog fetched OK; n8n root + pricing + Lindy URLs correctly blocked by robots.txt (guardrail confirmed). Cost: $0. Log: `runs/2026-04-19-research-cycle.md`. Snapshots: `data/snapshots/{n8n,Lindy}.json`. |
| **Deploy** | GitHub Actions cron (weekly Monday, not yet wired — awaiting explicit deploy dispatch) |
| **Reusable Parts** | `shared/robots_check.py` (robots.txt cache + per-domain rate limiter + polite User-Agent) · `shared/sanitize.py::strip_pii` (email/phone/SSN scrub) · snapshot-diff-as-source-of-truth pattern · multi-channel delivery-with-skip (`deliver_report.py`) |

### 13. VPS AI Stack Deploy
| Field | Detail |
|-------|--------|
| **Folder** | `VPS_AI_Stack_Deploy/` |
| **What** | Production stack on VPS (n8n + chatbot + monitoring + SSL) |
| **Phase** | 5 |
| **Owner** | Atlas |
| **Status** | Prompt ready, awaiting build |

### 14. D2C E-Commerce Suite — Built 2026-04-19
| Field | Detail |
|-------|--------|
| **Folder** | `D2C_Ecommerce_Suite/` |
| **What** | 5-module D2C automation: **orders** (confirm + ship + review ask) · **support** (classify + RAG-grounded draft + human approval) · **cart recovery** (3-step discount-only sequence, never auto-charge) · **reviews** (sentiment + auto-reply positive, escalate negative) · **inventory** (low-stock alerts + deterministic reorder suggestion, no auto-order). |
| **Phase** | 6 (Industry Playbooks — E-Commerce, D2C & Retail) |
| **Owner** | Atlas |
| **Status** | **Built + tested 2026-04-19 — ready for deploy dispatch (NOT deployed).** 30/30 tests pass (25 unit + 5 webhook integration). Full CLI smoke pass on dry-run. |
| **Agentic Loop** | Sense: Shopify/Woo webhook event (HMAC-verified, idempotency-deduped) → Think: normalise to internal event shape, classify support email, grade review sentiment, compute reorder velocity → Decide: per-module routing; recovery=discount-only; negative reviews = draft + Slack, never auto-send → Act: email (Resend) + WhatsApp (Twilio) + Slack + Airtable row → Learn: runs/*.jsonl + `tools/dashboard.py` rollup |
| **Tech** | FastAPI (HMAC + BackgroundTasks) · Python 3.11+ · Euri gpt-4o-mini (OpenAI-compatible) · Resend (email) · Twilio (WhatsApp) · Slack incoming webhooks · Airtable (with local JSONL fallback) · SQLite idempotency store |
| **APIs** | Shopify Admin REST + HMAC webhooks · WooCommerce REST + HMAC webhooks · Euri LLM · Resend · Twilio · Slack · Airtable |
| **Modules (5 under `modules/`)** | `orders/` (send_confirmation, tracking_update, request_review) · `support/` (classify_email rule+LLM, draft_reply KB-RAG, ticket_workflow) · `cart_recovery/` (detect_abandoned, send_recovery_email, track_recovery) · `reviews/` (collect_reviews Shopify+local+stubs, classify_sentiment rule+LLM, auto_reply) · `inventory/` (check_stock_levels, alert_low_stock dedupe, suggest_reorder deterministic) |
| **Shared tools** | `api/webhook.py` (single receiver, 2 routes) · `tools/hmac_verify.py` · `tools/idempotency.py` · `tools/events.py` (platform-agnostic normalisation) · `tools/senders/{email,whatsapp,slack}.py` (used by all 5 modules — no duplication) · `tools/llm.py` (prompt rendering + JSON mode) · `tools/shopify_client.py` · `tools/woo_client.py` · `tools/airtable_client.py` · `tools/dashboard.py` |
| **Workflows** | `workflows/master-orchestration.md` + per-module SOPs: `order-lifecycle.md`, `support-flow.md`, `cart-recovery.md`, `review-management.md`, `inventory-alerts.md` |
| **Prompts (8)** | `order_confirmation_v1`, `cart_recovery_v1`, `review_reply_positive`, `review_reply_negative`, `reorder_suggestion`, `classify_ticket_v1`, `draft_reply_v1`, `classify_sentiment` — all strict-JSON contracts with deterministic fallbacks |
| **Guardrails** | HMAC-first (401 on mismatch; 500 when secret missing — never trust unverified bodies) · Idempotent (Shopify replays deduped via X-Shopify-Webhook-Id or sha256(body)) · **Discount-only recovery** (zero order-placement code exists) · Support drafts post-filtered for prices ($/₹/INR/USD) and timing promises · Negative reviews never auto-send (draft + Slack escalation) · `inventory.auto_order_enabled = False` by design; flag exists so future flip is explicit · Input length caps on LLM prompts (200 / 2000 chars) to resist prompt injection |
| **Tests** | `tests/test_unit.py` (25) + `tests/test_webhook_integration.py` (5 via FastAPI TestClient) — HMAC golden + mismatch · idempotency dedupe · event normalisation (order/cart/fulfilled) · all 3 senders dry-run · orders module (skip/fire/tracking) · support classifier (rule: shipping/spam/P1) · price-redaction guardrail · cart persistence + step-2 discount copy · sentiment rule (pos/neg/ambiguous) · inventory suggest (thin stock) + empty poll when unconfigured · webhook (health, HMAC mismatch, happy path, duplicate, unsupported topic) |
| **Observability** | Per-event rows at `runs/YYYY-MM-DD-<module>.jsonl` via `tools/run_logger.py`. `tools/dashboard.py` rolls up events + errors + local Airtable row counts |
| **Deploy** | NOT deployed (per build contract). Target: Koyeb (webhook receiver — always-on) + n8n/cron for `cart_recovery/detect_abandoned.py --scan` + `inventory/alert_low_stock.py` daily |
| **Reusable Parts** | `tools/hmac_verify.py` (any Shopify/Woo webhook consumer) · `tools/idempotency.py` (any replay-prone source) · `tools/events.py` (platform-agnostic event shape) · `tools/senders/*` (all 5 modules share these; any future D2C project can too) · post-filter guardrail pattern (`modules/support/draft_reply.strip_prices`) · rule-first + LLM-refinement classifier pattern · walk-up path-setup prelude for CLIs |

### 15. Client Acquisition System — Built 2026-04-19
| Field | Detail |
|-------|--------|
| **Folder** | `Client_Acquisition_System/` |
| **What** | End-to-end 6-stage outbound pipeline: **scrape → enrich → qualify → outreach → discovery → proposal**. ICP + offer defined in YAML; every email compliance-wrapped (CAN-SPAM + DPDP); LinkedIn DMs draft-only (human sends); rate-limited 50/day + 1/prospect/3d; fake-prospect seed path for safe end-to-end testing without API keys. |
| **Phase** | 8 |
| **Owner** | Atlas |
| **Status** | **Built + tested 2026-04-19 — ready for deploy dispatch (NOT deployed).** Full 6-stage dry-run PASS on 5 fake prospects. Suppression + cooldown negative tests PASS. |
| **Agentic Loop** | Sense: ICP query / Apollo CSV / seeded prospects → Think: Hunter/Apollo enrich + website context scrape + LLM fit-score 0-100 + pain hypothesis → Decide: threshold gate (≥70 qualified, 50-69 nurture, <50 archive) + channel (email + optional LinkedIn DM draft) → Act: personalized email (compliance-footer injected) + LI draft to `.tmp/drafts/linkedin/` + followup schedule (d3/d7/d14) + prep brief + proposal draft on call_done → Learn: state transitions + sends.log + dashboard funnel metrics per ICP segment |
| **Tech** | Python 3.11+ · JSON state store (Airtable optional) · OpenAI SDK (Euri-compatible) · PyYAML · requests + bs4 · apify-client · outscraper · pyhunter |
| **APIs** | Apify / Outscraper (scrape) · Hunter.io + Apollo (enrich) · Euri LLM (free 200K/day — qualify + personalize) · Resend (send, 100/day free) · Cal.com / Calendly (booking) · Airtable (optional mirror) · Slack webhook (notify) |
| **Stages (6 folders under `stages/`)** | `01_scrape/` (google_maps.py, linkedin_search.py, apollo_export.py) · `02_enrich/` (find_email.py, linkedin_profile.py, company_context.py) · `03_qualify/` (score_fit.py) · `04_outreach/` (personalize_email.py, send_email.py, linkedin_dm.py, followup_sequence.py) · `05_discovery/` (booking_link.py, prep_brief.py) · `06_proposal/` (generate_draft.py) |
| **Orchestrator** | `tools/run_pipeline.py` — full loop, single-stage (`--stage 03_qualify`), seed-fakes (`--seed-fakes 5`), dry-run by default. Dynamic-loads stage files via `tools/_load.py` (folders start with digits, not importable normally). Writes `runs/YYYY-MM-DD-pipeline.md` per run. |
| **Shared (7 modules)** | `shared/env.py` · `shared/logger.py` (JSON, secret-masked) · `shared/state.py` (pipeline + transitions + suppression + enrich cache + replies) · `shared/rate_limit.py` (daily cap + per-prospect cooldown) · `shared/llm.py` (Euri → OpenRouter → OpenAI, with stub_response fallback) · `shared/compliance.py` (CAN-SPAM + DPDP footer builder + honest-subject + hook-present checks) · `shared/sanitize.py` (email/URL/domain validators) |
| **Compliance (non-negotiable, enforced in code)** | CAN-SPAM: unsubscribe URL + physical postal address + honest sender + honest subject — all auto-appended and validated before send. DPDP: legitimate-interest clause + one-click opt-out — appended via `compliance.build_footer()`. LinkedIn DM = draft only to `.tmp/drafts/linkedin/` — the codebase literally has no API call that sends a LinkedIn DM. Rate limits: 50/day/sender + 1/prospect/3d, hard cap via `rate_limit.RateLimitError`. Suppression list honored by `state.is_suppressed()` before every send. Personalization hook required via `compliance.check_body_has_hook` — body must reference the company by name. |
| **Prompts (6, all live + stub-fallback)** | `score_fit_v1` · `personalize_email_v1` · `linkedin_dm_v1` · `followup_variant` · `prep_brief_v1` · `proposal_draft_v1` (see `Client_Acquisition_System/PROMPTS.md`) |
| **Workflows (3, markdown SOPs)** | `workflows/pipeline-flow.md` (written FIRST per build contract) · `workflows/outreach-templates.md` (6 ICP-specific scaffolds) · `workflows/discovery-call-script.md` (BANT+ 30-min framework) |
| **Test** | `python tools/run_pipeline.py --seed-fakes 5 --dry-run` → full 6-stage loop in 0.7s, 5 LinkedIn drafts + 1 prep brief + 1 proposal draft generated, 0 real sends. Negative tests: suppression list blocks re-send → `status='suppressed'`; cooldown blocks same-day repeat → `RateLimitError`. Log: `runs/2026-04-19-atlas-e2e-test.md`. |
| **Deploy** | NOT deployed. Before deploy: populate real EURI/HUNTER/RESEND/APIFY keys in `.env`; author real `config/icp.yaml` + `config/offer.yaml`; stand up a public unsubscribe endpoint; configure Resend domain + DKIM/SPF; set `DRY_RUN_DEFAULT=false`. Target infra: n8n cron (daily scrape+qualify+outreach batch) + Koyeb worker (webhook for replies → mark engaged). |
| **Reusable Parts** | `shared/compliance.py` (CAN-SPAM+DPDP footer + honest-subject/hook guards — reusable in ANY outbound email system) · `shared/rate_limit.py` (daily + cooldown pattern via JSONL sends log) · `shared/state.py` (file-based pipeline + suppression + enrich cache + transitions log — zero-dep JSON state machine) · `shared/llm.py::stub_response` (deterministic LLM stubs for dry-run / offline testing) · `tools/_load.py` (dynamic import for digit-prefixed stage folders) · seed-fakes e2e test pattern |

---

## Demo / Educational Projects

### 6. Futuristic Space Shooter
| Field | Detail |
|-------|--------|
| **Folder** | `Futuristic_Space_Shooter/` |
| **What** | Browser-based arcade game. Demonstrates AI-assisted code generation. |
| **Phase** | Educational |
| **Tech** | HTML5, CSS3, JavaScript, GSAP, Canvas API |
| **Deploy** | Static hosting (GitHub Pages, Vercel) |
| **Status** | Complete |

---

## Reusable Components Across Projects

| Component | Found In | Reuse For |
|-----------|----------|-----------|
| Telegram delivery tool | AI_News_Telegram_Bot | Any bot that sends to Telegram |
| LLM ranking/scoring | AI_News_Telegram_Bot | Content curation, lead scoring |
| Salesforce client | Salesforce_PDF_Filler | Any CRM integration |
| PDF fill + flatten | Salesforce_PDF_Filler | Document automation |
| Multi-platform publisher | Blotato_Social_Media | Social media automation |
| Web scraper with fallback | Google Maps Scraper | Any data collection |
| Excel/Sheets exporter | Google Maps Scraper | Any data pipeline |
| Tool validator | Agentic Workflow | Every project (security) |
| Cost tracker | Agentic Workflow | Every project (budget) |
| Sandbox | Agentic Workflow | Every project (security) |
| Retry with backoff | Agentic Workflow | Every API integration |
| CAN-SPAM + DPDP footer builder | Client_Acquisition_System (`shared/compliance.py`) | ANY outbound email system |
| Rate limiter (daily cap + per-target cooldown) | Client_Acquisition_System (`shared/rate_limit.py`) | Any outbound/publish tool |
| JSON state machine (prospects + transitions + suppression + cache) | Client_Acquisition_System (`shared/state.py`) | Any pipeline with stage transitions |
| LLM stub_response pattern | Client_Acquisition_System (`shared/llm.py`) | Any LLM-dependent project needing dry-run |

---

## Phase Coverage

| Phase | Automations Built | Gap |
|-------|------------------|-----|
| 1 - Automation Thinking | _(design phase, no code)_ | N/A |
| 2 - AI System Designer | Agentic Workflow Engine | None |
| 3 - No-Code Automation | News Bot, Maps Scraper | Need: CRM workflow, email sequence |
| 4 - AI-Powered Systems | Salesforce PDF Filler, RAG Knowledge Chatbot (built), AI Voice Agent (built), AI Support Ticket, Autonomous Research | Deploy + live test remain |
| 5 - Deployment | _(all projects deploy)_ | Need: dedicated deployment demo |
| 6 - Industry Playbooks | Blotato Social Media, D2C E-Commerce Suite (built) | Need: healthcare |
| 7 - AI Operator Capstone | _(not started)_ | Full AI Personal Assistant |
| 8 - Career & Business | Client Acquisition System (built) | Portfolio remains |

---

**Total Automations:** 15 (9 complete + 5 in-progress + 1 demo)
**Last Updated:** 2026-04-19 — Atlas completed **D2C_Ecommerce_Suite** (Phase 6): 5 modules, single HMAC-verified + idempotent webhook receiver, 8 prompts, 6 SOPs, shared senders reused across all 5 modules, 30/30 tests pass (25 unit + 5 webhook integration), CLI smoke pass end-to-end. Recovery = discount-only (invariant enforced in code). Inventory alerts-only (auto-order flagged false). Run log: `D2C_Ecommerce_Suite/runs/2026-04-19-d2c-build.md`. Ready for deploy dispatch. 5 projects remain in Atlas queue.
