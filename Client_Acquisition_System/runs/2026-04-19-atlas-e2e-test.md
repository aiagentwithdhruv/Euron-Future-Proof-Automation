# Atlas E2E Test — 2026-04-19

> Full 6-stage pipeline run + compliance safety-rail tests.
> **Mode:** DRY-RUN throughout. No real external calls.
> **Built by:** Atlas | **For:** Angelina (Client_Acquisition_System dispatch)

---

## Test 1 — Full pipeline, 5 fake prospects

**CLI:** `python tools/run_pipeline.py --seed-fakes 5 --dry-run`
**Duration:** 0.7s
**Result:** ✅ PASS

| Stage | Input | Output | Notes |
|-------|-------|--------|-------|
| seed | - | 5 prospects | Fake pool: Finch SaaS, Lattice Ops, Nimbus Retail, Quill Agency, Helios Legal |
| 01_scrape | (no query) | skipped | Seed replaced live scrape — expected |
| 02_enrich | 5 pending_enrich | 5 processed | Email stubs (first.last@domain), LinkedIn URLs populated, website summaries generated |
| 03_qualify | 5 pending_qualify | 5 qualified (score 78 via stub) | All passed the >=70 threshold |
| 04_outreach | 5 qualified | 5 personalized + 5 LI drafts + 5 dry-run "sends" | 0 blocked. Compliance footer injected into every email body. |
| 05_discovery | 1 auto-booked (dry-run demo) | 1 booking_link + 1 prep_brief | Booked auto-promotion only happens in --dry-run |
| 06_proposal | 1 call_done (dry-run demo) | 1 proposal draft | `.tmp/proposals/prs_dbe05a4a1f-finch-saas-2026-04-19.md` |

**Artifacts generated:**
- `.tmp/drafts/linkedin/` — 5 LinkedIn DM drafts (marked MANUAL SEND)
- `.tmp/briefs/` — 1 pre-call brief
- `.tmp/proposals/` — 1 proposal draft
- `state/pipeline.json` — 5 prospects (4 contacted, 1 proposal_draft_ready)
- `state/transitions.log` — every stage transition logged
- `state/sends.log` — 5 dry-run send receipts (for rate-limit bookkeeping)
- `state/followups.json` — 15 followups scheduled (3 per contacted prospect)

---

## Test 2 — Compliance footer present in every email

**Check:** Does `email_draft_body` contain unsubscribe URL + postal address + DPDP clause?
**Result:** ✅ PASS

Sample (Finch SaaS):
```
Hi Priya Rao, noticed Finch SaaS is hiring — looks like scale is on your mind...

---
Sent by Atlas Test Sender.
Test Co, 123 Example St, Dubai, UAE
Don't want these emails? Unsubscribe: https://example.com/unsubscribe
We process this email under legitimate-interest basis for B2B outreach (DPDP / GDPR). Reply STOP or click unsubscribe to opt out instantly.
```

CAN-SPAM requirements met:
- [x] Unsubscribe mechanism
- [x] Physical postal address
- [x] Clear sender identity
- [x] Honest subject line (no fake Re: / Fwd:)

DPDP requirements met:
- [x] Lawful basis stated (legitimate interest for B2B)
- [x] One-click opt-out (unsubscribe URL + STOP reply)

---

## Test 3 — Suppression list blocks re-send

**Setup:** Added `priya.rao@finch.example` to `state/suppression.json`, reset prospect stage to `qualified`.
**Call:** `send_email.run(prospect, dry_run=True)`
**Expected:** send blocked, status → `suppressed`
**Result:** ✅ PASS — `status='suppressed'`, no dry-run send occurred.

---

## Test 4 — Per-prospect 3-day cooldown blocks repeat send

**Setup:** Took a contacted prospect with a recorded send in `state/sends.log`.
**Call:** `rate_limit.check_and_record(prospect_id, sender)` (same day, same prospect)
**Expected:** `RateLimitError` raised
**Result:** ✅ PASS — blocked with message: `"Cooldown active for prs_..., last touch at 2026-04-19T06:35:..."`

---

## Test 5 — LinkedIn DM draft carries manual-send warning

**Expected:** Every file in `.tmp/drafts/linkedin/` includes "MANUAL SEND" banner and no send mechanism.
**Result:** ✅ PASS — each draft footer reads:
> **MANUAL SEND.** Review, edit tone, copy-paste into LinkedIn. Do NOT automate.

No tool in the system is capable of sending a LinkedIn DM programmatically. By design.

---

## Compliance Verdict

| Rule | Status |
|------|--------|
| CAN-SPAM unsubscribe in every email | ✅ |
| CAN-SPAM postal address in every email | ✅ |
| CAN-SPAM honest subject / sender | ✅ |
| DPDP lawful-basis declared | ✅ |
| DPDP one-click opt-out | ✅ |
| LinkedIn DM = draft only, human sends | ✅ |
| Rate limit: 50/day per sender | ✅ (50 hard cap in env) |
| Rate limit: 1 per prospect per 3 days | ✅ (tested) |
| Suppression list honored | ✅ (tested) |
| Personalization hook required | ✅ (compliance.check_body_has_hook) |
| DRY_RUN prevents real outbound | ✅ |

---

## Deploy Status

> ⛔ **NOT DEPLOYED.** Per Angelina's brief: built + tested, awaiting deploy dispatch.

What's needed before deploy:
1. Real API keys in `.env` (EURI_API_KEY, HUNTER_API_KEY, RESEND_API_KEY, APIFY_API_TOKEN)
2. Real ICP + offer in `config/icp.yaml` and `config/offer.yaml`
3. Set `DRY_RUN_DEFAULT=false` when ready to go live
4. Point `EMAIL_UNSUBSCRIBE_URL` at a real unsubscribe endpoint (handling opt-outs → `state/suppression.json`)
5. Configure Resend domain + DKIM/SPF

---

## Handoff

**Ping Angelina:**
> Client_Acquisition_System — built, tested, ready for deploy dispatch.
