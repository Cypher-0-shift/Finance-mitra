# Financial Mitra 🪙 — AI Financial Companion & Anti-Fraud Guide

> **An empathetic, WhatsApp-first and web-based financial literacy, savings guidance, and scam deterrence assistant for emerging digital financial users across urban and rural India.**  
> Built by **Team ZENVEST** | Status: **Enterprise MVP Ready — Deployed on Render (Backend) & Vercel (Frontend)**

---

## 🌟 Executive Summary & Mission

As smartphone access and instant UPI digital transactions expand across India, millions of everyday users become prime targets for unregulated Ponzi schemes, deceptive Telegram "guaranteed high-return" investment groups, and financial cyber-fraud. Traditional banking portals and legal disclaimers often rely on rigid English financial terminology that alienates users lacking formal fiscal training.

**Financial Mitra** ("Financial Friend") bridges this trust gap by conversing as a warm, knowledgeable, and judgment-free financial mentor. Available through WhatsApp Cloud API and an interactive Web Demo, it evaluates investment offers, simplifies complex savings products, uncovers deceptive scam signatures using artificial intelligence, and directs families toward secured government savings plans (such as Public Provident Fund, Post Office Term Deposits, and Sukanya Samriddhi Yojana).

---

## 📚 Core System Documentation

Before deploying or expanding the codebase, explore our consolidated engineering and compliance design suite inside the `docs/` folder:
* **[📋 Product Requirement Document (PRD)](./docs/PRD.md):** Target demography, conversation design tenets, multi-language fluency, and user personas.
* **[🏗️ System Architecture & Engineering Stack](./docs/ARCHITECTURE.md):** Decoupled AI reasoning pipelines (Intent Router, Core Engine, Shaper), complete technology selection tables, Supabase vector RAG schema, and non-blocking concurrency.
* **[⚖️ Regulatory Compliance & Cyber Security](./docs/COMPLIANCE_AND_SECURITY.md):** SEBI Non-RIA legal exemption, Zero-Trust OTP banking credential protection, CERT-In fraud reporting alignment, threat model analysis, and AI emotional safety guardrails.

---

## ✨ Key Features & Capabilities

### 1. 🗣️ Adaptive Bilingual & Dialect Fluency
* **Per-Message Language Routing:** Automatically detects user script and dialect without rigid setup menus.
* **Three-Way Support:** Smoothly shifts between structured English, pure Devanagari Hindi (`हिन्दी`), and casual conversational Roman script Hindi (*Hinglish* - *"Bhai yeh scheme safe hai kya?"*).

### 2. 🛡️ Two-Stage AI Scam Detection & OCR Visual Verification
* **Text & Flyer Evaluation:** Users can query investment promotional texts or upload screenshot posters of fraudulent loan flyers.
* **Global Clipboard Support:** In the web dashboard, users can instantly upload screen captures simply by pressing **`Ctrl + V`** (or `Cmd + V` on macOS) anywhere on screen.
* **Clear Trust Verdicts:** Emits explicit color-coded assessments: **Safe-ish (Deep Teal)**, **Be Careful (Saffron Caution)**, or **Avoid (Alert Red)**, complete with actionable advice chips.

