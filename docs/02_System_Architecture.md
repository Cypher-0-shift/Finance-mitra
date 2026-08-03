# System Architecture Document — Financial Mitra
### Team ZENVEST | v2 — Enterprise-Grade Build Spec

*Companion to `01_PRD_Financial_Mitra.md`. Supersedes the v1 architecture doc. Key changes: multimodal input pipeline (text/voice/image) with a vision-LLM call replacing self-hosted OCR, the response pipeline split into a language-agnostic Core Engine and a separate Language & Trust Shaper, and a full security layer added throughout for multi-user pilot testing.*

---

## 1. Purpose & How to Use This Doc

Read order if you're about to start coding: Section 3 (architecture) → Section 5 (data model) → Section 6 (API contracts) → Section 9 (security controls) → Section 11 (build roadmap). Section 9 is not optional reading before you open the pilot to anyone outside the core team.

---

## 2. Requirements Recap (build constraints, updated)

| Constraint | Source | Design implication |
|---|---|---|
| ₹10–₹20/user/month cost ceiling | PRD NFR | Two LLM calls per turn (engine + shaper) is now the baseline cost, not one — see Section 7 cost modeling for how to keep this in budget |
| No autonomous money movement, ever | PRD Section 4.5 | No payment APIs, no auto-apply integrations, anywhere |
| Exactly one next action per turn | FR-7 | Enforced by structured output schema at the Core Engine stage |
| Escalation mandatory for high-risk/distress | FR-5 | Hard branch in the orchestrator, runs on every turn unconditionally |
| Text, voice, **and image** all first-class | FR-1, FR-10 | Input Normalizer must treat all three as equal-priority paths, not image-as-afterthought |
| No self-hosted OCR/vision model | PRD Section 5 (out of scope) | Image handling goes through a hosted multimodal LLM call, not a GPU inference server you run yourself |
| **Multi-user pilot, real financial data** | PRD Section 10 | Every component below is designed assuming untrusted, concurrent, real users from day one — not retrofitted after a single-tester demo |

---

## 3. High-Level Architecture

```
                              ┌─────────────────────────┐
                              │   User (WhatsApp app)     │
                              │   text, voice, or photo    │
                              └────────────┬──────────────┘
                                           │
                                           ▼
                          ┌────────────────────────────────┐
                          │   Meta WhatsApp Cloud API         │
                          │   (webhook in, Graph API out)      │
                          └────────────┬─────────────────────┘
                                       │  HTTPS webhook (inbound, signed)
                                       ▼
                    ┌──────────────────────────────────────────────┐
                    │            API Gateway / Edge Layer              │
                    │   TLS termination · rate limiting · WAF rules      │
                    │   webhook signature verification (FR-11)             │
                    └───────┬──────────────────────────────────────────┘
                            ▼
                    ┌──────────────────────────────────────────────┐
                    │        Backend Orchestrator (FastAPI, stateless) │
                    │                                                    │
                    │  1. Session load/create (Postgres)                  │
                    │  2. Input Normalizer → route by modality              │
                    │  3. Intent Router                                       │
                    │  4. Core Engine (reasoning + RAG, structured output)      │
                    │  5. Risk/distress gate — runs unconditionally               │
                    │  6. Language & Trust Shaper                                    │
                    │  7. Output Adapter (text/voice) → WhatsApp Graph API             │
                    │  8. Event logging → analytics store (anonymized)                   │
                    └───┬─────────────┬─────────────┬─────────────┬───────────────────┘
                        │             │             │             │
          ┌─────────────▼─┐  ┌────────▼───────┐ ┌───▼──────────┐  ┌▼────────────────────┐
          │  STT / TTS      │  │  Vision LLM       │ │  Reasoning     │  │  RAG Retrieval          │
          │  (Bhashini)       │  │  (image → text/     │ │  LLM call        │  │  (pgvector, scam-        │
          │                    │  │  structured desc.)    │ │  (structured out)  │  │  pattern KB)              │
          └────────────────────┘  └──────────────────────┘ └────────────────────┘  └───────────────────────────┘
                        │
          ┌─────────────▼─────────────────────────────────────────────────────┐
          │                        Postgres (Supabase, RLS enabled)               │
          │  users · conversations · messages · escalations · scam_kb_cards ·       │
          │  financial_actions_log · audit_log · rate_limit_counters                  │
          └─────────────┬─────────────────────────────────────────────────────┘
                        │
          ┌─────────────▼─────────────┐        ┌──────────────────────────────┐
          │  Escalation Notifier         │───────▶│  NGO/MFI Partner Queue           │
          │  (internal, authenticated API) │        │  (authenticated dashboard/inbox)   │
          └────────────────────────────────┘        └────────────────────────────────────┘

          ┌────────────────────────────────────────────────────────────────────┐
          │                    Observability & Security Layer                     │
          │  structured logs · audit trail · error tracking · anomaly alerting ·    │
          │  secrets manager · dependency/vulnerability scanning                       │
          └────────────────────────────────────────────────────────────────────────┘
```

