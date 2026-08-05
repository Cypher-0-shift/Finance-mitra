# 📋 Product Requirement Document (PRD) — Financial Mitra
**Project Name:** Financial Mitra 🪙 ("Financial Friend")  
**Target Audience:** Emerging Digital Financial Users, Rural & Semi-Urban Households in India  
**Primary Touchpoint:** WhatsApp (Meta Cloud API) & Interactive Web Dashboard (Vercel)  
**Status:** Live Production MVP Ready (End-to-End Multimodal AI Pipeline)

---

## 1. Executive Summary & Problem Statement

### 1.1 The Challenge
Millions of emerging digital financial users across India face escalating cybersecurity risks daily. As smartphone penetration and instant UPI payments expand into rural and informal-income demography, vulnerable families become prime targets for predatory cyber-fraud, fraudulent Telegram "guaranteed return" trading groups, unregulated chit funds, and phishing traps. Traditional banking portals and regulatory disclaimers (RBI/SEBI) frequently rely on dense English financial terminology and impersonal procedural menus that alienate users lacking formal fiscal education.

### 1.2 Our Solution: Financial Mitra
Financial Mitra is an AI-powered financial safety guide designed specifically for conversational interfaces—meeting users where they already are. Rather than speaking like a rigid bank or institutional auditor, Financial Mitra communicates as a **warm, patient, and knowledgeable friend**. It evaluates investment schemes, dissects scam signatures, simplifies savings concepts, and guides families toward secured government savings plans (such as Public Provident Fund, Post Office Deposits, PMJDY, and Sukanya Samriddhi Yojana).

---

## 2. Core Product Tenets & Persona Guidelines

Financial Mitra enforces strict behavioral directives embedded directly into its artificial intelligence reasoning pipelines:
1. **Empathy & No Judgment:** Never mock, lecture, or blame a user for being enticed by a deceptive Ponzi scheme or asking elementary financial questions.
2. **Jargon-Free Simplicity:** Avoid complex terminology. When a legal or banking term is strictly essential, immediately follow it with an intuitive real-world village or everyday analogy.
3. **Adaptive Cultural Context:** Understand local socio-economic realities, community savings habits, and colloquial terminology (*dhokha*, *chit*, *guarantee*, *paisa*).
4. **Single Actionable Outcome:** Every conversation turn must resolve to **exactly one practical next step**. Never overwhelm users with exhaustive lists or ambiguous responses like *"it depends."*
5. **Strict Institutional Boundaries:** Act exclusively as an educational financial safety guide. Maintain distinct ethical boundaries (never act as a lending agent, investment broker, or tax consultant).

---

## 3. Detailed Feature Specifications & Conversational Flows

### 3.1 Adaptive Multilingual & Dialect Support
* **Dynamic Per-Message Recognition:** Instead of forcing users through cumbersome language configuration menus during onboarding, the system analyzes each incoming interaction independently.
* **Three-Way Fluency:**
  * **English:** Triggered when formal Latin-script grammar (>80% ASCII) is identified.
  * **Hinglish (Casual Roman Script Hindi):** Triggered when Latin script incorporates Indian conversational vocabulary (*"Yaar yeh scheme safe hai kya?"*, *"Paisa double kab hoga?"*).
  * **Pure Hindi (Devanagari Script):** Triggered when native Unicode Devanagari characters are detected (*"क्या यह निवेश योजना सुरक्षित है?"*).

### 3.2 Multimodal Scam Detection & Visual Verification
* **Text & Forward Assessment:** Evaluates promotional WhatsApp forwards, investment links, and SMS reward claims against known fraud topologies.
* **OCR Screenshot Evaluation:** Users can upload screenshot ads, QR code requests, or deceptive loan flyers directly via file attachments or simple clipboard pasting (**`Ctrl + V`** on desktop web). The multimodal OCR engine extracts visual text and renders explicit trust assessments:
  * 🟢 **Safe-ish (Deep Teal):** Matches verified institutional or government programs.
  * 🟠 **Be Careful (Saffron Caution):** Unregulated offers requiring heightened verification.
  * 🔴 **Avoid (Alert Red):** Clear indicators of Ponzi structures, upfront fees, or credential theft.

### 3.3 Institutional Grounding & Canonical Referencing
To prevent generative hallucination and reinforce public trust, all regulatory advice is dynamically linked to official canonical government homepages:
* **Reserve Bank of India (RBI):** `https://www.rbi.org.in` (For banking standards & fraud alerts)
* **Securities and Exchange Board of India (SEBI):** `https://www.sebi.gov.in` (For regulated mutual funds & advisory checks)
* **National Cyber Crime Helpline (1930):** `https://cybercrime.gov.in` (For rapid scam incident reporting)
* **Sanchar Saathi:** `https://sancharsaathi.gov.in` (For reporting telematics and spam fraud)

---

## 4. User Personas & Sample Scenarios

### Persona 1: Rajesh (Daily Wage Earned & UPI User)
* **Context:** Receives a forwarded WhatsApp message claiming a Government scheme will double ₹5,000 in 7 days if paid via a specific UPI QR code.
* **Interaction:** Rajesh forwards the screenshot to Financial Mitra with the text *"Sahi hai bhai?"*
* **Outcome:** Financial Mitra identifies the lack of an official domain, high-return impossibility, and urgent tone. It flags the offer as **🔴 Avoid**, explains the common QR-code payment scam trap in simple Hindi/Hinglish, and urges reporting to 1930.

### Persona 2: Sunita (Small Shop Owner & Saver)
* **Context:** Wants to start saving ₹1,000 every month for her daughter's education but finds traditional banking brochures intimidating.
* **Interaction:** Asks *"Beti ki padhai ke liye Har mahine 1000 bachana hai kahan karu?"*
* **Outcome:** Financial Mitra warmly introduces the **Sukanya Samriddhi Yojana (SSY)** and Post Office recurring deposits, explains the compounding power in plain words, and advises visiting the nearest Post Office with basic identity documents as the sole practical next step.