### 3. ⚖️ Interactive Legal Compliance & Canonical References
* **Zero-Hallucination Citations:** Automatically links cited regulatory bodies directly to verified government canonical root homepages:
  * Reserve Bank of India: [`https://www.rbi.org.in`](https://www.rbi.org.in)
  * SEBI Official Investor Portal: [`https://www.sebi.gov.in`](https://www.sebi.gov.in)
  * National Cyber Crime Helpline (1930): [`https://cybercrime.gov.in`](https://cybercrime.gov.in)
* **On-Demand Compliance Dashboard:** Built-in modal accessible from both the welcome page and chat header detailing our non-RIA educational scope and OTP banking safety guarantees.

### 4. 🚀 Enterprise Concurrency & Abuse Protection
* **Asynchronous Connection Pooling:** Powered by non-blocking FastAPI and Uvicorn with optimized HTTP connection pools.
* **Per-User Rate Limiting:** Database-backed sliding window usage counters protect external LLM APIs from spam DDoS overload and enforce daily budget ceilings without interrupting concurrent legitimate users.

---

## 📁 Repository & Architecture Structure

```
financial-mitra/
├── app/                                 # FastAPI Backend Architecture
│   ├── main.py                          # Lifespan initialization, CORS, connection pools & /health
│   ├── config.py                        # Pydantic environment validation & startup security guards
│   ├── routers/
│   │   ├── webhook.py                   # Meta WhatsApp Cloud API endpoint (/webhook/whatsapp)
│   │   ├── dev.py                       # Live web demo API endpoint (/dev/chat)
│   │   └── internal.py                  # Protected escalation administration APIs
│   ├── services/
│   │   ├── whatsapp.py                  # Meta Graph API outbound client
│   │   ├── session.py                   # Supabase user & conversation state persistence
│   │   ├── rate_limit.py                # Sliding window spam throttling & token cost caps
│   │   └── analytics.py                 # North Star metrics telemetry (scams blocked, savings initiated)
│   ├── engines/
│   │   ├── core_engine.py               # Analytical AI Reasoning Engine (Groq Llama-3 / Gemini)
│   │   ├── shaper.py                    # Bilingual translation & cultural persona shaping
│   │   ├── intent_router.py             # Classification engine (Scam Check vs Money Decision)
│   │   ├── risk_gate.py                 # Deterministic regex + AI guardrails (Self-harm, coercion)
│   │   └── vision.py                    # Multimodal OCR flyer evaluation pipeline
│   ├── security/
│   │   ├── signature.py                 # Constant-time HMAC-SHA256 Meta payload verification
│   │   └── auth.py                      # Bearer cryptographic service token authentication
│   └── db/
│       └── client.py                    # Asynchronous Supabase PostgreSQL connection layer
├── frontend/                            # Vite + React + TypeScript Web Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── WelcomeScreen.tsx        # Hero onboard screen with branding & legal disclaimers
│   │   │   ├── TopAppBar.tsx            # Sticky navigation header with live translation toggles
│   │   │   ├── MessageBubble.tsx        # Two-tone message bubbles with clickable URL parser & banners
│   │   │   ├── ChatInput.tsx            # Floating input bar with Ctrl+V clipboard guidance & photo uploads
│   │   │   ├── PhotoPreviewModal.tsx    # Interactive image screenshot evaluation viewer
│   │   │   ├── ComplianceModal.tsx      # Bilingual SEBI/RBI legal compliance disclaimer overlay
│   │   │   └── MitraLogo.tsx            # Vector SVG rupee shield branding emblem
│   │   ├── types.ts                     # TypeScript data contracts and payload schemas
│   │   └── App.tsx                      # Primary orchestration engine with anonymous session tracking
│   ├── vercel.json                      # Vercel deployment configuration & SPA routing rules
│   └── .env.example                     # Sample frontend production environment variables
├── tests/                               # Comprehensive Automated Test Suite (72/72 Passing)
│   ├── test_signature.py                # Cryptographic timing-safe webhook tests
│   ├── test_core_schema.py              # AI engine structured JSON schema tests
│   ├── test_risk_gate.py                # Multilingual keyword safety & injection guardrail tests
│   ├── test_dev_chat.py                 # Web demo integration test pipeline
├── docs/                                # Enterprise Documentation Suite (Consolidated)
│   ├── ARCHITECTURE.md                  # System architecture, decoupled pipelines & tech stack tables
│   ├── COMPLIANCE_AND_SECURITY.md       # Regulatory SEBI/RBI compliance, threat models & privacy specs
│   └── PRD.md                           # Product requirement document, user flows & persona tenets
├── render.yaml                          # Render cloud infrastructure deployment blueprint
└── requirements.txt                     # Pinned backend Python dependencies
```

---

## 🛠️ Local Development Setup

### Prerequisites
* **Python:** v3.10+
* **Node.js:** v18+ & NPM
* **Database:** Supabase PostgreSQL instance (with `pgcrypto` enabled)
* **AI API Keys:** Groq Cloud or Google AI Studio (Gemini)

### 1. Backend Configuration (FastAPI)

```bash
# 1. Create and activate a Python virtual environment
python -m venv .venv
# On Windows PowerShell: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# 2. Install backend package requirements
pip install -r requirements.txt

# 3. Configure local environment
cp .env.example .env
# Open .env and insert your SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and GEMINI/GROQ keys

# 4. Launch local backend API server
uvicorn app.main:app --reload --port 8000
```
*The Backend server will be live at `http://localhost:8000`. Test endpoint health at `http://localhost:8000/health`.*

### 2. Frontend Configuration (React / Vite)

```bash
# 1. Navigate into the frontend application directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Configure local frontend environment
cp .env.example .env.local
# Inside .env.local, set: VITE_API_URL=http://localhost:8000

# 4. Launch local React development server
npm run dev
```
*Your frontend dashboard will immediately open in your browser at `http://localhost:5173`.*

---

## 🧪 Automated Verification & Testing

Financial Mitra maintains a strictly enforced automated regression and security test suite using `pytest` and `asyncio`. The test suite verifies timing-safe cryptographic signatures, dynamic timestamp windowing in rate limiters, Pydantic JSON contracts, and bilingual Devanagari keyword guardrails.

To execute the entire 72-case verification suite locally:

```bash
# Ensure your virtual environment is active in the project root
pytest tests/ -v
```

*Expected Output:*
```
============================= 72 passed in 0.95s ==============================
```

---

## 🌐 Production Deployment Guide

### 1. Backend Hosting (Render)
1. Link your GitHub repository to your Render dashboard.
2. Select **New Web Service** using the included `render.yaml` configuration blueprint, or manually configure:
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port 10000`
3. Under **Environment Variables**, provide your live production variables (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `WHATSAPP_VERIFY_TOKEN`, etc.).
4. Deploy the service. Your live API base endpoint will be: `https://financial-mitra.onrender.com`.

### 2. Frontend Hosting (Vercel)
1. Import your GitHub repository into your Vercel Dashboard and select the `frontend` folder as the Root Directory.
2. Vercel will automatically detect the **Vite** preset:
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
3. In the Vercel project deployment settings, add the Environment Variable:
   * **`VITE_API_URL`** = `https://financial-mitra.onrender.com`
4. Click **Deploy**. Vercel will process SPA routing via `vercel.json` and deploy your responsive application globally with zero-configuration edge caching.

---

## 📜 License & Acknowledgments
Designed and built with passion by **Team ZENVEST** to promote inclusive financial literacy and digital safety across emerging economies. Refer to [COMPLIANCE_AND_SECURITY.md](./docs/COMPLIANCE_AND_SECURITY.md) inside `docs/` for full usage disclaimers, threat defenses, and regulatory guidelines.