**What changed from v1:** an explicit API Gateway / Edge layer in front of the orchestrator (TLS, rate limiting, WAF, signature verification happen *before* your application code runs, not inside it), a Vision LLM branch alongside STT/TTS for image input, the single "generate response" step split into Core Engine + Language & Trust Shaper, and an Observability & Security layer running alongside everything else rather than bolted on.

---

## 4. Component Breakdown

### 4.1 API Gateway / Edge Layer (new)
- **Role:** the first thing any request hits. Terminates TLS, enforces rate limits per source IP and per WhatsApp user ID, applies basic WAF-style rules (reject malformed payloads, oversized images, obviously non-Meta traffic), and verifies the webhook signature before anything reaches application code.
- **Build note:** Railway's edge/proxy layer combined with FastAPI middleware can cover this at pilot scale — you don't need a dedicated CDN/WAF product yet, but the *behavior* (signature check, rate limit, reject-before-processing) must exist from day one, not be "added later."

### 4.2 Input Normalizer
- **Role:** takes whatever arrived (text, voice, image) and produces a uniform internal representation before intent routing.
  - Text → pass through, with basic sanitization (strip control characters, cap length).
  - Voice → Bhashini STT → text, with a confidence score attached; low-confidence transcriptions trigger a "did you mean to send this as text?" fallback rather than silently guessing.
  - Image → passed to a **hosted multimodal LLM call** (not a self-hosted OCR/vision model — see PRD Section 5) that returns a structured description: any readable text, and a plain description of visual context (e.g. "screenshot of a loan app requesting Aadhaar and an upfront processing fee").
- **Why a hosted multimodal call instead of dedicated OCR:** one API call instead of standing up and paying to run a GPU inference server; you get both text extraction *and* visual context understanding (useful for scam detection — the visual design of a fake scheme poster matters, not just its text) in one step; pay-per-call fits the cost ceiling far better than always-on GPU hosting.
- **Build note:** cap image size/resolution before sending to the model (both for cost and because oversized uploads are a common abuse vector), and set a hard file-type allowlist (jpeg/png only).

### 4.3 Intent Router
- Classifies normalized input into `money_decision` | `trust_check` | `general`, regardless of original modality.
- Lightweight, fast, and cheap — this can be a smaller/cheaper model call or even a fine-tuned classifier if volume justifies it later; not worth over-engineering for pilot scale.

### 4.4 Core Engine (reasoning, language-agnostic)
- Retrieves from the RAG scam-pattern knowledge base (Section 4.6), reasons about the user's situation, and produces **structured output only** — never free text directly to the user:

```json
{
  "core_message": "the substance of the answer, in neutral/English-internal form",
  "next_action": "exactly one, specific and concrete",
  "verdict": "safe_ish | be_careful | avoid | null",
  "risk_signals_detected": ["string", "..."],
  "escalation_recommended": true,
  "sources": [{"name": "RBI Annual Report on Financial Inclusion", "pattern": "upfront fee scam"}]
}
```

- Validate this against a Pydantic schema before it's allowed to proceed to the Shaper. If validation fails, retry once with a stricter prompt; if it fails again, fall back to a safe canned response rather than passing malformed content downstream.
- **Model choice:** a cheaper model handles `money_decision` and `general`; escalate to a stronger model specifically for `trust_check` reasoning, where a wrong verdict is the single worst failure mode in the product.

### 4.5 Risk & Distress Gate (safety-critical, unconditional)
- Runs on every turn, regardless of intent — two layers, either one triggers escalation:
  1. **Deterministic keyword/pattern layer** — urgency language, self-harm/distress phrasing, requests to share OTP/PIN, high-pressure tactics.
  2. **LLM-assessed layer** — the `escalation_recommended` field in the Core Engine's structured output.
- If either layer flags, the escalation branch fires (Section 4.8) *in addition to* the normal response — never instead of it, and never silently.

### 4.6 RAG Layer (Scam Pattern Knowledge Base)
- pgvector on Supabase; scam-pattern cards (name, description, example phrasing, red-flag reasoning, source citation) chunked for retrieval, not raw report text.
- Sourced from RBI Annual Report on Financial Inclusion, NGO/MFI practitioner input, Phase 1 research.
- Needs a named owner for quarterly refresh — scam tactics evolve, and a stale KB is a silent safety regression.

