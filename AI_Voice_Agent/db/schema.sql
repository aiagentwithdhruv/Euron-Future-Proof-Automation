-- Supabase schema for AI Voice Agent
-- Run in Supabase SQL editor, or via `supabase db reset` with this as a seed.

-- ============ CUSTOMERS ============
create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  name text,
  phone text unique not null,
  email text,
  last_service text,
  last_booking_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_customers_phone on customers(phone);

-- ============ LEADS ============
create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  name text,
  phone text not null,
  email text,
  reason text,
  notes text,
  source text default 'inbound_voice',     -- inbound_voice | outbound_voice | web | import
  outcome text,                              -- booked | interested | not_interested | callback | voicemail | wrong_person | dnc_requested | incomplete | lead_captured
  booking_ref text,
  callback_requested boolean default false,
  callback_at timestamptz,
  follow_up_on timestamptz,
  consent_outbound boolean default false,
  consent_source text,
  last_touch timestamptz,
  last_call_at timestamptz,
  call_count int default 0,
  status text default 'new',                 -- new | contacted | qualified | won | lost
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_leads_phone on leads(phone);
create index if not exists idx_leads_outcome on leads(outcome);
create index if not exists idx_leads_consent on leads(consent_outbound);

-- ============ CALL LOGS ============
create table if not exists call_logs (
  id uuid primary key default gen_random_uuid(),
  call_id text unique not null,              -- Vapi/Bland/Retell call id
  direction text not null,                   -- inbound | outbound
  caller_phone text,
  customer_id uuid references customers(id),
  lead_id uuid references leads(id),
  transcript text,
  recording_url text,
  duration_s numeric,
  summary text,
  summary_status text default 'pending',     -- pending | ok | failed | skipped
  outcome text,
  tags text[],
  sentiment text,                            -- positive | neutral | negative
  caller_intent text,
  action_items text[],
  needs_human_review boolean default false,
  escalated boolean default false,
  escalation_reason text,
  escalation_priority text,
  confidence numeric,
  created_at timestamptz not null default now()
);

create index if not exists idx_call_logs_call_id on call_logs(call_id);
create index if not exists idx_call_logs_direction on call_logs(direction);
create index if not exists idx_call_logs_outcome on call_logs(outcome);
create index if not exists idx_call_logs_created on call_logs(created_at desc);

-- ============ DNC LIST ============
create table if not exists dnc_list (
  phone text primary key,
  reason text,
  added_at timestamptz not null default now()
);

-- ============ OUTBOUND QUEUE (optional; Vapi tracks state too) ============
create table if not exists outbound_queue (
  id uuid primary key default gen_random_uuid(),
  phone text not null,
  lead_id uuid references leads(id),
  status text default 'pending',             -- pending | placed | completed | failed | skipped
  vapi_call_id text,
  scheduled_at timestamptz default now(),
  attempts int default 0,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_outbound_status on outbound_queue(status);

-- ============ RLS NOTE ============
-- The API uses the SERVICE ROLE key which bypasses RLS.
-- If you also expose these tables to a frontend, add RLS policies per your auth model.
