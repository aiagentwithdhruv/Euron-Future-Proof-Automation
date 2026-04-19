# AI_Voice_Agent — Prompts

---

## Prompts

| Name | File | Purpose | Variables | Category |
|------|------|---------|-----------|----------|
| `receptionist_system_v1` | `prompts/receptionist_system_v1.md` | Inbound greeting + intent flow + booking script | `business_name`, `hours`, `services`, `timezone`, `recording_enabled`, `human_handoff_available` | voice-system |
| `outbound_followup_v1` | `prompts/outbound_followup_v1.md` | Outbound follow-up script for opted-in leads | `business_name`, `lead_name`, `last_touch`, `offer`, `caller_id`, `recording_enabled` | voice-system |
| `post_call_summary` | `prompts/post_call_summary.md` | Structured JSON summary + tags from a transcript | `transcript`, `call_direction`, `duration_s`, `caller_phone`, `business_name` | summary |

---

## Notes

- All three prompts live in `prompts/` as standalone markdown.
- `receptionist_system_v1` + `outbound_followup_v1` are compiled into the Vapi assistant config (see `vapi/assistant.example.json`).
- `post_call_summary` is invoked server-side by `api/services/llm_service.py` on every `/webhook/call_ended`.
- All prompts version in filename (`_v1`). Update the filename to `_v2` for breaking changes; keep old versions for comparison.

---

**Last Updated:** 2026-04-19