### 4.7 Language & Trust Shaper
- Takes the Core Engine's structured output and produces the final user-facing message:
  - Translates/localizes into the user's language (Hindi/English, extensible).
  - Applies the "warm friend" register defined in PRD Section 8 — plain words, no jargon, no lecturing tone.
  - Converts `sources` into a legible trust cue ("this matches a pattern the RBI has warned about") rather than a citation format.
  - Packages for the correct output modality (Section 4.9).
- **Model choice:** this stage's job (translate + tone, not reason) is easier than the Core Engine's — use a cheaper/faster model here to help offset the two-call cost increase (Section 7).

### 4.8 Escalation Notifier
- On trigger: writes an `escalations` row, notifies the NGO/MFI partner via an **authenticated** internal API (Section 9.2) — no public, unauthenticated queue.
- v1 build stays low-tech: a notification to a partner-side channel is enough for a pilot; don't build a full dashboard before a partner needs one.
- SLA for partner response time must be agreed with the partner in writing before pilot launch (PRD Section 13).

### 4.9 Output Adapter
- Matches output modality to input modality by default (FR-6): voice in → voice out (via Bhashini TTS), text in → text out, image in → text out (a spoken description of an image reply is unnatural) with an option for the user to request voice instead.

### 4.10 Analytics / North Star Logging
- Logs event type, whether a meaningful financial action was completed, timestamp, and an anonymized user identifier — never raw conversation, voice, or image content (FR-9).
- Anonymization approach (hashed WhatsApp ID, no reversible mapping stored alongside content) must be implemented before any real user testing, not just documented.

### 4.11 Observability & Security Layer (new, runs alongside everything)
- Structured logging across all components, with an **audit trail** specifically for: who accessed the escalation queue, who accessed raw conversation data, and every authentication event on internal tooling.
- Error tracking via cloud dashboards so failures during pilot testing are caught quickly, not discovered via a user complaint.
- Anomaly alerting on rate-limit triggers, repeated failed auth attempts, and unusual cost spikes per user.
- Secrets manager (Railway env vars at minimum; a dedicated secrets manager if the team scales past a handful of services) — nothing sensitive in source control, ever.
- Dependency/vulnerability scanning on the codebase (e.g. `pip-audit`, GitHub Dependabot) as a routine, not a one-time check.

---

## 5. Data Model (Postgres / Supabase, updated)

```sql
-- Extensions
create extension if not exists vector;
create extension if not exists pgcrypto;

-- Users
create table users (
  id uuid primary key default gen_random_uuid(),
  whatsapp_id_hash text unique not null,  -- hashed, never store raw WhatsApp number in plaintext
  preferred_language text default 'hi',
  created_at timestamptz default now(),
  last_active_at timestamptz default now()
);

-- Conversations
create table conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) not null,
  intent text,
  status text default 'open',            -- 'open' | 'resolved' | 'escalated'
  started_at timestamptz default now(),
  resolved_at timestamptz
);

-- Messages (input_type now includes 'image')
create table messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) not null,
  sender text not null,                  -- 'user' | 'system'
  input_type text,                       -- 'text' | 'voice' | 'image'
  message_text text,                     -- transcribed/extracted text; consider app-level encryption
  media_ref text,                        -- pointer to transient media storage, NOT the media itself long-term
  core_engine_output jsonb,              -- structured output from Section 4.4
  shaped_response jsonb,                 -- final localized output, if sender='system'
  created_at timestamptz default now()
);

-- Escalations
create table escalations (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) not null,
  reason text not null,                  -- 'keyword' | 'llm_flag' | 'both'
  risk_signals jsonb,
  status text default 'pending',         -- 'pending' | 'acknowledged' | 'resolved'
  partner_notified_at timestamptz,
  created_at timestamptz default now()
);

-- Scam pattern knowledge base
create table scam_kb_cards (
  id uuid primary key default gen_random_uuid(),
  pattern_name text not null,
  description text not null,
  example_phrasing text,
  source text,
  embedding vector(1536),
  updated_at timestamptz default now()
);

-- North Star metric logging (anonymized, decoupled from conversation content)
create table financial_actions_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) not null,
  action_type text not null,             -- 'savings_started' | 'scam_avoided' | 'scheme_applied' | ...
  conversation_id uuid references conversations(id),
  created_at timestamptz default now()
);

-- Audit log (new) — every access to sensitive data or internal tooling
create table audit_log (
  id uuid primary key default gen_random_uuid(),
  actor text not null,                   -- authenticated identity of the accessor
  action text not null,                  -- e.g. 'viewed_escalation', 'accessed_raw_conversation'
  resource_type text,
  resource_id uuid,
  ip_address text,
  created_at timestamptz default now()
);

-- Rate limiting (new) — per-user request counters for abuse prevention
create table rate_limit_counters (
  user_id uuid references users(id) primary key,
  window_start timestamptz not null,
  request_count int default 0,
  flagged boolean default false
);
```

