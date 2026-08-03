# Tech Stack Document — Financial Mitra
### Team ZENVEST | v1

*Companion to `01_PRD_Financial_Mitra.md`, `02_System_Architecture.md`, `03_Security_Compliance.md`. This document is the concrete "what do I actually install/sign up for" reference — each choice includes what it's for, why it over alternatives, and its cost tier.*

---

## 1. Core Backend

| Component | Choice | Alternatives considered | Why this one |
|---|---|---|---|
| Language/framework | Python + FastAPI | Node/Express, Django | Async support fits webhook-heavy I/O well; matches your existing SANARCH/Club Manager stack, so patterns (Pydantic models, async handlers, project structure) transfer directly and save real build time |
| Data validation | Pydantic | Marshmallow, manual validation | Native to FastAPI; used throughout for the structured-output schema enforcement that's core to FR-7 |
| Background task handling | FastAPI `BackgroundTasks` for pilot scale; revisit a proper queue (e.g. Celery + Redis) if volume grows | Inline synchronous processing | Webhook responses need to return fast (Section 6.1 of architecture doc); a queue is over-engineering for pilot scale but the right next step post-pilot |

---

## 2. Hosting & Infrastructure

*Updated: Railway replaced with Render. See trade-off note below.*

| Component | Choice | Why |
|---|---|---|
| App hosting | **Render** | Railway's genuine free tier was discontinued in 2023 (now a one-time trial credit). Render provides a true free web-service tier suitable for pilot scale. |
| Database | Supabase (managed Postgres) | Postgres + pgvector + built-in Row-Level Security + Auth in one platform; avoids running a separate vector DB |
| Static/edge concerns | Render's proxy layer + FastAPI middleware | Sufficient at pilot scale for TLS termination, basic rate limiting; a dedicated WAF/CDN product is worth revisiting post-pilot, not before |

**⚠️ Known trade-off — Render free tier cold start:** Render's free tier spins down after 15 minutes of inactivity. The first request after any idle period incurs a 30–60 second cold start. This conflicts with the PRD's sub-5-second latency target for that first message. Mitigation: the keep-alive GitHub Actions workflow (`.github/workflows/keep-alive.yml`) pings `/health` every 10 minutes during active hours. This does not eliminate the issue for overnight idle periods — switch to a paid Render instance type (`starter` or above) before the pilot opens to real users if consistent latency is required.

---

## 3. Messaging & Communication

| Component | Choice | Alternatives considered | Why |
|---|---|---|---|
| Messaging channel | Meta WhatsApp Cloud API (direct) | BSP (Gupshup, Twilio) | Direct integration avoids per-message BSP markup; free developer tier sufficient for pilot. Trade-off: you own webhook reliability and Business verification lead time yourself — budget for that in Phase 0 |

---

## 4. AI / LLM Layer

*Updated: Google Gemini resolved as the LLM stack for all call types. Provider is a starting choice, not a permanent lock-in — all engine modules are isolated and swappable. See trade-off note below.*

| Call type | Resolved model | Reasoning |
|---|---|---|
| Intent routing | **Gemini 2.5 Flash** | Cheapest available, low-complexity task |
| Core Engine — `money_decision` / `general` | **Gemini 2.5 Flash** | Cost ceiling (₹10–20/user/month) is the binding constraint |
| Core Engine — `trust_check` | **Gemini 2.5 Pro** | A wrong verdict is the single worst failure mode — worth the stronger model on this path ONLY |
| Language & Trust Shaper | **Gemini 2.5 Flash-Lite** (`gemini-2.5-flash-lite`) | Mechanically simpler task (translate + tone); cheapest/fastest model to offset the two-call cost increase. *(Note: scheduled shutdown Oct 16, 2026 — must migrate to latest alias or successor before sunset).* |
| Image understanding (Phase 5) | **Gemini 2.5 Flash** (multimodal) | Native multimodal support; replaces self-hosted OCR entirely |
| Embeddings (RAG) | **`models/text-embedding-004`** (Gemini) | Must match the model used to populate `scam_kb_cards` — mismatch silently breaks retrieval quality |

**⚠️ Known trade-off — Gemini free-tier training-data policy:** Gemini's free API tier allows Google to use submitted prompts and responses to improve their models. The paid tier (billing enabled on the Google Cloud project) excludes this by default. This is a direct conflict with the DPDP Act 2023 purpose-limitation commitment if real users' financial conversations flow through the free tier. The application enforces this as a hard startup guard: if `ENVIRONMENT=production` and `GEMINI_TIER=free`, the app refuses to start. Enable GCP billing and set `GEMINI_TIER=paid` before any real-user traffic.

