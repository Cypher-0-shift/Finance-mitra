# Financial Mitra — AI Financial Companion
**Team ZENVEST | BITSoM × Masai Capstone Project**

A WhatsApp-first and web-based AI companion that helps low-income, informal-income users in India make confident money decisions and avoid scams — in Hindi or English, no app download required.

> 📢 **Access & Availability Notice:**
> - 📱 **WhatsApp Integration (Testing Phase):** Currently in Meta sandbox testing mode. Access is restricted to pre-registered test numbers while Meta Business Verification is in progress.
> - 🌐 **Web App (Open to All Users):** Fully accessible to all users via any web browser! The web experience features interactive **Legal & Compliance** buttons (in the top navigation header and welcome screen) providing instant access to SEBI Non-RIA educational disclaimers, RBI safety guidelines, and zero-OTP data protection guarantees.

---

## What it does

Two things, and only two things in v1:

1. **"What should I do with this money?"** — user describes money they just received; system asks 1–2 clarifying questions and returns one concrete, prioritized action.
2. **"Is this offer/loan/scheme trustworthy?"** — user sends a text description or a screenshot; system evaluates it against a curated scam-pattern knowledge base and returns a plain verdict (Safe-ish / Be Careful / Avoid) with a reason and a source reference.

Every response ends in exactly one next action. The AI never moves money, never asks for OTPs, and escalates to a human NGO/MFI partner when real distress or high risk is detected.

---

## Access Channels

| Channel | Status | Who Can Access | Features |
|---|---|---|---|
| 🌐 **Web Platform** | 🟢 Live / Open | **All Users** | Interactive chat, screenshot upload (`Ctrl+V`), **Legal & Compliance buttons/modal**, bilingual Hindi/English UI |
| 📱 **WhatsApp API** | ⏳ In Testing | **Registered Testers Only** | Text & flyer evaluation via WhatsApp Cloud API (awaiting Meta Business Verification) |

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | FastAPI (Python, async) |
| Frontend | React + Vite + TypeScript |
| Database | Supabase (Postgres + pgvector + RLS) |
| AI — reasoning | Groq Cloud (`llama-3.3-70b-versatile`) / Gemini 2.5 Pro |
| AI — classification & shaping | Groq Cloud (`llama-3.1-8b-instant`) / Gemini 2.5 Flash-Lite |
| AI — vision | Gemini 2.5 Flash multimodal (image/screenshot input) |
| RAG | pgvector cosine similarity on scam-pattern knowledge base |
| Messaging | Meta WhatsApp Cloud API |
| Backend hosting | Render |
| Frontend hosting | Vercel |

---

## Repository structure

The codebase is organized into four main categories: **Backend**, **Frontend**, **Docs**, and **Other Files & Configuration**.

```
financial-mitra/
│
├── ⚙️ backend/                 # Backend service (FastAPI, Pytest, scripts)
│   ├── app/                    # FastAPI application code
│   │   ├── main.py             # App factory & lifespan
│   │   ├── config.py           # Settings & validation
│   │   ├── dependencies.py     # FastAPI dependency injection
│   │   ├── db/                 # Supabase PostgreSQL client & migrations
│   │   ├── engines/            # AI reasoning (Groq), intent router, shaper, risk gate
│   │   ├── routers/            # Webhook, web dev chat, internal admin APIs
│   │   ├── security/           # Webhook signature & RBAC auth
│   │   └── services/           # Session, RAG, rate limiter, escalation, analytics, audit
│   ├── tests/                  # 72 unit tests with mocked external APIs
│   └── scripts/                # Database population scripts
│
├── 💻 frontend/                # Frontend web application (React + Vite + TypeScript)
│   ├── src/
│   │   ├── App.tsx             # Root component
│   │   ├── types.ts            # Data models
│   │   └── components/         # WelcomeScreen, TopAppBar, MessageBubble, ComplianceModal, etc.
│   ├── vercel.json             # Vercel deployment config
│   └── package.json            # Node dependencies
│
├── 📖 docs/                    # System & regulatory documentation
│   ├── PRD.md                  # Product Requirements Document
│   ├── ARCHITECTURE.md         # System Architecture & AI Pipeline specs
│   └── COMPLIANCE_AND_SECURITY.md # Regulatory compliance & security controls
│
└── 🛠️ ROOT CONFIGURATION FILES
    ├── README.md               # Project overview & guide
    ├── render.yaml             # Render infrastructure deployment blueprint
    ├── requirements.txt        # Pinned backend dependencies
    ├── pyproject.toml          # Python project configuration
    ├── .env.example            # Environment variables reference template
    └── .env                    # Local environment variables
```

---

## Local development

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- A Supabase project with `pgvector` and `pgcrypto` extensions enabled
- A Groq Cloud API Key (`GROQ_API_KEY`) or Google AI Studio key (`GEMINI_API_KEY`)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, GROQ_API_KEY / GEMINI_API_KEY
# Set: ENVIRONMENT=development

uvicorn app.main:app --reload --port 8000
```

Health check: `http://localhost:8000/health`

Test the pipeline without WhatsApp: `POST http://localhost:8000/dev/chat`
```json
{
  "session_id": "dev-test-001",
  "message": "Someone promised me 50% returns in 3 months",
  "input_type": "text",
  "language": "en"
}
```

> `/dev/chat` is only active when `ENVIRONMENT=development`. It does not exist in production.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Set: VITE_API_URL=http://localhost:8000
npm run dev
```

Frontend runs at `http://localhost:5173`

> 💡 **Web Version Features:** The web app allows all users to chat immediately without an app install or WhatsApp access. Users can click the **Compliance & Safety** button in the top navigation header or welcome screen at any time to inspect our SEBI Non-RIA disclaimer, data privacy policy, and RBI/Cyber Crime (1930) reporting guidelines.