**Design notes:**
- `whatsapp_id_hash` replaces storing the raw phone number — hash with a server-side secret salt, never store the reversible mapping in the same table.
- Row-Level Security (RLS) policies enabled on every table from day one: application service role has scoped access; no table is publicly readable via the Supabase API by default.
- `media_ref` deliberately does not store voice/image content long-term in the primary database — see Section 9.3 for transient media handling.

---

## 6. API Contracts

### 6.1 Inbound webhook (from Meta)
```
POST /webhook/whatsapp
Headers: X-Hub-Signature-256 (verified against app secret — reject if invalid, FR-11)
Body: Meta's standard WhatsApp webhook payload
Response: 200 OK immediately; actual processing happens async (background task/queue),
          not inline with the webhook response
```

### 6.2 Outbound send (to Meta Graph API)
```
POST https://graph.facebook.com/v{version}/{phone_number_id}/messages
Headers: Authorization: Bearer {access_token}  -- from secrets manager, never hardcoded
Body: { messaging_product: "whatsapp", to: "...", type: "text"|"audio", text/audio: {...} }
```

### 6.3 Internal escalation notification (authenticated, new)
```
POST /internal/escalate
Headers: Authorization: Bearer {internal_service_token}  -- service-to-service auth, not public
Body: { conversation_id, reason, risk_signals }
→ writes escalations row, notifies partner channel, writes audit_log entry
```

### 6.4 Internal admin/escalation queue access (new)
```
GET /internal/escalations
Headers: Authorization: Bearer {authenticated_session_token}
→ requires role check (team-member or authorized-partner role)
→ every access writes an audit_log entry (who, when, what was viewed)
```

### 6.5 Core Engine call shape (conceptual)
```
System prompt: Product Principles + structured-output schema (Section 4.4) + retrieved RAG context
Input: normalized text (from text/voice/image path)
Output: validated JSON matching the Core Engine schema
```

### 6.6 Language & Trust Shaper call shape (conceptual)
```
System prompt: persona/tone instructions (PRD Section 8) + target language
Input: Core Engine's structured output
Output: final user-facing text, ready for the Output Adapter
```

---

## 7. Cost Modeling (updated for two-call pipeline)

| Item | Notes |
|---|---|
| WhatsApp Cloud API | Free tier sufficient for pilot; re-check once past free conversation limit |
| STT/TTS (Bhashini) | Low/free; confirm current pricing before scale |
| Vision LLM call (image input) | New cost line vs. v1 — only incurred on image-input turns, not every turn |
| Core Engine LLM call | Cheap model for `money_decision`/`general`; stronger model reserved for `trust_check` |
| Language & Trust Shaper call | Cheaper/faster model — offsets the two-call increase |

**Implication:** the two-call split (Section 4.4 + 4.7) is the right product architecture, but it's a real cost increase over the v1 single-call design. Keep it in budget by (a) using the cheapest viable model for the Shaper stage, since its job is mechanically simpler, and (b) only escalating to a stronger model for the Core Engine on `trust_check`, not by default on every intent.

---

## 8. Reliability & Fallback

- **WhatsApp Cloud API downtime:** queue outbound messages with backoff; send an immediate acknowledgment for inbound messages that can't be fully processed within a few seconds, rather than leaving silence.
- **LLM API failure/timeout (either stage):** fall back to a canned safe response with an escalation contact, never a broken or hallucinated reply.
- **STT/vision-LLM low confidence:** ask the user to resend as text rather than guessing — this applies to both blurry/unclear images and unclear audio.
- **Rate-limit trip:** throttle with a polite in-band message ("you're sending messages faster than I can keep up — give me a moment"), not a silent drop.

---

## 9. Security Controls (implementation detail — see `03_Security_Compliance.md` for full threat model)

This section lists what must exist in the codebase/infra before pilot testing opens beyond the core team. Full rationale, threat model, and compliance mapping live in the dedicated Security & Compliance document — this is the build checklist.

