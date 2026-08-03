# Product Requirements Document — Financial Mitra
### Team ZENVEST | v2 — Enterprise-Grade Build Spec

*Revision note: this supersedes the Phase 2 PRD. Changes from v1: multimodal input (text/voice/image) promoted from "out of scope" to v1, persona explicitly defined ("friend who knows when to hand off to a human"), security/compliance elevated to a first-class section given multi-user pilot testing, and the response pipeline restructured into a language-agnostic reasoning core + a separate localization/trust-shaping stage.*

---

## 1. Executive Summary

Financial Mitra is a WhatsApp-first AI financial companion that helps low-income, informal-income individuals in India make confident everyday financial decisions and avoid scams — through simple, jargon-free, trustworthy conversations in their own language, accepting text, voice, or a photo of whatever they're looking at.

**Problem:** Low-income and underbanked users struggle to make confident everyday financial decisions because financial information is scattered, hard to understand, not personalized, and doesn't clearly tell them what action to take. This is compounded by real vulnerability to scams and exploitation (chit funds, fake loan apps, predatory moneylenders), where a single bad decision can be catastrophic given the lack of any financial cushion.

**Solution:** An AI companion, accessible entirely within WhatsApp (text, voice note, or photo — no app download), that (a) helps users decide what to do with money they have, and (b) tells them clearly whether an offer, scheme, or loan is trustworthy — always ending in one concrete next action, and escalating to a human partner when risk or distress is detected.

**v1 scope:** Two trigger moments — "sudden money in hand" and "is this offer trustworthy" — across three input types (text, voice, image), chosen because scam material overwhelmingly arrives as a screenshot or photo (a WhatsApp forward, a loan-app screen, a poster), not typed text. Supporting that properly is core to the value proposition, not a stretch feature.

---

## 2. Goals & Success Metrics

**North Star Metric:** Number of users who complete at least one meaningful financial action per month (started a savings habit, avoided a high-cost loan/scam, successfully applied for a government scheme).

| Category | Metric |
|---|---|
| Adoption | Weekly/Monthly Active Users, activation rate (first meaningful interaction) |
| Trust & Safety | Scam alerts triggered per week, escalations to human support, user complaints per 1,000 users |
| Behavior change | % of users who start saving regularly, reduction in high-cost informal borrowing |
| Retention | Day-7 and Day-30 retention |
| Unit economics | Cost per AI interaction, cost per completed financial action |
| **Security & trust (new)** | Zero unauthorized data disclosures; escalation SLA adherence %; auth/abuse incidents per 1,000 users |

---

## 3. Users & Jobs To Be Done

*(Unchanged from Phase 2 — restated for completeness.)*

**v1 trigger moments (in scope):**
1. **Sudden money in hand** — "I just got paid / a lump sum — what do I do with it?"
2. **Being offered something that sounds good** — "Is this scheme / loan / offer trustworthy?"

**v2+ trigger moments (documented for context, out of scope for v1):** unexpected expense/shock, wanting to start "doing it right" from zero, being chased/pressured for money.

**Illustrative personas:**
- **Ramesh** — construction worker, irregular income + lump sums after project completion, low literacy, WhatsApp-comfortable.
- **Radha** — household helper, steady monthly income, targeted by a neighbor's chit fund scheme, likely to forward a screenshot of the offer rather than type it out.

---

## 4. Product Principles (expanded)

These govern every prompt, every UI decision, every escalation rule. If a build decision conflicts with one of these, the principle wins.

1. **Action over information.** Every response ends in exactly one thing to do next — never a list, never "it depends," never advice without an action.
2. **No judgment, ever.** The tone never implies the user was foolish for asking, for almost falling for something, or for not knowing a term.
3. **Trust is the product.** Every trust-check verdict is explainable in one plain sentence, and (new) backed by a visible, plain-language source reference — "this matches a pattern regulators have warned about" beats an unexplained verdict.
4. **A friend who knows when to hand off.** Warm, informal, non-corporate tone — but explicit and unembarrassed about routing to a real human when something is beyond what a chatbot should decide alone. This handoff is a trust signal, not a failure state, and should be worded that way.
5. **Never the last word on money movement.** The AI explains and recommends; it never executes, applies, sends, or authorizes anything financial on the user's behalf. Permanent, not phase-based.
6. **Language and modality follow the user, not the other way around.** If they send a voice note, they get one back. If they send a photo, that's a fully first-class input, not a degraded path.

