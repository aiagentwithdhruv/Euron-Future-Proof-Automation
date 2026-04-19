# Technical Support Knowledge Base

## What this team can confirm
- Status page lives at the URL configured in the product footer.
- Account issues (login, password reset, 2FA) are self-serve from the login screen.
- Engineering investigates every technical issue within 4 business hours.
- Known incidents are posted on the status page before they're resolved.

## What we NEVER commit to in a reply
- Fix ETAs (we can never guarantee when a bug is fixed).
- Root cause details before a postmortem is published.
- Specific SLA numbers unless the customer has a signed contract.
- Workarounds that bypass security/auth.

## Safe phrasing
- "Thanks for the report — I've filed a ticket with Engineering and they'll follow up once they have an update."
- "If you're seeing login issues, try resetting your password at <login-url>. If that doesn't resolve it, reply here and I'll loop Engineering in."
- "I've captured the details. For the fastest response, please include the browser + OS you're using and a screenshot if possible."

## Common intents
1. Can't log in → suggest password reset; if already tried, escalate.
2. Feature broken → capture repro steps, escalate to Engineering.
3. Outage report → confirm receipt, direct to status page, escalate if unreported.
4. API error → ask for request ID + timestamp, escalate.
