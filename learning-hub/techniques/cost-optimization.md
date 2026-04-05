# Cost Optimization — Running AI Automations Cheaply

> **Source:** Bootcamp Phase 5 (Week 12) + production experience
> **Applies to:** Every automation using paid APIs
> **Last verified:** 2026-04-05

---

## Problem
AI API calls cost money. Students can easily burn $50+ in a day if not careful. The system must enforce budget discipline automatically.

## The Cost Hierarchy

```
FREE first:
  1. Euri API (200K tokens/day free)
  2. OpenRouter (free signup credits)
  3. Open-source models (Ollama local)

CHEAP second:
  4. gpt-4o-mini ($0.15/1M input, $0.60/1M output)
  5. claude-haiku ($0.25/1M input, $1.25/1M output)

EXPENSIVE last:
  6. gpt-4o ($2.50/1M input, $10/1M output)
  7. claude-opus ($15/1M input, $75/1M output)
```

## Pattern: Model Routing by Task

```yaml
# config/models.yaml
tasks:
  classification: euri/gpt-4o-mini    # Cheap — simple decision
  extraction: euri/gpt-4o-mini        # Cheap — structured output
  summarization: euri/gpt-4o-mini     # Cheap — compression
  generation: euri/gpt-4o-mini        # Balanced
  research: euri/gpt-4o               # Expensive — needs depth
  code_review: euri/gpt-4o            # Expensive — needs accuracy
```

## Cost Reduction Techniques

### 1. Caching (50-80% savings)
```python
import hashlib, json, os

CACHE_DIR = ".tmp/llm_cache/"

def cached_llm_call(prompt, model="gpt-4o-mini"):
    cache_key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
    cache_file = f"{CACHE_DIR}{cache_key}.json"

    if os.path.exists(cache_file):
        with open(cache_file) as f:
            return json.load(f)

    result = llm_call(prompt, model)  # Actual API call

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result
```

### 2. Prompt Length Reduction (20-40% savings)
- Strip unnecessary context from prompts
- Use system prompts for repeating instructions (cached by some providers)
- Send only the relevant chunk, not the full document

### 3. Batching (10-30% savings)
- Batch multiple small tasks into one prompt where possible
- "Classify these 10 emails" vs 10 separate "classify this email" calls

### 4. Budget Enforcement (prevents disasters)
```python
from shared.cost_tracker import check_budget, check_run_budget

# Before ANY paid API call:
check_budget()           # Daily limit: $5
check_run_budget(0.50)   # Per-run limit: $2

# After API call:
log_cost("gpt-4o-mini", 0.003, "500 tokens for classification")
```

## Gotchas

- **Loops kill budgets:** An LLM call in a loop of 1000 items = 1000 API calls. Batch or cache.
- **Streaming doesn't save money:** Same token count whether streamed or not.
- **Retries cost double:** 3 retries on a $0.10 call = $0.30. Fix the root cause.
- **Free tiers expire:** Euri resets daily, OpenRouter credits are one-time. Monitor usage.

## Related
- `api-integration.md` — how to call these APIs properly
- `deployment-patterns.md` — free hosting to keep infra costs at $0