---

## 5. Scope

### In scope (v1 MVP)
- WhatsApp conversational intake — **text, voice note, and image**, Hindi + English
- "Should I trust this?" scam/scheme trust-check — including from a photographed or forwarded screenshot, with plain-language verdict, reason, and source reference
- "What should I do with this money?" guided decision flow
- Jargon-free explainers using everyday analogies
- One clear next action per conversation, every time
- Human escalation path to an NGO/MFI partner for high-risk or distress cases
- Basic engagement/impact logging for the North Star metric
- **Enterprise-grade security baseline for multi-user pilot testing** (Section 10): authentication/access control for internal tooling, encryption in transit and at rest, rate limiting and abuse prevention, audit logging, incident response plan, and DPDP Act 2023–aligned data handling — required *before* opening testing beyond the core team, not a post-launch add-on.

### Explicitly out of scope (v1)
- Alternative credit scoring / micro-loan referrals (v2)
- SHG/group coaching mode (v2/v3)
- IVR/missed-call access for feature-phone users (v3)
- Government scheme eligibility checker (v1.x)
- Any autonomous execution of financial transactions (permanent non-goal, see Section 4.5)
- Self-hosted, GPU-based OCR/vision models (see Section 9 — a hosted multimodal LLM call handles image understanding directly; running your own vision-model inference server is out of scope for cost and ops-burden reasons)

---

## 6. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | User can message the WhatsApp Business number in text, voice note, or image, in Hindi or English. |
| FR-2 | System detects intent among: (a) "what to do with money I have," (b) "is this scheme/offer trustworthy," (c) general question — regardless of whether the input was text, transcribed voice, or an image description. |
| FR-3 | For intent (a): system asks at most 1–2 clarifying questions (amount, urgency, existing goals), then returns one concrete, prioritized suggestion. |
| FR-4 | For intent (b): system evaluates the input — including image content — against known scam-pattern signals (Section 9.5) and returns a clear verdict — safe-ish / be careful / avoid — with one plain-language reason and, where applicable, a named source reference. |
| FR-5 | If high risk or distress is detected in the conversation, system offers to connect the user to a human NGO/MFI partner and creates an escalation record — this check runs on every turn, unconditionally, regardless of intent. |
| FR-6 | System matches output modality to input modality by default (voice in → voice out; image in → text out, since a spoken description of an image is unnatural) and always allows the user to request the other. |
| FR-7 | Every conversation turn ends with exactly one clear, specific next action — never advice without an action, and never more than one action at once. This is enforced by a structured output schema, not left to free-form generation. |
| FR-8 | System never instructs the user to send money, share OTPs, or take any specific irreversible financial action on the AI's say-so alone. |
| FR-9 | System logs each meaningful financial action (for the North Star metric) without exposing personally identifying conversation content to the analytics layer. |
| FR-10 *(new)* | When the input is an image, the system processes it via a multimodal model call rather than a separate self-hosted OCR pipeline, and treats any text or claims extracted from the image with the same scam-pattern evaluation as typed text. |
| FR-11 *(new)* | All inbound webhook requests are cryptographically verified (signature check) before any processing occurs; unverified requests are rejected and logged. |
| FR-12 *(new)* | Any internal tooling or dashboard used by the team or NGO/MFI partner requires authenticated access with role-based permissions — no shared passwords, no unauthenticated escalation queue. |

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Language coverage | Hindi + English for v1; architecture must not hard-code language handling. |
| Modality coverage | Text, voice, and image must all be first-class inputs in v1 — none is a "phase 2 nice-to-have." |
| Latency | Target sub-5-second response for text/image; voice may run longer due to STT/TTS round-trip — measure and set a realistic SLA after Phase 1 testing rather than assuming. |
| Availability | Dependent on WhatsApp Cloud API uptime; define a fallback message for downtime windows. |
| **Data security** *(expanded)* | Conversation logs, images, and voice recordings encrypted at rest and in transit; access to the escalation queue and any raw conversation data restricted to a named, authenticated set of individuals; secrets never stored in code or logs. See Section 10 for the full security baseline. |
| **Data privacy** *(expanded)* | Retention and anonymization policy defined and implemented — not just documented — before any user outside the core team accesses the system. Must account for the fact that pilot testing involves real people's real financial situations, not synthetic test data. |
| Cost ceiling | Per-conversation AI inference + WhatsApp messaging cost should stay within ₹10–₹20/user/month. Hard design constraint — directly limits clarifying back-and-forth and number of model calls per conversation (now two calls per turn under the reasoning-core/shaper split — see architecture doc). |
| Accessibility | Voice input/output reliable for low-literacy users; image input must tolerate real-world photo conditions (glare, blur, low light) common on low-end phone cameras. |
| **Abuse resistance** *(new)* | System must withstand a multi-user pilot without a single bad actor (spam, prompt injection via image/text, scraping attempts) degrading service or cost for other users. See Section 10.4. |

