-- ============================================================================
-- Financial Mitra — Initial Database Migration
-- 001_initial.sql
--
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New Query)
-- AFTER enabling extensions (see step 1 below).
--
-- Source of truth: 02_System_Architecture.md Section 5
-- Do NOT modify table/column names without updating the spec first.
--
-- RLS design: deny-by-default on every table.
-- The service role key (used by the backend) bypasses RLS by design.
-- Additional row-level policies are scaffolded per table below.
-- ============================================================================

-- ── Step 1: Extensions ────────────────────────────────────────────────────────
-- Enable in Supabase Dashboard → Database → Extensions if not via SQL:
CREATE EXTENSION IF NOT EXISTS vector;     -- pgvector for RAG retrieval
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid(), pgcrypto functions


-- ── Step 2: Tables (exact schema from Arch §5) ────────────────────────────────

-- Users
-- whatsapp_id_hash: hashed with server-side salt (WHATSAPP_ID_HASH_SALT).
-- The raw WhatsApp phone number is NEVER stored in plaintext.
-- The salt lives in the secrets manager, not this database.
-- See 03_Security_Compliance.md Section 4.4.
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_id_hash    TEXT UNIQUE NOT NULL,  -- salted hash, never raw phone number
    preferred_language  TEXT DEFAULT 'hi',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    last_active_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations
CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) NOT NULL,
    intent          TEXT,                           -- 'money_decision' | 'trust_check' | 'general'
    status          TEXT DEFAULT 'open',            -- 'open' | 'resolved' | 'escalated'
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- Messages
-- message_text: transcribed/extracted text.
-- APPLICATION-LEVEL ENCRYPTION DECISION: resolved as "no" for pilot.
--   Rely on Supabase disk-level encryption + short retention window.
--   If this decision is revisited post-pilot, add a 'message_text_encrypted BYTEA'
--   column here and migrate plaintext content at that time.
-- See 03_Security_Compliance.md Section 4.2.
--
-- core_engine_output and shaped_response are stored as SEPARATE columns
-- per 02_System_Architecture.md Section 5 and the pipeline spec (Section 4.4/4.7).
-- They MUST NOT be collapsed into a single field.
CREATE TABLE IF NOT EXISTS messages (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID REFERENCES conversations(id) NOT NULL,
    sender              TEXT NOT NULL,          -- 'user' | 'system'
    input_type          TEXT,                   -- 'text' | 'voice' | 'image'
    message_text        TEXT,                   -- transcribed/extracted text
    media_ref           TEXT,                   -- pointer to transient storage only (NOT the media itself)
    core_engine_output  JSONB,                  -- structured output from Core Engine (Arch §4.4)
    shaped_response     JSONB,                  -- final localised output from Shaper (Arch §4.7)
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Escalations
-- reason: 'keyword' | 'llm_flag' | 'both'
-- Per Arch §4.5: either layer triggers escalation, never requiring both.
-- The 'both' value records cases where both layers fired simultaneously.
CREATE TABLE IF NOT EXISTS escalations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id         UUID REFERENCES conversations(id) NOT NULL,
    reason                  TEXT NOT NULL,      -- 'keyword' | 'llm_flag' | 'both'
    risk_signals            JSONB,
    status                  TEXT DEFAULT 'pending',  -- 'pending' | 'acknowledged' | 'resolved'
    partner_notified_at     TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Scam pattern knowledge base (RAG)
-- embedding: vector(768) matches the Gemini models/text-embedding-004 output dimension.
-- IMPORTANT: the ivfflat index BELOW is intentionally deferred.
-- ivfflat indexes built on an empty table perform poorly — the index must be
-- created AFTER populating scam_kb_cards with real rows (Phase 3).
-- A comment in the index section marks exactly where to run it.
CREATE TABLE IF NOT EXISTS scam_kb_cards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name    TEXT NOT NULL,
    description     TEXT NOT NULL,
    example_phrasing TEXT,
    source          TEXT,
    embedding       VECTOR(768),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- North Star metric logging (anonymized)
-- NEVER store raw conversation content in this table (FR-9).
-- This table is designed to be safe to export to analytics without
-- joining back to the messages table.
CREATE TABLE IF NOT EXISTS financial_actions_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) NOT NULL,
    action_type     TEXT NOT NULL,  -- 'savings_started' | 'scam_avoided' | 'scheme_applied' | ...
    conversation_id UUID REFERENCES conversations(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log
-- Every access to raw conversation data or the escalation queue writes a row here.
-- Per 02_System_Architecture.md Section 9.6 and pilot launch checklist item 8.
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor           TEXT NOT NULL,      -- authenticated identity of the accessor
    action          TEXT NOT NULL,      -- e.g. 'viewed_escalation', 'accessed_raw_conversation'
    resource_type   TEXT,
    resource_id     UUID,
    ip_address      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Rate limit counters
-- One row per user — the row is UPSERTED each time the window resets.
-- This means the table only holds the CURRENT window per user, not history.
-- Design implication (flagged in plan): if per-window history is needed for
-- trend analysis, change the PK to (user_id, window_start) composite.
-- Implemented as per spec (Arch §5) — single-column PK.
CREATE TABLE IF NOT EXISTS rate_limit_counters (
    user_id         UUID REFERENCES users(id) PRIMARY KEY,
    window_start    TIMESTAMPTZ NOT NULL,
    request_count   INT DEFAULT 0,
    flagged         BOOLEAN DEFAULT FALSE
);


-- ── Step 3: Performance Indexes ───────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_users_whatsapp_hash
    ON users(whatsapp_id_hash);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_escalations_conversation_id
    ON escalations(conversation_id);

CREATE INDEX IF NOT EXISTS idx_escalations_status
    ON escalations(status);

CREATE INDEX IF NOT EXISTS idx_financial_actions_log_user_id
    ON financial_actions_log(user_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_actor
    ON audit_log(actor);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at
    ON audit_log(created_at);

-- ── DEFERRED: pgvector ivfflat index on scam_kb_cards ─────────────────────────
-- Run this AFTER Phase 3 populates scam_kb_cards with real rows.
-- Building ivfflat on an empty table produces a useless index.
-- Recommended: run when scam_kb_cards has at least 100 rows.
-- Replace <lists> with ceil(sqrt(num_rows)) — e.g. 10 for 100 rows.
--
-- CREATE INDEX scam_kb_cards_embedding_idx
--     ON scam_kb_cards USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 10);
--
-- After creating: run ANALYZE scam_kb_cards;


-- ── Step 4: Enable Row-Level Security on ALL tables ───────────────────────────
-- Deny-by-default: no row is accessible without an explicit policy.
-- The service role key (backend) bypasses RLS — this is intentional for
-- server-side operations. Human-facing routes enforce additional logic in
-- app/security/auth.py on top of this.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;
ALTER TABLE scam_kb_cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE financial_actions_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit_counters ENABLE ROW LEVEL SECURITY;


-- ── Step 5: RLS Policies (deny-by-default; service role bypasses) ─────────────
--
-- Policy scaffold: anon (public API) has NO access to any table.
-- Authenticated Supabase users (internal team/partner) will have policies
-- added in Phase 4 when Supabase Auth is wired in.
-- For now, all non-service-role access is blocked.

-- Users: no public access
CREATE POLICY "deny_all_users_anon" ON users
    FOR ALL TO anon USING (FALSE);

-- Conversations: no public access
CREATE POLICY "deny_all_conversations_anon" ON conversations
    FOR ALL TO anon USING (FALSE);

-- Messages: no public access
CREATE POLICY "deny_all_messages_anon" ON messages
    FOR ALL TO anon USING (FALSE);

-- Escalations: no public access
-- Phase 4 will add: authenticated team_member can read all; partner_viewer scoped
CREATE POLICY "deny_all_escalations_anon" ON escalations
    FOR ALL TO anon USING (FALSE);

-- Scam KB: anon read-only (safe — no PII, needed if we ever add a public lookup)
-- For now, deny all to be conservative; relax in Phase 3 if a public scam-check
-- API surface is added.
CREATE POLICY "deny_all_scam_kb_anon" ON scam_kb_cards
    FOR ALL TO anon USING (FALSE);

-- Financial actions log: no public access
CREATE POLICY "deny_all_financial_actions_anon" ON financial_actions_log
    FOR ALL TO anon USING (FALSE);

-- Audit log: no public access (team_member only — Phase 4)
CREATE POLICY "deny_all_audit_log_anon" ON audit_log
    FOR ALL TO anon USING (FALSE);

-- Rate limit counters: no public access
CREATE POLICY "deny_all_rate_limits_anon" ON rate_limit_counters
    FOR ALL TO anon USING (FALSE);


-- ── Verification query ────────────────────────────────────────────────────────
-- Run this after the migration to confirm all tables and RLS are set up:
--
-- SELECT tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;
--
-- Expected output: all 8 tables with rowsecurity = true.
