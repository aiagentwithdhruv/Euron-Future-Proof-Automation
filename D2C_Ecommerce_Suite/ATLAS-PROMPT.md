# Atlas — D2C E-Commerce Automation Suite

> **Persona:** Atlas, backend engineer at Angelina-OS.
> **Dispatched by:** Angelina.
> **Rule #0:** If unclear, STOP and ask Angelina.
> **Note:** Related to XLwear (Rohit's client rebuild). Cross-reference if Dhruv says so.

---

## Read Before You Code (Mandatory)

1. `../CLAUDE.md` — root rules
2. `../learning-hub/ERRORS.md`
3. `../learning-hub/automations/CATALOG.md`
4. `../Multi_Channel_Onboarding/` — reuse email/WhatsApp senders
5. `../AI_Support_Ticket_System/` — reuse ticket classifier for support sub-module
6. `../RAG_Knowledge_Chatbot/` — reuse for product knowledge chatbot
7. `../Agentic Workflow for Students/shared/` — shared modules
8. `../student-starter-kit/agents/backend-builder.md` — persona

---

## Objective (one sentence)

**Complete D2C automation suite: order lifecycle + AI support + abandoned cart recovery + review management + inventory alerts — one integrated system, sellable as Rs.50K-2L package.**

---

## Agentic Loop (across all 5 sub-modules)

- **Sense:** Shopify/Woo webhook event (order created / cart abandoned / review / stock low)
- **Think:** Classify event → decide flow (confirm order / recover cart / reply review / reorder stock)
- **Decide:** Message template + channel + timing + escalation
- **Act:** Send email/WhatsApp, update CRM, create support ticket, trigger reorder
- **Learn:** Track conversion per flow → tune timing + copy

---

## Build Contract

1. Modular — 5 sub-modules under `modules/`:
   - `modules/orders/` — order lifecycle (confirmation → ship → deliver → review)
   - `modules/support/` — AI ticket + KB (reuse RAG_Knowledge_Chatbot)
   - `modules/cart_recovery/` — abandoned cart
   - `modules/reviews/` — review collection + auto-reply
   - `modules/inventory/` — stock alerts + auto-reorder suggestions
2. Single webhook receiver routes events to modules
3. One unified dashboard (Airtable MVP OR Next.js later)
4. Test each module independently → full integration test
5. DO NOT deploy

---

## Tools to Build

### Shared
| Tool | Purpose |
|------|---------|
| `api/webhook.py` | Shopify/Woo webhook receiver (FastAPI) |
| `tools/shopify_client.py` | Shopify API wrapper |
| `tools/woo_client.py` | WooCommerce API wrapper |
| `tools/dashboard.py` | CLI metrics view (orders, recovered carts, tickets, reviews) |

### modules/orders/
- `send_confirmation.py` — order confirmation email + WhatsApp
- `tracking_update.py` — shipping status notification
- `request_review.py` — post-delivery review ask

### modules/support/
- `classify_email.py` — reuse from AI_Support_Ticket_System
- `draft_reply.py` — use RAG on product KB
- `ticket_workflow.py` — full lifecycle

### modules/cart_recovery/
- `detect_abandoned.py` — scheduled job (cron every 30 min)
- `send_recovery_email.py` — sequence: 1 hr / 24 hr / 3 days
- `track_recovery.py` — attribution tracker

### modules/reviews/
- `collect_reviews.py` — from Shopify + Google + Trustpilot
- `classify_sentiment.py` — positive / neutral / negative
- `auto_reply.py` — thank positive, escalate negative

### modules/inventory/
- `check_stock_levels.py` — poll daily
- `alert_low_stock.py` — Slack + email when below threshold
- `suggest_reorder.py` — LLM analyzes velocity → suggests order qty

---

## Workflow SOPs

One per sub-module:
- `workflows/order-lifecycle.md`
- `workflows/support-flow.md`
- `workflows/cart-recovery.md`
- `workflows/review-management.md`
- `workflows/inventory-alerts.md`

Plus master: `workflows/master-orchestration.md` — how webhook routes to sub-modules.

---

## APIs / Tools

| API | Free Tier | Used For |
|-----|-----------|----------|
| Shopify Partner | Dev store free | Shopify |
| WooCommerce | Open-source | Woo (alt) |
| Euri | 200K tokens/day | LLM |
| Resend | 100/day | Email |
| Twilio / Meta | Trial | WhatsApp |
| Airtable | Free | Dashboard (MVP) |

---

## Env Vars

```
# Store
SHOPIFY_STORE_DOMAIN=
SHOPIFY_ACCESS_TOKEN=

WOO_URL=
WOO_CONSUMER_KEY=
WOO_CONSUMER_SECRET=

# LLM
EURI_API_KEY=

# Channels
RESEND_API_KEY=
EMAIL_FROM=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=

# Store
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=

# Notify
SLACK_WEBHOOK_URL=

# Config
ABANDONED_CART_DELAY_MIN=60
LOW_STOCK_THRESHOLD=10
REVIEW_REQUEST_DELAY_DAYS=7
```

---

## Rules of Engagement

- **Doubt = STOP.** Questions:
  - "Which platform — Shopify or WooCommerce? Both?"
  - "Is this tied to XLwear or a generic template?"
  - "Review platforms — Shopify native, Google, Trustpilot — which ones?"
  - "Inventory module — auto-order enabled or alerts-only?"
- **Webhooks must be signed-verified** — Shopify HMAC check mandatory.
- **Idempotency KEY** on every webhook — Shopify replays events.
- **Never auto-charge customers.** Recovery = discount offer, not charge.

---

## Test Command

```bash
cd D2C_Ecommerce_Suite
uvicorn api.webhook:app --reload --port 8080
# Use ngrok → register URL in Shopify Partner
# Create test order on dev store → verify flow
```

---

## When Done

Update catalog + techniques file. Ping Angelina.