---

## 8. Persona & Response Pipeline (Product-level view)

*(Engineering detail lives in the System Architecture doc — this section defines the product behavior the pipeline must deliver.)*

The response to any user turn is built in two conceptually separate stages:

1. **Understand & Reason** — figure out what's being asked (across text/voice/image), retrieve relevant scam-pattern or guidance knowledge, and produce the *substance* of the answer: what's true, what the verdict is, what the one next action should be. This stage is language-agnostic.
2. **Shape & Deliver** — take that substance and turn it into something that sounds like a warm, plain-spoken friend talking in the user's own language, with source references made legible ("this matches a pattern the RBI has warned people about" rather than a citation format), and packaged for the right output modality.

Keeping these separate means the *substance* of a trust verdict can be tested and audited independently of how it's phrased — important for a safety-critical feature being used by real people during a pilot.

---

## 9. AI Workflow & Agent Workflow

**Input handling:**
- Text → passed directly to the reasoning core.
- Voice note → speech-to-text, then passed as text.
- Image → passed directly to a multimodal LLM call (not a separate self-hosted OCR model — see Section 5, out-of-scope) that both reads any text in the image and understands visual context (e.g. a loan app's UI, a poster's design cues), producing a structured description the reasoning core can act on.

**Reasoning core:** retrieves from the RAG scam-pattern knowledge base, reasons about intent and risk, and produces structured output (verdict, next action, risk flags, sources) — not free text.

**RAG layer:** curated knowledge base of known scam patterns (guaranteed high returns, pressure to act fast, unregistered/unlicensed entities, upfront fees, unrealistic promises), sourced from the RBI Annual Report on Financial Inclusion, NGO/MFI practitioner input, and Phase 1 research. Needs a named maintenance owner — scam tactics evolve.

**Language & trust shaper:** localizes the structured output into the user's language and register, attaches source references in plain language, and packages for the correct output modality.

**Agentic pieces — used narrowly:**
1. **Escalation agent:** on detecting high scam-risk or distress signals, autonomously routes to a human NGO/MFI partner queue and creates a logged escalation record. The one place autonomy is a safety feature, not a growth feature.
2. **Check-in agent:** lightweight periodic follow-up on a user's stated goal. Scoped narrowly to avoid becoming an unscoped "autonomous financial advisor."

**Explicit non-goal (permanent):** the AI never autonomously moves money, applies for a loan, or takes any irreversible financial action on the user's behalf.

---

## 10. Security & Compliance (new — required before multi-user pilot)

This section exists because pilot testing means real people, outside the core team, sending real financial situations through the system — the security bar has to match that from day one, not be retrofitted after an incident.

### 10.1 Principle
Treat every pilot user the way you'd treat a production user, because during testing, they effectively are one — with real financial information and real trust being placed in the product.

### 10.2 Baseline requirements (detailed in the Security & Compliance doc)
- Authenticated, role-based access to any internal tooling, dashboards, or the escalation queue — no shared credentials, no public-by-default admin views.
- Encryption in transit (TLS everywhere) and at rest (database-level and, for message content, consider application-level encryption given sensitivity).
- Webhook signature verification on every inbound request (FR-11).
- Secrets management via environment variables / a secrets manager — never in source control.
- Rate limiting and abuse detection to prevent a single user or bad actor from degrading service or blowing the cost budget for everyone else.
- Input validation and prompt-injection resistance, particularly for image inputs, which are a less-tested attack surface than text.
- Audit logging of who accessed what (especially escalation records and raw conversation content) and when.
- A documented incident response plan — what happens if there's a data exposure or a serious model failure (e.g. a wrong "safe" verdict on a real scam) during the pilot.

