# Financial Mitra

> WhatsApp-first AI financial companion for low-income, informal-income users in India.
> Built by Team ZENVEST. Current status: **Phase 0 Complete — Paused for Live Provisioning & Human Confirmation Gates**.

---

## What This Is

Financial Mitra helps users make confident everyday financial decisions and avoid scams — through plain-language conversations in Hindi or English, via WhatsApp. In v1 MVP, it accepts text and photos only (voice notes deferred to v1.x). Output is text-only.

Two trigger moments in v1:
1. **"What do I do with money I have?"** — guided financial decision flow
2. **"Is this offer trustworthy?"** — scam/scheme trust-check with a clear verdict

Read the full spec before modifying anything: `01_PRD_Financial_Mitra.md`, `02_System_Architecture.md`, `03_Security_Compliance.md`, `04_Tech_Stack.md`.

---

## Project Structure

```
financial-mitra/
├── app/
│   ├── main.py                  # FastAPI app factory, lifespan, /health
│   ├── config.py                # Pydantic Settings (all env vars, startup guard)
│   ├── dependencies.py          # Shared FastAPI dependencies
│   ├── routers/
│   │   ├── webhook.py           # POST /webhook/whatsapp (Meta inbound)
│   │   └── internal.py          # /internal/* (escalation queue, Phase 4)
│   ├── services/
│   │   ├── whatsapp.py          # Meta Graph API outbound client
│   │   ├── session.py           # Conversation/session persistence
│   │   └── audit.py             # audit_log writer
│   ├── engines/
│   │   ├── core_engine.py       # Core Engine — Gemini reasoning (isolated module)
│   │   ├── shaper.py            # Language & Trust Shaper (isolated module)
│   │   ├── intent_router.py     # Intent classification (isolated module)
│   │   └── vision.py            # Vision LLM — Phase 5 stub
│   ├── schemas/
│   │   ├── core_engine.py       # Pydantic schema for Core Engine output (Arch §4.4)
│   │   ├── webhook.py           # Meta webhook payload models
│   │   └── internal.py          # Internal API models
│   ├── security/
│   │   ├── signature.py         # HMAC-SHA256 webhook verification (FR-11)
│   │   └── auth.py              # Internal API role-based auth
│   └── db/
│       ├── client.py            # Supabase async client
│       └── migrations/
│           └── 001_initial.sql  # Full schema + RLS + extensions
├── tests/
│   ├── test_signature.py        # Webhook sig verification tests
│   ├── test_core_schema.py      # Core Engine Pydantic schema tests
│   └── test_risk_gate.py        # Risk/distress gate tests
├── .github/
│   ├── workflows/keep-alive.yml # Render + Supabase keep-alive (every 10 min)
│   └── dependabot.yml           # Weekly dependency vulnerability scan
├── .env.example                 # All env vars listed — copy to .env, fill in values
├── .gitignore                   # .env is listed — never commit secrets
├── render.yaml                  # Render deployment blueprint
├── requirements.txt             # Pinned Python dependencies
└── pyproject.toml               # pytest, coverage config
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- A Supabase project (with `vector` and `pgcrypto` extensions enabled)
- A Gemini API key (Google AI Studio)

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in all values
```

**Minimum values needed to start locally (dev mode):**
- `WHATSAPP_VERIFY_TOKEN` — any string
- `WHATSAPP_APP_SECRET` — any string for local dev
- `WHATSAPP_ACCESS_TOKEN` — placeholder
- `WHATSAPP_PHONE_NUMBER_ID` — placeholder
- `SUPABASE_URL` — your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` — your service role key
- `SUPABASE_ANON_KEY` — your anon key
- `GEMINI_API_KEY` — your Gemini API key
- `WHATSAPP_ID_HASH_SALT` — any 32+ char random string (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`)
- `INTERNAL_SERVICE_TOKEN` — any random string
- `RENDER_HEALTH_CHECK_TOKEN` — any random string

### 3. Run the database migration

Copy `app/db/migrations/001_initial.sql` and run it in the Supabase SQL editor.
Then verify: `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';`
— all 8 tables should show `rowsecurity = true`.

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

The app starts on `http://localhost:8000`. Check `/health` to confirm DB connectivity.

### 5. Run tests

```bash
pytest tests/ -v
```

All three test suites pass without live credentials (pure logic tests).

---

## Deployment (Render)

1. Create a Render account and connect this GitHub repo as a new **Web Service**.
2. Render will auto-detect `render.yaml` — use the **Blueprint** deployment option.
3. Set all environment variables from `.env.example` in the Render Dashboard → Environment.
4. **Critical:** Set `ENVIRONMENT=production` and `GEMINI_TIER=paid`.
5. Add `RENDER_APP_URL` and `RENDER_HEALTH_CHECK_TOKEN` as **GitHub Actions secrets** (for the keep-alive workflow).

