# 🏗️ System Architecture & Technology Stack — Financial Mitra
**Classification:** Technical Architecture & Engineering Specifications  
**Hosting Topology:** Render (FastAPI Cloud Backend) & Vercel (React Edge Frontend)  
**Database Layer:** Supabase PostgreSQL with `pgvector` & Row-Level Security

---

## 1. Architectural Overview & Decoupled AI Pipeline

Financial Mitra is engineered around a **Decoupled Multi-Stage Reasoning Pipeline**. Rather than forwarding unverified user inputs directly into a single unpredictable Large Language Model prompt, our platform completely separates **analytical trust reasoning** from **empathetic linguistic translation and presentation shaping**.

```
                           ┌───────────────────────────────────────────────┐
                           │   Meta WhatsApp Cloud API / Vercel Web Demo   │
                           └───────────────────────┬───────────────────────┘
                                                   │ HTTPS Payload Over TLS 1.3
                                                   ▼
                           ┌───────────────────────────────────────────────┐
                           │       FastAPI Gateway (Uvicorn Async Pool)    │
                           │   • Cryptographic Signature Verification      │
                           │   • Sliding-Window Rate & Spam Protection     │
                           └───────────────────────┬───────────────────────┘
                                                   │
                ┌──────────────────────────────────┴──────────────────────────────────┐
                ▼                                                                     ▼
     [Text / Multimodal Query]                                              [Greeting / Reset Cmd]
                │                                                                     │
                ▼                                                                     ▼
   ┌─────────────────────────┐                                           ┌─────────────────────────┐
   │  1. Intent Router       │                                           │  Instant Response Bumper│
   │   (Scam vs Money Check) │                                           │   (Zero LLM Overhead)   │
   └────────────┬────────────┘                                           └─────────────────────────┘
                │
                ▼
   ┌─────────────────────────┐             Vector Embeddings             ┌─────────────────────────┐
   │  2. RAG Scam Database   │ ────────────────────────────────────────► │   Supabase PostgreSQL   │
   │   (pgvector Similarity) │ ◄──────────────────────────────────────── │  • Known Scam Topologies│
   └────────────┬────────────┘             Verified Authorities          └─────────────────────────┘
                │
                ▼
   ┌─────────────────────────┐
   │  3. Core Reasoning LLM  │ ────► [Risk & Coercion Gate] ──► [Human Escalation Queue]
   │   • Strict JSON Output  │
   │   • Trust & Verdicts    │ ────► [North Star Metric Logging: Scams Blocked / Savings]
   └────────────┬────────────┘
                │ Structured Core Output (JSON) + Dialect Detection Flag
                ▼
   ┌─────────────────────────┐
   │  4. Language Shaper LLM │ ────► [Injects Verified Reference URLs & Cultural Empathy]
   │   • Bilingual Translation│
   └────────────┬────────────┘
                │
                ▼
   [Final Verified Conversational Response to WhatsApp or Web Dashboard]
```

---

## 2. Exhaustive Tech Stack Architecture

| Layer | Recommended Choice | Purpose & Engineering Justification |
|---|---|---|
| **Backend Framework** | **Python + FastAPI** | Native asynchronous (`asyncio`) network architecture ideal for high-throughput webhook handling. Integrates seamlessly with Pydantic JSON validation contracts. |
| **Frontend Application** | **Vite + React (TypeScript)** | Responsive, edge-deployable interactive web UI supporting live translation toggles, floating chat interactions, and global clipboard (`Ctrl+V`) screenshot capturing. |
| **Backend Hosting** | **Render (Container Service)** | Reliable cloud app hosting with environment isolation, automatic HTTPS TLS termination, and health check support (`/health`). |
| **Frontend Hosting** | **Vercel Edge Network** | Zero-configuration global edge caching and SPA client-side routing via `vercel.json` rewrite rules. |
| **Database & RAG Storage**| **Supabase PostgreSQL** | Unified managed PostgreSQL instance enabled with `pgvector` for similarity scam pattern matching and `pgcrypto` for secure token/identifier hashing. |
| **AI Reasoning Layer** | **Google Gemini / Groq Cloud** | Modular engine separation allows fast inference swapping: lightweight models (Flash/Llama-3-8B) for linguistic shaping and heavy reasoning models (Pro/Llama-3-70B) for high-accuracy scam trust evaluation. |
| **Outbound Messaging** | **Meta WhatsApp Cloud API** | Direct enterprise integration eliminating third-party broker markups, supported by robust HMAC cryptographic webhook validation. |

