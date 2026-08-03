# 🏗️ System Architecture & Technical Design — Financial Mitra

This document outlines the technical software design, algorithmic reasoning pipelines, micro-service layers, database schema, and deployment architecture powering **Financial Mitra**.

---

## 1. Architectural Overview & Design Philosophy

Financial Mitra is architected around a **Decoupled Multi-Stage Reasoning Pipeline**. Instead of forwarding uncooked user queries to an unpredictable monomorphic LLM prompt, the framework isolates **analytical logical deduction** from **conversational empathetic shaping**. 

```
                                  ┌──────────────────────────────┐
                                  │      Meta WhatsApp Cloud     │
                                  │        (Webhook / API)       │
                                  └──────────────┬───────────────┘
                                                 │ HTTPS POST (Webhook Payload)
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │   FastAPI Gateway (Uvicorn)  │
                                  │   • Signature Verification   │
                                  │   • Lifecycle & Short-Circuit│
                                  └──────────────┬───────────────┘
                                                 │
                   ┌─────────────────────────────┴─────────────────────────────┐
                   ▼                                                           ▼
         [Text / Multimodal Query]                                 [Greeting / Reset Cmd]
                   │                                                           │
                   ▼                                                           ▼
       ┌───────────────────────┐                                 ┌───────────────────────────┐
       │ 1. Intent Router      │                                 │ Instant Response Bumper   │
       │    (Classify intent)  │                                 │ (0 LLM overhead latency)  │
       └───────────┬───────────┘                                 └───────────────────────────┘
                   │
                   ▼
       ┌───────────────────────┐         Query Vectors / Records ┌───────────────────────────┐
       │ 2. RAG Context Lookup │ ─────────────────────────────► │   Supabase PostgreSQL     │
       │    (Scam Pattern DB)  │ ◄───────────────────────────── │   • Scam patterns & KBs   │
       └───────────┬───────────┘         Trusted Authorities     └───────────────────────────┘
                   │
                   ▼
       ┌───────────────────────┐
       │ 3. Core Engine (70B)  │  ──► [Risk / Distress Gate] ──► [Human Escalation Record]
       │    • Strict JSON Dump │
       │    • Trust & Verdicts │  ──► [North Star Metric Logging: Scams Avoided / Savings]
       └───────────┬───────────┘
                   │ Structured Core Engine Output (JSON) + Detected Language Mode
                   ▼
       ┌───────────────────────┐
       │ 4. Shaper Engine (8B) │  ──► [Injects Reference URLs & Plain-Text Arithmetic Math]
       │    • Empathy persona  │
       │    • Tone & length    │
       └───────────┬───────────┘
                   │ Formatted WhatsApp Response Message
                   ▼
       ┌───────────────────────┐
       │ 5. WhatsApp Client    │  ──► Sends secure payload via Meta Graph API v22.0
       └───────────────────────┘
```

---

## 2. Core Modules & Directory Structure

```
Financial mitra/
├── app/
│   ├── main.py                   # Application lifespan, global resource initialization, FastAPI initialization
│   ├── config.py                 # Pydantic Settings implementation loading parameters from .env
│   ├── routers/
│   │   ├── webhook.py            # Primary Meta Cloud WhatsApp Webhook endpoint (& validation GET routes)
│   │   └── dev.py                # Isolated `/dev/chat` playground API for terminal-based testing without real phone routing
│   ├── engines/
│   │   ├── core_engine.py        # Heavy reasoning analyzer producing structured analytical JSON evaluation
│   │   ├── shaper.py             # Empathetic conversational shaper transforming JSON to culturally attuned text
│   │   ├── intent_router.py      # High-speed semantic classifier determining downstream routing demands
│   │   └── vision.py             # Optical Character Recognition (OCR) + Multimodal image evaluation for fraud screenshots
│   ├── services/
│   │   ├── whatsapp.py           # Async Meta Cloud API Graph Wrapper (Message Dispatcher & Media Downloader)
│   │   ├── rag.py                # Retrieval-Augmented Generation client interfacing with Supabase vector databases
│   │   ├── session.py            # Lifecycle management (User registration, Chat threads, DB persistence)
│   │   ├── escalation.py         # Automated risk flagger monitoring distress parameters
│   │   └── analytics.py          # Real-time event logger recording targeted North Star behavioral milestones
│   ├── schemas/
│   │   └── core_engine.py        # Validated Pydantic models governing intermediate data structures
│   └── db/
│       └── client.py             # Managed Supabase REST & Vector database service bindings
├── scratch/                      # System diagnostics and automated configuration scripts (e.g. fix_waba_subscription.py)
├── .env                          # Local environment deployment credentials
├── PRD.md                        # Complete Product Requirements & Specification document
└── ARCHITECTURE.md               # Detailed Technical Systems document (This file)
```

---

## 3. Detailed Component Pipeline

