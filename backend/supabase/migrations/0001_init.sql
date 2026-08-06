-- Wakalah schema v1 — mandates, decisions, and the evidence audit trail.
--
-- Apply with the Supabase MCP (apply_migration) or the Supabase CLI. Never edit
-- a released migration in place: add 0002_*.sql instead, so any environment can
-- rebuild the exact same database by replaying files in order.
--
-- Privacy design worth knowing: the audit tables are keyed by `principal_ref`,
-- a SHA-256 hash of the phone number, not the number itself. The long-lived,
-- fast-growing tables therefore hold no raw subscriber identifiers. Only
-- `mandates` keeps the MSISDN, because the service needs it to call the network
-- (and on the sandbox those numbers are Nokia's simulators, not real people).

-- ---------------------------------------------------------------- mandates
create table if not exists public.mandates (
    mandate_id              text primary key,
    principal_ref           text not null,           -- sha256(msisdn); the audit key
    principal_id            text not null default '', -- display identity
    principal_msisdn        text not null,            -- needed to call the network
    agent_id                text not null,
    agent_key_fingerprint   text not null,            -- the token is bound to this keypair
    scope                   jsonb not null,
    status                  text not null default 'active',
    risk_score              double precision not null default 0,
    policy_version          text not null default 'v1',
    revoked_reason          text,
    created_at              timestamptz not null default now(),
    expires_at              timestamptz
);

create index if not exists mandates_principal_ref_idx on public.mandates (principal_ref);
create index if not exists mandates_status_idx on public.mandates (status);

-- --------------------------------------------------------------- decisions
create table if not exists public.decisions (
    transaction_id      text primary key,
    mandate_id          text not null references public.mandates (mandate_id),
    principal_ref       text not null,
    verdict             text not null,               -- allow | step_up | deny
    risk_tier           text not null,               -- low | medium | high
    agent_proposal      text,                        -- what the AI proposed, before policy
    policy_overrode     boolean not null default false,
    reason_codes        jsonb not null default '[]'::jsonb,
    rationale           text not null default '',
    policy_version      text not null,
    amount              double precision,
    currency            text,
    beneficiary_id      text,
    latency_ms          integer,
    decided_at          timestamptz not null default now()
);

-- The two questions this table is asked: "show me this principal's history"
-- and "show me what we decided recently".
create index if not exists decisions_principal_ref_idx on public.decisions (principal_ref);
create index if not exists decisions_decided_at_idx on public.decisions (decided_at desc);
create index if not exists decisions_mandate_id_idx on public.decisions (mandate_id);

-- ---------------------------------------------------------------- evidence
-- One row per signal per decision: the evidence that justified a verdict, with
-- the compliance context (purpose, legal basis, consent) attached to each.
create table if not exists public.decision_evidence (
    id              bigint generated always as identity primary key,
    transaction_id  text not null references public.decisions (transaction_id) on delete cascade,
    signal          text not null,
    dimension       text not null,                   -- binding|identity|hijack|continuity|context
    provider        text not null default 'nokia_nac',
    result          jsonb not null default '{}'::jsonb,
    source          text not null,                   -- live|cached|replay|simulated|unavailable
    purpose         text not null default 'FraudPreventionAndDetection',
    legal_basis     text not null default 'legitimate_interest',
    consent_status  text not null default 'not_required_at_runtime',
    ok              boolean not null default true,
    error_code      text,
    latency_ms      integer,
    evidence_time   timestamptz not null default now()
);

create index if not exists decision_evidence_tx_idx on public.decision_evidence (transaction_id);

-- ------------------------------------------------------------------- RLS
-- These tables are reached only by the backend using the service key, which
-- bypasses RLS. Enabling RLS with no policies means that if the Data API ever
-- exposes them, anon and authenticated roles can read nothing. Default deny.
alter table public.mandates            enable row level security;
alter table public.decisions           enable row level security;
alter table public.decision_evidence   enable row level security;

revoke all on public.mandates          from anon, authenticated;
revoke all on public.decisions         from anon, authenticated;
revoke all on public.decision_evidence from anon, authenticated;