### Technical Trade-off Notes
* **Cold Start Management:** Free or baseline cloud container instances can spin down during idle overnight windows. To ensure high responsiveness, automated keep-alive cron actions ping our health service every 10 minutes during active daylight periods.
* **LLM Training Privacy Guardrail:** To uphold user privacy under modern data protection standards, our backend enforces a strict startup security check: when operating in production mode (`ENVIRONMENT=production`), the application refuses to launch if commercial LLM usage billing tiers aren't enabled (`GEMINI_TIER=paid`), guaranteeing zero retention of sensitive customer text for model training.

---

## 3. Core AI Engine Responsibilities

### 3.1 Intent Router (`intent_router.py`)
Classifies incoming conversational interaction into actionable branches:
* `trust_check`: Queries evaluating suspicious promotions, investment returns, or forwarded flyers.
* `money_decision`: Queries requesting guidance on personal savings, compounding interest, or spending plans.
* `general_greeting`: Instant conversational handshakes resolved via deterministic bumpers without invoking LLM tokens.

### 3.2 Analytical Core Engine (`core_engine.py`)
Executes purely logical financial deduction grounded in retrieved RAG context from Supabase. It returns strictly verified JSON schemas (`CoreEngineOutput`) without attempting personality generation:
```json
{
  "verdict": "avoid",
  "core_message": "Unregulated foreign exchange investment groups promising guaranteed daily returns exhibit standard characteristics of Ponzi scams.",
  "next_action": "Do not transfer funds or share banking details. Report the channel to the National Cyber Crime portal.",
  "risk_signals": ["Guaranteed abnormal returns", "Telegram-only support", "Unverified corporate domain"],
  "escalation_recommended": false,
  "sources": [
    {"name": "National Cyber Crime Helpline (1930)", "url": "https://cybercrime.gov.in"}
  ]
}
```

### 3.3 Language & Trust Shaper (`shaper.py`)
Receives structured analytical verdicts and shapes them into accessible, culturally resonant conversations in the exact script required by the user (English, Hindi Devanagari, or Roman Hinglish). It appends canonical institutional hyperlinks and ensures empathy without altering foundational trust ratings.

### 3.4 Multimodal Vision Processor (`vision.py`)
Analyzes uploaded flyer screenshots and investment promotional posters, extracting embedded text via Optical Character Recognition (OCR) to evaluate return rates, QR codes, and suspicious visual layout signatures.

---

## 4. Supabase Database Schema & Data Models

Our relational database structure is designed around strict access encapsulation and token minimization:

```sql
-- Core User Identities (Hashed WhatsApp identifiers for privacy)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    whatsapp_id_hash VARCHAR(64) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Active User Sessions & Multi-Turn Context
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    channel VARCHAR(20) DEFAULT 'whatsapp',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Vector RAG Knowledge Base for Scam Signatures
CREATE TABLE scam_kb_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    content_text TEXT NOT NULL,
    risk_level VARCHAR(50) CHECK (risk_level IN ('safe_ish', 'be_careful', 'avoid')),
    embedding VECTOR(768)
);

-- North Star Metric & Action Analytics Logging
CREATE TABLE financial_actions_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL, -- e.g., 'scam_avoided', 'savings_started'
    verdict_emitted VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);
```

---

## 5. Non-Blocking Concurrency & Multi-User Independence

To support thousands of simultaneous conversational interactions without cross-user state leakage or bottlenecking:
1. **Asynchronous Connection Pooling:** All database queries and external LLM REST invocations utilize optimized `httpx.AsyncClient` pools and async SQLAlchemy/PostgreSQL drivers.
2. **Session Isolation:** WhatsApp traffic is uniquely keyed by HMAC-verified sender phone number hashes, while Vercel Web Demo users generate localized, ephemeral cryptographic tokens (`demo_<random_id>`) stored purely in browser memory. Neither pathway can inspect or mutate another user's conversational state.
