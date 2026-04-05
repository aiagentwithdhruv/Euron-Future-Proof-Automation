# API Integration — Connecting Any Service

> **Source:** All bootcamp projects + production patterns
> **Applies to:** Phase 3-7, any automation that calls external APIs
> **Last verified:** 2026-04-05

---

## Problem
Every automation connects to external services. API integration is the most common source of errors (auth, rate limits, schema changes, timeouts).

## Pattern: Defensive API Integration

```
Build client --> Handle auth --> Make request
  --> Validate response --> Handle errors --> Retry if transient
    --> Log everything --> Return structured result
```

## Universal API Client Template

```python
import requests
import os
from shared.retry import retry
from shared.logger import get_logger
from shared.cost_tracker import log_cost

logger = get_logger(__name__)

class APIClient:
    def __init__(self, base_url: str, api_key_env: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            raise ValueError(f"Missing API key: {api_key_env}")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @retry(max_attempts=3, base_delay=2.0)
    def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    @retry(max_attempts=3, base_delay=2.0)
    def post(self, endpoint: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.post(url, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
```

## Auth Patterns

| Pattern | When | Example |
|---------|------|---------|
| API Key in header | Most simple APIs | `Authorization: Bearer <key>` |
| API Key in query | Some legacy APIs | `?api_key=<key>` |
| OAuth2 Client Credentials | Service-to-service | Salesforce, Google APIs |
| OAuth2 Authorization Code | User-facing | Gmail, Calendar |
| HMAC Signature | Webhooks | Stripe, Shopify |

## Error Handling Matrix

| Status | Meaning | Action |
|--------|---------|--------|
| 200-299 | Success | Process response |
| 400 | Bad request | Fix your request, don't retry |
| 401 | Unauthorized | Check/refresh API key |
| 403 | Forbidden | Check permissions/scopes |
| 404 | Not found | Check endpoint URL |
| 429 | Rate limited | Retry after `Retry-After` header |
| 500-599 | Server error | Retry with backoff (transient) |

## Gotchas

- **Always set timeout:** `timeout=30` on every request. Hanging connections kill bots.
- **Rate limit headers:** Read `X-RateLimit-Remaining` and `Retry-After`. Don't guess.
- **Pagination:** Most list APIs paginate. Always check for `next_page` or `has_more`.
- **API versioning:** Pin to a specific version (`/v1/`, `/v2/`). Unversioned APIs break without warning.
- **Response validation:** Don't trust API responses blindly. Check for expected fields.

## Related
- `webhook-patterns.md` — receiving API callbacks
- `cost-optimization.md` — managing API costs
