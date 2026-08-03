# 📋 Product Requirement Document (PRD) — Financial Mitra

**Project Name:** Financial Mitra  
**Target Audience:** Rural & Semi-Urban Low-Income Households in India  
**Platform / Interface:** WhatsApp (via WhatsApp Cloud API)  
**Current Status:** Live End-to-End Operational Pipeline (MVP / Demo Ready)  

---

## 1. Executive Summary & Problem Statement

### 1.1 The Challenge
Millions of emerging financial and digital users in rural and semi-urban India face severe financial security risks daily. As smartphone penetration and instant UPI digital payments scale, vulnerable users become prime targets for cyber-fraud, Ponzi schemes, unregulated chit funds, and fraudulent Telegram "high-return" investment groups. 
Traditional banking portals and regulatory guidelines (RBI/SEBI) often rely on heavy English financial jargon, rigid procedural steps, and impersonal communication styles that alienate users who lack formal financial literacy.

### 1.2 Our Solution: Financial Mitra
**Financial Mitra** ("Financial Friend") is an AI-powered financial safety guide designed specifically for WhatsApp—the most widely adopted interaction platform across urban and rural Indian demography. 

Rather than acting as an authoritative bank or preachy financial institution, Financial Mitra communicates as a **warm, knowledgeable, and empathetic friend**. It evaluates investment opportunities, uncovers deceptive scam signatures, simplifies complex financial products, and guides families toward secured government savings plans (such as Post Office Schemes, PPF, PMJDY, and Sukanya Samriddhi Yojana).

---

## 2. Core Product Tenets & Persona Guidelines

Financial Mitra enforces absolute behavioral directives directly embedded into its natural language delivery pipeline:
1. **Empathy & No Judgment:** Never blame, mock, or lecture the user for being enticed by a fraudulent scheme or asking basic financial questions.
2. **Jargon-Free Simplicity:** Avoid dense technical vocabulary. If a financial term is strictly essential, follow it immediately with an intuitive real-world analogy.
3. **Adaptive Cultural Context:** Understand local socio-economic dynamics, Indian colloquial terminology (*dhokha*, *paisa*, *chit*, *scheme*), and community savings behaviors.
4. **Single Actionable Outcome:** Every conversation turn must end with **exactly one clear, practical next step**. Never overwhelm users with complex multi-choice lists or vague answers like *"it depends."*
5. **Legality & Boundaries:** Act solely as an educational financial safety mentor, explicitly maintaining boundaries (not a lending institution, stockbroker, or legal regulator).

---

## 3. Detailed Feature Requirements & Functional Specifications

### 3.1 Adaptive Multilingual & Dialect Support (English, Hindi, Hinglish)
* **Dynamic Per-Message Recognition:** Instead of locking a user into a static preference during onboarding, the AI inspects every incoming message independently using ASCII character ratio analysis and specialized lexicon scanning.
* **Three-Way Fluency:**
  * **English:** Triggered when structured Latin-script text (>80% ASCII) is detected without native colloquial slang.
  * **Hinglish (Casual Roman Script Hindi):** Triggered when Latin script contains conversational Indian vocabulary (*"yaar yeh scheme safe hai kya"*, *"paisa kab milega"*).
  * **Pure Hindi (Devanagari Script):** Triggered when native Unicode script is utilized (*"क्या यह स्कीम सुरक्षित है?"*).

### 3.2 Multimodal Scam Detection & Image Evaluation
* **Text-Based Fraud Analysis:** Parses promotional messages, forwarded texts, and suspicious return promises.
* **Vision Engine Integration:** Users can forward screenshots of scam flyers, QR codes, UPI fraudulent payment prompts, or deceptive Telegram advertisements. The platform extracts OCR textual contents and evaluates visual symbols to generate plain-language trust warnings.

### 3.3 Institutional Reference Links
When verifying a scheme or identifying fraud patterns, the system matches authorities to official Indian regulatory portals to bolster institutional trust without cluttering responses:
* **Reserve Bank of India (RBI) / Financial Fraud:** `https://www.rbi.org.in` & Potential Fraud warnings.
* **Securities and Exchange Board of India (SEBI):** Recognized FPI and investor guidelines.
* **National Payments Corporation of India (NPCI):** UPI ecosystem security standards.
* **India Post & Ministry of Finance:** Official Post Office Savings Schemes, PMJDY, and PPF references.
* **Rule:** References appear cleanly as plain-text URLs at the very end of statements only when contextually justified.