### 10.3 Regulatory alignment
- **DPDP Act 2023 (India's Digital Personal Data Protection Act):** Financial Mitra processes personal and financial data of Indian residents and must align with DPDP principles — purpose limitation, data minimization, consent for data collection, and a defined retention/deletion policy. This is not optional groundwork for a pilot involving real users' financial situations.
- **RBI guidance:** while Financial Mitra doesn't itself extend credit or move money (permanent non-goal, Section 4.5), it discusses financial products and schemes — worth a light-touch review against RBI's general guidance on digital lending—adjacent communication, even though it falls outside formal digital lending regulation.

### 10.4 Abuse resistance for pilot scale
With multiple real testers, expect: spam/nuisance messages, attempts to jailbreak the escalation logic, attempts to extract the system prompt or scam-pattern KB, and simple cost-exhaustion attempts (rapid-fire messages). Rate limiting, per-user cost caps, and basic anomaly alerting are pilot-scale requirements, not later hardening.

*(Full threat model, control list, and compliance mapping in `03_Security_Compliance.md`.)*

---

## 11. Acceptance Criteria (sample, updated)

**Scam/trust-check feature:**
- Given a user describes or photographs an investment, loan, or scheme offer, when the system evaluates it, then it returns a trust verdict (safe-ish / be careful / avoid) with one reason and, where a match exists, a named source reference, within the target response time.
- Given the verdict is "be careful" or "avoid," when delivered, then the response includes exactly one specific reason and one specific recommended action.
- Given high risk or distress is detected, when the conversation ends, then an escalation record is created and a human partner is notified.
- Given an image input, when it contains readable text or a recognizable loan-app/scheme UI, then the system correctly extracts and evaluates that content without requiring the user to also type a description.

**Money-decision feature:**
- Given a user describes receiving money (amount, source, timing), when the system responds, then it asks at most 1–2 clarifying questions before giving one prioritized suggestion.
- Given a suggestion is given, when the conversation ends, then it includes exactly one concrete next action, phrased in plain language with no financial jargon.

**Security (new):**
- Given a webhook request without a valid signature, when it arrives, then it is rejected and logged, and no processing occurs.
- Given a single user sends an abnormally high volume of messages in a short window, when the rate limit is exceeded, then further messages are throttled with a polite explanation, and an internal alert fires.
- Given any team member or partner accesses the escalation queue or raw conversation data, when they do so, then the access is authenticated, role-checked, and logged.

---

## 12. Release Plan

| Version | Scope |
|---|---|
| v1 (MVP) | Trigger moments #1 and #2, all three input modalities (text/voice/image), Hindi + English, human escalation, full security baseline (Section 10). |
| v1.x | Government scheme eligibility checker. Regional language coverage based on pilot geography. |
| v2 | Trigger moments #3 (unexpected expense) and #5 (being chased for money). Alternative credit scoring API for partner NBFCs/MFIs — requires RBI compliance review before build. |
| v3 | SHG/group coaching mode. IVR/missed-call access for feature-phone users. |

---

## 13. Open Questions Carried Into Build

- MVP anchor moment prioritization (#1 and #2) is inferred from Phase 1 secondary research — validate against primary interviews.
- Which regional languages beyond Hindi to prioritize for v1.x depends on pilot geography, not yet chosen.
- Ownership of WhatsApp Cloud API setup and the NGO/MFI partner relationship for human escalation is not yet assigned within the team.
- **New:** who owns the DPDP compliance review and sign-off before pilot testing opens beyond the core team — this needs a named owner, not an assumption that "someone will handle it."
- **New:** the NGO/MFI partner's escalation SLA and the incident-response point of contact both need to be agreed *in writing* before pilot launch, given real users will be relying on both.

---

*Prepared by Team ZENVEST. Companion documents: `02_System_Architecture.md`, `03_Security_Compliance.md`, `04_Tech_Stack.md`.*