**Future bake-off note:** before committing to Gemini long-term, run a bake-off on: Hindi/code-mixed accuracy, structured-output reliability at scale, image understanding on real Indian document photos, and actual per-call cost. The engine module isolation (`app/engines/`) makes this a low-effort swap.

---

## 5. Why Not a Self-Hosted Vision/OCR Model

This is worth documenting explicitly since it was actively considered (`baidu/Unlimited-OCR` and similar).

- Models in this class are large vision-language models requiring GPU inference (CUDA, vLLM/SGLang/transformers serving) — this means running and paying for a dedicated GPU server continuously, which conflicts directly with the ₹10–20/user/month cost ceiling and adds real ops burden (server management, scaling, uptime) that a small team building a pilot shouldn't take on.
- A hosted multimodal LLM call achieves the same outcome (read text + understand visual context from an image) as a pay-per-call API, with no infrastructure to run or maintain.
- **When to revisit:** if the product scales significantly and image-processing volume/cost analysis shows a self-hosted model would be cheaper at that scale, or if a specific accuracy gap on a document type (e.g. dense multi-page loan contracts) can't be closed with a hosted model — this is a legitimate future optimization, just not a v1/pilot decision.

---

## 6. Security & Operations Tooling

| Component | Choice | Why |
|---|---|---|
| Secrets management | Railway environment variables | Sufficient at pilot scale; keeps secrets out of the repo entirely |
| Error & event tracking | Built-in cloud console logs | Catch failures proactively during pilot testing rather than via user complaints |
| Dependency scanning | GitHub Dependabot + `pip-audit` | Free, automatable, catches known vulnerabilities in dependencies as a routine, not a one-time check |
| Auth for internal tooling | Supabase Auth | Already part of the stack; avoids standing up a separate auth system for a small internal team + partner access |

---

## 7. Cost Tier Summary (pilot scale)

| Layer | Expected tier |
|---|---|
| Hosting (Railway) | Free/low hobby tier sufficient for pilot traffic |
| Database (Supabase) | Free tier sufficient for pilot data volume |
| WhatsApp Cloud API | Free within Meta's service-conversation allowance |
| LLM calls | The real variable cost — see Section 7 of the architecture doc for the per-conversation cost model and why call discipline (not infra) is the binding constraint |
| Error tracking / dependency scanning | Free tiers sufficient at this scale |

**Bottom line:** infrastructure cost is close to zero at pilot scale on this stack. The entire cost-ceiling conversation is about LLM call volume and model choice, not hosting — which is exactly why Sections 4 and 7 of the architecture doc deserve more attention during build than infra provisioning does.

---

## 8. Setup Checklist (Phase 0, in build order)

1. Meta Developer account → WhatsApp Business App → begin Business verification (has **multi-day lead time — start first**)
2. Supabase project → enable `vector` and `pgcrypto` extensions → run `app/db/migrations/001_initial.sql` in SQL editor
3. **Render** project → connect GitHub repo → configure all environment variables from `.env.example` → set `ENVIRONMENT=production`, `GEMINI_TIER=paid`
4. Google AI Studio / GCP project → enable Gemini API → **enable billing for the paid tier** (required before real-user traffic per `GEMINI_TIER` guard)
5. Enable Dependabot on the GitHub repo (`.github/dependabot.yml` is already committed)
6. Supabase Auth configured for internal tooling access (team-member and partner-viewer roles) — Phase 4
7. Add `RENDER_APP_URL` and `RENDER_HEALTH_CHECK_TOKEN` as GitHub Actions secrets for the keep-alive workflow

---

## 9. Documented Trade-offs (new)

Both trade-offs below are documented here so they are visible at the code level and
not just in conversation history.

### 9.1 Render free-tier cold start

- **What:** Render's free web service spins down after 15 minutes of inactivity. The first request after idle incurs a 30–60 second boot delay.
- **Impact:** Conflicts with the PRD's sub-5-second latency target for that first message.
- **Mitigation:** Keep-alive GitHub Actions workflow pings `/health` every 10 minutes.
- **Resolution:** Switch to a paid Render instance type (`starter` or above) before the pilot opens to real users, if consistent latency is required.

### 9.2 Gemini free-tier training-data policy

- **What:** The Gemini free API tier allows Google to use submitted prompts/responses to improve their models. The paid tier excludes this by default.
- **Impact:** Direct conflict with DPDP Act 2023 purpose-limitation for real users' financial conversations.
- **Mitigation:** Hard startup guard in `app/config.py` — the app refuses to start if `ENVIRONMENT=production` and `GEMINI_TIER=free`.
- **Resolution:** Enable GCP billing, set `GEMINI_TIER=paid` in Render environment variables before any real-user traffic.

---

*Companion documents: `01_PRD_Financial_Mitra.md`, `02_System_Architecture.md`, `03_Security_Compliance.md`.*