### 3.4 Plain-Text Financial Math & Educational Calculations
* When responding to interest rates, investment returns, or scam calculations, the AI provides transparent, step-by-step arithmetic explanations in plain text.
* **Scam Contrast Calculation Test:** Specifically demonstrates unrealistic returns (e.g., contrasting *"100% ROI in 20 days on ₹10,000"* against a legitimate Bank FD yield of ~₹55 over the same period).

### 3.5 Conversation Lifecycle Management (Short-Circuits & Reset)
* **Greeting Short-Circuit:** Recognizes common greetings (*"hi"*, *"hello"*, *"namaste"*) and responds immediately with an engaging introductory banner without invoking heavy multi-step reasoning models.
* **Session Reset Command:** Allows users to reset conversation contexts cleanly using instinctive phrases (*"restart"*, *"new chat"*, *"phir se"*, *"naya shuru"*). This updates database states to archive old context and presents a clean slate.

### 3.6 Risk Gate & Empathetic Human Escalation
* **Distress Detection:** Monitors messages for severe emotional distress, heavy actualized financial loss, or acute vulnerability.
* **Warm Escalation Framing:** Recommends human intervention without triggering panic or implying technological limitation: *"I want to make sure you get the right personalized human support here."* Automatically flags escalations into database monitors for support partners.

---

## 4. Key Performance Indicators & North Star Metrics

To measure genuine socioeconomic utility beyond simple messaging traffic, Financial Mitra implements real-time database logging for two core **North Star Metrics**:

| Metric Name | Trigger Definition | Impact Goal |
| :--- | :--- | :--- |
| **🛡️ Scams Avoided** (`scam_avoided`) | Triggered when an interactive reasoning thread successfully exposes a high-risk fraud pattern and issues a definitive `avoid` or `be_careful` verdict to an endangered user. | Measuring capital preservation and fraud prevention across targeted low-income cohorts. |
| **🌱 Savings Started** (`savings_started`) | Triggered when an educational dialogue concludes with an endorsed recommendation toward organized secure government/bank instruments (FD, PPF, Sukanya Samriddhi, Post Office). | Driving financial inclusion and disciplined capital wealth generation. |

---

## 5. User Interaction Workflows (Sample Use-Cases)

### Use-Case A: Deferring an Unregulated Telegram Scam (Hinglish Mode)
* **User:** *"Bhai ek telegram group mein bol rahe hai ki 5000 lagao aur 20 din mein double milenge via UPI. Agar mai karlu toh safe hai?"*
* **Financial Mitra:** *"Bhai, meri maan toh isse door hi reh, yeh saaf dhokha (scam) lag raha hai! Koi bhi asli scheme ya bank 20 din mein paisa double nahi karti—agar tum ₹5,000 Bank FD mein rakoge toh 20 din mein sirf ₹25-30 interest milega, ₹5,000 nahi! RBI ne bhi aise telegram aur UPI schemes ke against taazatreen warning jaari ki hai. Ek kaam karo: us telegram group ko abhi block aur report kar दो! Reference: https://www.rbi.org.in/Scripts/Pontential_Fraud.aspx"*

### Use-Case B: Exploring Legitimate Government Savings (Pure Hindi Mode)
* **User:** *"नमस्ते, मैं हर महीने ₹1000 अपनी बेटी के लिए बचाना चाहता हूँ। कहाँ लगाना ठीक रहेगा?"*
* **Financial Mitra:** *"नमस्ते! अपनी बेटी की भविष्य के लिए हर महीने बचत शुरू करने का आपका विचार बहुत ही सराहनीय है। इसके लिए सरकार की 'सुकन्या समृद्धि योजना' (Sukanya Samriddhi Yojana) सबसे उत्तम और सुरक्षित होगी, जिसमें सामान्य बैंकों से कहीं ज्यादा ब्याज और टैक्स छूट भी मिलती है। आप आज ही अपने नजदीकी पोस्ट ऑफिस या सरकारी बैंक जाकर बेटी का सुकन्या खाता खोलने का फार्म भरें। Reference: https://www.indiapost.gov.in/Financial/pages/content/post-office-saving-schemes.aspx"*
