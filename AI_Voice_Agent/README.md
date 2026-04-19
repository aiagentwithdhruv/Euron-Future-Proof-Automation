# AI Voice Agent

> Inbound AI receptionist + outbound follow-up caller. Vapi-powered. FastAPI backend exposes deterministic tool endpoints that the voice platform calls.

---

## What It Does

**Inbound:** Caller dials your business number → Vapi picks up → AI receptionist greets → captures intent → books appointments on Google Calendar → fires SMS + email via Twilio/Resend → logs transcript + summary to Supabase.

**Outbound:** CSV of opted-in leads → script validates consent / DNC / time window → Vapi places the call → AI delivers a personalized follow-up → captures outcome → updates CRM.

## Agentic Loop

- **Sense:** Incoming call OR outbound task from queue
- **Think:** LLM classifies intent (inbound) OR personalizes pitch (outbound)
- **Decide:** Pick script branch, call the right tool endpoint
- **Act:** Calendar, CRM, confirmations, escalation
- **Learn:** Post-call summary + tags → Supabase

## Architecture

```
Caller ── Vapi ── HTTPS ──> FastAPI (api/main.py)
                             ├─ /tool/check_availability
                             ├─ /tool/book_appointment
                             ├─ /tool/capture_lead
                             ├─ /tool/lookup_customer
                             ├─ /tool/escalate_to_human
                             ├─ /tool/send_confirmation
                             └─ /webhook/call_ended
                                 └─> Supabase + Calendar + Twilio + Resend + Euri LLM
```

Three-layer separation: **routes** (thin) → **services** (business logic) → **external APIs**. No SQL or API calls in routes.

## Setup

```bash
cd AI_Voice_Agent
cp .env.example .env        # fill keys — see below
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Required keys for a full inbound flow

- `API_KEY` — shared secret (the voice platform sends this on every tool call)
- `VAPI_API_KEY` + `VAPI_ASSISTANT_ID` (outbound also needs `VAPI_PHONE_NUMBER_ID`)
- `EURI_API_KEY` — free 200K tokens/day, covers summaries
- `GOOGLE_CALENDAR_ID` + `GOOGLE_SERVICE_ACCOUNT_JSON` — booking
- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` — CRM + call logs
- `TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM` — SMS confirmations (optional)
- `RESEND_API_KEY` + `EMAIL_FROM` — email confirmations (optional)
- `HUMAN_HANDOFF_NUMBER` — transfer target (optional; falls back to callback capture)

The app **starts** even without these — `/healthz` will report which services are configured. Only the routes that need a specific service will fail when called.

## Database

Run `db/schema.sql` in Supabase's SQL editor. Creates: `customers`, `leads`, `call_logs`, `dnc_list`, `outbound_queue`.

## Vapi Setup

1. Create an assistant in Vapi dashboard.
2. Start from `vapi/assistant.example.json` — replace `YOUR_TUNNEL`, `{{BUSINESS_NAME}}`, `{{API_KEY}}`, `{{HUMAN_HANDOFF_NUMBER}}`.
3. Paste the compiled `prompts/receptionist_system_v1.md` (with variables interpolated) as the system message.
4. Point tool URLs + `serverUrl` at your tunnel URL.
5. Send `X-Api-Key` header matching your `API_KEY`.

## Run

```bash
uvicorn api.main:app --reload --port 8080
```

In a second terminal:

```bash
cloudflared tunnel --url http://localhost:8080       # or: ngrok http 8080
```

Paste the tunnel URL into Vapi's assistant config. Place a **test call from the Vapi dashboard** (web mic — no real phone number needed).

## Outbound

```bash
python tools/queue_outbound.py --csv leads.example.csv --dry-run
# Review the plan, then:
python tools/queue_outbound.py --csv leads.example.csv
```

Script **blocks** on any row failing consent / DNC / time-window / attempt-cap checks. No flag bypasses these — they are regulatory.

## Offline Transcript Summary (debugging)

```bash
python tools/summarize_call.py --transcript path/to/transcript.txt --duration 180
# Or pipe:
cat transcript.txt | python tools/summarize_call.py --transcript -
```

## Compliance Checklist

- [x] Consent mandatory for outbound (enforced in `queue_outbound.py`)
- [x] DNC list check before every outbound call
- [x] Time-of-day gate (configurable per env)
- [x] Max 3 attempts per lead
- [x] Recording disclosure scripted into the prompt
- [x] "Talk to human" escalates immediately (no AI gating)
- [x] Every call logged — transcript + summary + tags
- [x] API_KEY required on every tool + webhook endpoint

## Deploy (later)

Koyeb (always-on FastAPI) + set env vars from `.env.example`. Point Vapi at the Koyeb URL. Do NOT deploy until inbound + outbound test calls pass end-to-end.

---

**Phase:** 4
**Owner:** Atlas
**Platform default:** Vapi