### 9.1 Transport & storage
- TLS enforced everywhere (Railway/Supabase default to this — verify, don't assume).
- Encryption at rest via Supabase's default disk encryption; evaluate application-level encryption for `messages.message_text` given sensitivity.
- No media (voice/image) retained long-term in primary storage without an explicit, documented reason and retention window — see Section 9.3.

### 9.2 Authentication & access control
- All internal tooling (escalation queue, admin views, any future dashboard) requires authenticated login — no shared credentials, no unauthenticated links.
- Role-based access: team-member role vs. authorized-partner role, with different data visibility.
- Service-to-service calls (e.g. escalation notifier → internal API) use service tokens, not user credentials.

### 9.3 Media handling
- Voice notes and images are processed and then deleted from transient storage within a short, defined window (e.g. 24–48 hours) unless explicitly retained for a documented quality-review purpose with user awareness.
- Never pass raw media directly into logs or error trackers — redact or reference by ID only.

### 9.4 Rate limiting & abuse prevention
- Per-user and per-IP rate limits enforced at the Edge Layer (Section 4.1).
- Per-user cost caps — if a single user's LLM spend in a day exceeds a threshold, throttle and alert, don't just let it run.
- Basic prompt-injection resistance: treat all user input (text, transcribed voice, and especially extracted image text) as untrusted content, never as instructions to the system — the Core Engine's system prompt must explicitly guard against injected instructions claiming to override product principles.

### 9.5 Secrets & dependencies
- All API keys/tokens in environment variables via Railway, never in the repo.
- Routine dependency vulnerability scanning (Dependabot or equivalent) as part of the normal workflow, not a pre-launch afterthought.

### 9.6 Audit & incident response
- Every access to raw conversation data or the escalation queue writes an `audit_log` row (Section 5).
- A documented, even if simple, incident response plan: who's notified, what's the immediate containment step, and what's communicated to affected users if there's a data exposure — written *before* the pilot, not drafted during an actual incident.

---

## 10. Tech Stack Summary

*(Full comparison and rationale in `04_Tech_Stack.md` — this is the quick-reference version.)*

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python), async |
| Hosting | Railway |
| Database | Supabase (Postgres + pgvector + RLS) |
| Messaging | Meta WhatsApp Cloud API (direct) |
| STT/TTS | Bhashini (primary) |
| Image understanding | Hosted multimodal LLM call (no self-hosted vision model) |
| Core Engine LLM | Cheap model default; stronger model for trust-check |
| Shaper LLM | Cheap/fast model |
| RAG | pgvector on Supabase |
| Secrets | Railway environment variables |
| Error tracking | Built-in cloud console logs |
| Dependency scanning | Dependabot or `pip-audit` |

---

## 11. Build Roadmap (updated sequencing)

**Phase 0 — Setup:** Meta Developer account + Business verification (has lead time), Supabase + Railway scaffolding, Bhashini access, **and** security baseline setup (secrets manager, RLS policies, audit_log table) — done in parallel with Phase 0, not deferred.

**Phase 1 — Skeleton pipeline:** webhook receive (with signature verification from the start) → echo text back → session persistence.

**Phase 2 — Core conversational logic:** intent classification, Core Engine structured-output integration for `money_decision` (text only first), schema validation + fallback logic.

**Phase 3 — Trust-check + RAG:** populate `scam_kb_cards`, pgvector retrieval, `trust_check` flow, Language & Trust Shaper stage introduced here (test the split on this flow first, since it's the highest-value use case for source-citing).

**Phase 4 — Safety layer:** keyword/pattern risk detection, escalation record + authenticated notification, audit logging on escalation access. **Do not proceed to Phase 6 without a real NGO/MFI partner and written SLA in place.**

**Phase 5 — Multimodal expansion:** voice (STT/TTS, tested against real target-user audio), then image (vision LLM call, tested against real-world photo conditions — glare, blur, low-end cameras).

**Phase 6 — Security hardening & pilot readiness:** rate limiting live and tested, per-user cost caps enforced, incident response plan written and reviewed by the team, DPDP-aligned retention/anonymization policy implemented (not just documented), and a small closed pilot with a handful of real users before any wider rollout.

---

## 12. Open Technical Decisions

- Exact LLM provider/model choice for each of the three call types (Core Engine default, Core Engine trust-check, Shaper) — needs a small bake-off on Hindi/code-mixed accuracy, image understanding quality, and cost.
- Bhashini vs. alternative STT/TTS — needs real accent/noise testing before Phase 5.
- NGO/MFI partner identity and escalation SLA — blocker for Phase 4/6.
- Whether application-level encryption for message content is worth the added complexity for a pilot-scale deployment, or whether Supabase's disk-level encryption is sufficient given the retention window is short (Section 9.3) — worth a explicit team decision, not a default.

---

*Companion documents: `01_PRD_Financial_Mitra.md`, `03_Security_Compliance.md`, `04_Tech_Stack.md`.*
