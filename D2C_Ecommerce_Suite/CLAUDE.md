# D2C_Ecommerce_Suite — Rules

> Inherits from `../CLAUDE.md`.

---

## Project

- **Name:** D2C_Ecommerce_Suite
- **Objective:** 5-module e-commerce automation suite (orders + support + cart recovery + reviews + inventory)
- **Phase:** 6 — Industry Playbooks (Week 13: E-Commerce, D2C & Retail)
- **Status:** In Progress
- **Owner:** Atlas
- **Related:** XLwear (Rohit client) — possible cross-use

---

## Agentic Loop

1. **Sense:** Shopify/Woo webhook
2. **Think:** Classify event
3. **Decide:** Flow + channel + timing
4. **Act:** Email + WhatsApp + ticket + reorder
5. **Learn:** Track conversion per flow

---

## Tech

| Layer | Choice |
|-------|--------|
| Platform | Shopify OR WooCommerce |
| LLM | euri/gpt-4o-mini |
| Email | Resend |
| WhatsApp | Twilio |
| Store | Airtable (MVP) |
| Deploy (later) | n8n (webhooks + cron) |

---

## Project-Specific Rules

- **Shopify HMAC verification on every webhook.** No verify = drop.
- **Idempotency key on every event** — Shopify replays.
- **Never auto-charge.** Recovery = discount offer only.
- **Modules independently testable.**
- **All 5 modules reuse shared senders** (no duplicate email/WhatsApp code).
