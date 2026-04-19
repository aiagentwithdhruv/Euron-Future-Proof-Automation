# D2C_Ecommerce_Suite — Prompts

All prompts are stored as `prompts/<name>.md` with YAML-ish frontmatter and a
strict-JSON output contract. Every prompt used at runtime MUST come through
`tools/llm.py::render()` + `generate_json()` so the frontmatter + `{{var}}`
substitution stay consistent.

---

## Prompts

| Name | File | Purpose | Variables | Category | Used by |
|------|------|---------|-----------|----------|---------|
| `order_confirmation_v1`  | `prompts/order_confirmation_v1.md` | Personalized order confirmation (email + WhatsApp) | customer_name, items, total, eta, order_name | content      | modules/orders/send_confirmation |
| `cart_recovery_v1`       | `prompts/cart_recovery_v1.md`      | Recovery email per step (1 hr / 24 hr / 3 d)        | customer_name, step, items, discount_code, discount_pct, cart_url | content      | modules/cart_recovery/send_recovery_email |
| `review_reply_positive`  | `prompts/review_reply_positive.md` | Thank a positive reviewer                           | review_text, customer_name, rating                 | content      | modules/reviews/auto_reply |
| `review_reply_negative`  | `prompts/review_reply_negative.md` | Draft make-it-right reply (human approves)          | review_text, customer_name, rating                 | content      | modules/reviews/auto_reply |
| `reorder_suggestion`     | `prompts/reorder_suggestion.md`    | One-sentence reason for a reorder qty suggestion    | sku, product_title, last_30d_sales, current_stock, velocity_per_day, days_of_cover, suggested_qty, target_cover_days | analysis     | modules/inventory/suggest_reorder |
| `classify_ticket_v1`     | `prompts/classify_ticket_v1.md`    | Classify support email (intent/priority/sentiment/team) | subject, body, intents, priorities, teams          | classification | modules/support/classify_email |
| `draft_reply_v1`         | `prompts/draft_reply_v1.md`        | Draft support reply grounded in KB chunks           | subject, body, intent, sentiment, context          | content      | modules/support/draft_reply |
| `classify_sentiment`     | `prompts/classify_sentiment.md`    | Disambiguate sentiment when rule baseline is unsure | rating, text                                       | classification | modules/reviews/classify_sentiment |

---

## Guardrails applied by code (not the prompt alone)

- `modules/support/draft_reply.strip_prices` strips `$/₹/INR/USD` amounts
  even if the LLM leaks them.
- Timing promises (`within N hours/days`) are post-filtered into
  `[timing varies]`.
- Any ticket classified as `P1` via rule keywords (legal/chargeback/safety)
  is escalated regardless of what the LLM returns.
- Review replies to negative reviews never auto-send — they sit at
  `.tmp/review_drafts/<id>.json` for human approval.

---

## Build Prompt

`ATLAS-PROMPT.md` is the full build brief for this project.

---

**Last Updated:** 2026-04-19
