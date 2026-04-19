# Knowledge Base

Each file here is a reference the LLM pulls from when drafting replies. One file per intent. Keep entries short, factual, non-committal.

**Never include pricing, promises, or PII examples.** The guardrail strips those, but they shouldn't be authored in the first place.

| File | Intent | Used by |
|------|--------|---------|
| `billing.md` | billing | Billing team drafts |
| `technical.md` | technical | Engineering drafts |
| `refund.md` | refund | Billing/Success drafts |
| `general.md` | feedback / other | Default fallback |

Add more files as intents are introduced. Extend `classify_ticket.py` intent list in parallel.