### ⚠️ Known Pilot-Stage Limitation: Cold Start

Render's free tier spins down after 15 minutes of inactivity. The first message after any idle period will have a **30–60 second delay**, which conflicts with the PRD's sub-5-second latency target.

**Mitigation:** The keep-alive workflow (`.github/workflows/keep-alive.yml`) pings `/health` every 10 minutes to prevent spin-down during active hours.

**Permanent fix:** Upgrade to a paid Render instance type before the pilot opens to real users.

---

## Critical: GEMINI_TIER Setting

```
⚠️ DATA PRIVACY GATE — READ BEFORE GOING LIVE
```

Gemini's **free tier** allows Google to use submitted prompts and responses to train their models. Gemini's **paid tier** (billing enabled on the GCP project) excludes this by default.

This is a direct conflict with the DPDP Act 2023 purpose-limitation commitment for real users' financial conversations.

**The app hard-blocks startup if `ENVIRONMENT=production` and `GEMINI_TIER=free`.**

Before any real-user traffic:
1. Enable billing on your Google Cloud project
2. Set `GEMINI_TIER=paid` in Render environment variables

Development and testing on synthetic data can use `GEMINI_TIER=free`.

---

## Phase Status

| Phase | Codebase Implementation | Operational & Gate Status | Action Required |
|---|---|---|---|
| **Phase 0 — Setup** | ✅ Scaffold & SQL Migrations Complete | 🟡 Paused at 0→1 Gate | Awaiting human confirmation that Meta, Supabase, and Render services are provisioned in production. |
| **Phase 1 — Skeleton Pipeline** | 📦 Authored (Mock-tested only) | ⏳ Blocked by 0→1 Gate | Untested against live Meta WhatsApp Cloud endpoints & real Supabase network connections. |
| **Phase 2 — Core Conversational** | 📦 Authored (Mock-tested only) | ⏳ Blocked by 0→1 Gate | Requires live paid-tier Gemini API validation. Shaper uses `gemini-2.5-flash-lite` (scheduled shutdown Oct 16, 2026). |
| **Phase 3 — Trust-Check RAG** | 📦 Authored (Mock-tested only) | ⏳ Blocked by 0→1 Gate | Untested against active Supabase pgvector embeddings under live RLS policies. |
| **Phase 4 — Safety Layer** | 📦 Authored (Mock-tested only) | 🔴 **BLOCKED BY 3→4 GATE** | **Requires an explicitly named NGO/MFI partner and an escalation SLA agreed in writing before live deployment.** |
| **Phase 5 — Multimodal (Image OCR)** | 📦 Authored (Mock-tested only) | ⏳ Blocked by 0→1 Gate | Untested against live Meta Graph media endpoints. (Voice / STT / Bhashini deferred to v1.x). |
| **Phase 6 — Pilot Readiness** | 📦 Authored (Mock-tested only) | 🔴 **BLOCKED BY 5→6 GATE** | **Requires a named DPDP Act compliance owner and a scheduled legal review before real-user pilot.** |

---

## Security Notes

- **Never commit `.env`** — `.gitignore` already lists it. After every `git status`, confirm `.env` is not tracked.
- **Secrets** — all in environment variables, never in code or logs.
- **RLS** — enabled on every Supabase table from the first migration. Verify: `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';`
- **Webhook verification** — runs on raw bytes BEFORE any payload parsing (FR-11).
- **Audit log** — every access to escalation queue or raw conversation data writes a row.
- **Media retention** — image files deleted after `MEDIA_RETENTION_HOURS` (default: 24).

Full security requirements: `03_Security_Compliance.md` and the pilot launch checklist in Section 10.

---

## Pilot Launch Checklist (from 03_Security_Compliance.md Section 10)

Before opening testing beyond the core team, every item must be ✅:

- [ ] Webhook signature verification live and tested
- [ ] All secrets in environment variables — none in the repo (check git history too)
- [ ] RLS policies enabled on every Supabase table
- [ ] Internal tooling requires authenticated login, no shared credentials
- [ ] Rate limiting live at the edge layer, tested with burst requests
- [ ] Per-user cost cap implemented and alerting
- [ ] Media retention window implemented (auto-deletion, not manual)
- [ ] Audit logging live on escalation queue and raw-data access
- [ ] Incident response plan written, every team member knows first point of contact
- [ ] NGO/MFI partner escalation SLA agreed in writing
- [ ] DPDP-aligned consent notice shown at first contact
- [ ] Basic prompt-injection test run against trust-check flow
- [ ] Dependency vulnerability scan run and high-severity issues resolved
- [ ] `GEMINI_TIER=paid` confirmed in production environment

---

*Companion documents: `01_PRD_Financial_Mitra.md`, `02_System_Architecture.md`, `03_Security_Compliance.md`, `04_Tech_Stack.md`.*
