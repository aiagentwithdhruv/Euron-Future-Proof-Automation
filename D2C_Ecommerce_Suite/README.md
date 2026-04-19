# D2C E-Commerce Automation Suite

> 5-module integrated system: Orders + Support + Cart Recovery + Reviews + Inventory. Sellable as Rs.50K-2L D2C package.

---

## Modules

1. **Orders** — Confirmation → tracking → delivery → review request
2. **Support** — AI ticket + product KB chatbot
3. **Cart Recovery** — 1 hr → 24 hr → 3 day recovery sequence
4. **Reviews** — Collection + sentiment + auto-reply
5. **Inventory** — Stock alerts + auto-reorder suggestions

## Agentic Loop

- **Sense:** Shopify/Woo webhook
- **Think:** Classify event
- **Decide:** Flow + channel + timing
- **Act:** Multi-channel dispatch
- **Learn:** Conversion tracking tunes flows

## Setup

```bash
cp .env.example .env
# Fill Shopify / Woo + EURI + RESEND + TWILIO + AIRTABLE
```

## Run

```bash
# Local webhook receiver
uvicorn api.webhook:app --reload --port 8080

# Individual module CLIs
python modules/cart_recovery/detect_abandoned.py --dry-run
python modules/inventory/check_stock_levels.py
```

## Deploy (later)

**n8n** (webhook receiver + scheduled scans) + Airtable (dashboard). GitHub Actions as fallback for batch runs. See root `DEPLOY.md`.

---

**Phase:** 6
**Owner:** Atlas