### 3.1 Webhook Router & Pre-Processing (`app/routers/webhook.py`)
1. **Webhook Security:** Verifies incoming `hub.verify_token` against internal secrets during initialization.
2. **Media Processing:** If an attachment payload is received (`input_type == "image"`), invoking `wa_client.download_media` fetches binary contents from Meta's encrypted CDN and delegates processing to `vision.py` to deduce visual indicators and OCR text.
3. **Command Short-Circuits:**
   * **Greetings:** Immediately captures conversational greetings (`"hii"`, `"hello"`, `"namaste"`) to deliver instant introductions without spinning up inferencing engines.
   * **Resets:** Intercepts restart requests (`"reset"`, `"phir se"`, `"clear"`), safely closes active database conversation logs (`status = 'closed'`), and establishes fresh conversational scopes.
4. **Three-Way Dialect Engine:** Evaluates incoming string characters:
   * Analyzes ASCII character distribution ratios (`_ascii_ratio > 0.85`).
   * Evaluates native terminology sets (`_hinglish_words`) to distinguish accurately between pure **English**, **Hinglish**, and **Devanagari Hindi** on every single turn.

### 3.2 AI Engine Ecosystem (`app/engines/*`)
The pipeline heavily relies on **Groq Cloud API** inference architecture to guarantee sub-3-second real-time responsiveness over cellular networks:

* **Intent Router Engine:** Quickly tags user messages into discrete operational lanes (e.g., `trust_check`, `savings`, `education`, `general`).
* **Core Reasoning Engine (`core_engine.py`):** Powered by heavy inferencing models (e.g., `llama-3.3-70b-versatile`). It strictly abstracts emotion away and generates structured validation objects:
  ```json
  {
    "verdict": "avoid",
    "risk_signals_detected": ["unrealistic returns", "urgency tactics", "unregulated channel"],
    "core_message": "Scheme is statistically unsustainable and displays classic Ponzi attributes.",
    "next_action": "Do not send funds; immediately report and exit group.",
    "sources": [{"name": "RBI", "pattern": "Unregulated high return Telegram fraud"}],
    "escalation_recommended": false
  }
  ```
* **Language & Trust Shaper (`shaper.py`):** Powered by high-speed execution models (`llama-3.1-8b-instant`). It receives the raw Core JSON alongside the detected language profile and injects conversational warmth, cultural idioms, step-by-step arithmetic explanations, and verified Indian institutional links (RBI, SEBI, NPCI, India Post).

---

## 4. Database Persistence Layer (Supabase / PostgreSQL)

All interactions are logged continuously inside a cloud-hosted Supabase PostgreSQL instance via asynchronous HTTP REST queries:

### 4.1 Core Relational Entities
1. `users`:
   * Stores anonymized cryptographic hashes of WhatsApp IDs (`whatsapp_id_hash`) to guarantee user privacy while preserving continuous personalization histories and language profiles.
2. `conversations`:
   * Tracks active chat lifespans (`status`: `open` or `closed`), intent trajectories, and timestamp records.
3. `messages`:
   * Complete audit logging containing input modalities (`text`, `image`), sender origins (`user` vs `system`), and associated metadata payloads.

### 4.2 Analytical & Safe Guard Rails
4. `escalations`:
   * Triggered automatically whenever the Risk Gate flags emotional distress or serious financial losses. Holds diagnostic signals for specialized support network review.
5. `financial_actions_log`:
   * Dedicated North Star telemetry tracking verified real-world outcomes: `scam_avoided` (fraud averted) and `savings_started` (organized investment adopted).
6. `rate_limit_counters`:
   * Protects webhook endpoints against malicious automated flood requests or brute-force DoS loops.

---

## 5. External Integration Mechanics

### 5.1 Meta WhatsApp Cloud API v22.0
* **Outbound Delivery:** Handled by `app/services/whatsapp.py` using `httpx.AsyncClient` targeting `https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages`. 
* **Authentication Security:** Requires permanent System User access authorization (`WHATSAPP_ACCESS_TOKEN`) with delegated administrative roles (`whatsapp_business_messaging`, `whatsapp_business_management`) generated inside Meta Business Suite.
* **Webhook Routing:** Connected locally via secure tunneling (`ngrok http 8000`) or cloud production targets (Render/Railway container deployments) via the endpoint URI `/webhook/whatsapp`.

---

## 6. Verification & Developer Tooling

### 6.1 Interactive Terminal Sandbox (`/dev/chat`)
To enable deep development, algorithmic iteration, and RAG tuning without invoking WhatsApp network tariffs or device usage, the platform exposes a dedicated REST testing harness under `app/routers/dev.py`. Developers can send POST invocations containing mock payloads and inspect full diagnostic execution trees (including intermediate Core JSON outputs, Shaper transformations, and intent routing decisions).