### Database migrations

In your Supabase SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```
Then run the full contents of `app/db/migrations/001_initial.sql`.

Verify RLS is active on all 8 tables:
```sql
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';
```
All rows must show `rowsecurity = true` before proceeding.

### Tests

```bash
pytest tests/ -v
```
Expected: `72 passed`. No live API keys needed — all external calls are mocked.

---

## Environment variables

Copy `.env.example` and fill in all values. Key variables:

| Variable | What it is |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (never expose client-side) |
| `GROQ_API_KEY` | Groq Cloud API key (for fast Llama 3 reasoning & classification) |
| `GROQ_MODEL_CHEAP` | `llama-3.1-8b-instant` (intent classification & shaping) |
| `GROQ_MODEL_STRONG` | `llama-3.3-70b-versatile` (core trust-check reasoning) |
| `GEMINI_API_KEY` | Google AI / Gemini API key (optional / vision multimodal) |
| `WHATSAPP_APP_SECRET` | Meta app secret for webhook signature verification |
| `WHATSAPP_ACCESS_TOKEN` | Permanent system-user token from Meta Business Settings |
| `WHATSAPP_PHONE_NUMBER_ID` | Your WhatsApp Business phone number ID |
| `WHATSAPP_VERIFY_TOKEN` | Any string you choose — must match what you set in Meta's webhook config |
| `WHATSAPP_ID_HASH_SALT` | Secret salt for hashing WhatsApp IDs before storing |
| `INTERNAL_SERVICE_TOKEN` | Bearer token for internal escalation API |
| `ENVIRONMENT` | `development` or `production` |
| `SENTRY_DSN` | Sentry error tracking DSN (optional in development) |

---

## WhatsApp integration (testing phase)

> ⚠️ **Note:** The WhatsApp integration is currently under **testing/sandbox phase** and is restricted to pre-approved test phone numbers. General users can use the **Web Version** in the meantime, which is open to everyone.

The system works with Meta's free test tier while Business Verification is in progress. You can message up to 5 manually added phone numbers without verification approved.

1. In Meta App Dashboard → **WhatsApp → API Setup**, copy your Phone Number ID and generate a system-user access token (see `docs/ARCHITECTURE.md` for the exact steps).
2. Use [ngrok](https://ngrok.com) to expose your local server: `ngrok http 8000`
3. In Meta → **WhatsApp → Configuration → Webhook**, set Callback URL to `https://<your-ngrok-id>.ngrok-free.app/webhook/whatsapp` and set Verify Token to match `WHATSAPP_VERIFY_TOKEN` in your `.env`.
4. Subscribe to the `messages` webhook field.
5. Add your personal number as a test recipient in the Meta dashboard.
6. Send a message from your phone to the test WhatsApp Business number.

---

## Production deployment

### Backend (Render)

1. Connect your GitHub repo to Render → **New Web Service** → select Blueprint (uses `render.yaml`).
2. Under **Environment Variables**, add all production values from `.env.example`.
3. Set `ENVIRONMENT=production`.
4. Deploy. Health check at `https://your-app.onrender.com/health`.

> Render's free tier spins down after 15 minutes of inactivity. The GitHub Actions keep-alive workflow (`.github/workflows/keep-alive.yml`) pings `/health` every 10 minutes to prevent this and keep Supabase's free-tier project from pausing.

### Frontend (Vercel)

1. Import your repo into Vercel → set Root Directory to `frontend`.
2. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`
3. Deploy. Vercel detects Vite automatically.

---

## Security & Compliance baseline

Before opening testing to anyone outside the core team, verify every item in `docs/COMPLIANCE_AND_SECURITY.md` Section 10 (pilot-launch checklist). Key controls already implemented:

- **Web Legal & Compliance Buttons:** Interactive compliance overlay accessible on the web UI (`ComplianceModal.tsx`), informing users of our Non-RIA educational advisory scope and safety guidelines.
- HMAC-SHA256 webhook signature verification on every inbound request before any processing
- WhatsApp IDs stored as salted hashes only — raw phone numbers never persisted
- RLS enabled on all 8 Supabase tables (deny-by-default)
- Two-layer risk/distress gate: keyword pattern matching OR LLM flag triggers escalation — neither layer requires the other
- Per-user rate limiting + daily LLM cost cap
- Audit logging on all access to escalation records and raw conversation data
- Media (images) auto-deleted after 24 hours

---

## Operational blockers (not code — real-world gates)

| Gate | Status | What's needed |
|---|---|---|
| Meta Business Verification | ⏳ Submitted, 2–7 day wait | Approval needed to message beyond 5 test numbers |
| NGO/MFI escalation partner | 🔴 Not named | Escalation system exists but routes to no one. Need a partner + written SLA before pilot. |
| DPDP Act compliance review | 🔴 No owner assigned | Need a named person to conduct legal data-retention review before real users. |

---

## Documentation

| Doc | What's in it |
|---|---|
| `docs/PRD.md` | Product scope, functional requirements, personas, acceptance criteria |
| `docs/ARCHITECTURE.md` | Component design, data model, API contracts, pipeline diagrams |
| `docs/COMPLIANCE_AND_SECURITY.md` | Threat model, DPDP Act alignment, security controls, pilot-launch checklist |

---

## Team

**Team ZENVEST** — BITSoM × Masai School Capstone Project, Phase 2

*Financial Mitra is an educational capstone project. It is not a registered financial advisor and does not provide regulated financial advice. See `docs/COMPLIANCE_AND_SECURITY.md` for full scope and disclaimers.*
