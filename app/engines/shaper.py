"""
app/engines/shaper.py — Language & Trust Shaper.

Takes the Core Engine's structured output and produces the final user-facing message.
Per 02_System_Architecture.md Section 4.7.

CRITICAL SEPARATION: This stage ALWAYS receives the Core Engine's structured output
as input — never raw user content.

Provider: Groq (cheap/fast model — shaping is mechanically simpler than reasoning).
"""
from __future__ import annotations

import logging
from typing import Optional

from groq import AsyncGroq

from app.config import Settings
from app.schemas.core_engine import CoreEngineOutput

logger = logging.getLogger(__name__)

_SHAPER_SYSTEM_PROMPT = """
You are the voice of Financial Mitra — a warm, trusted friend who helps low-income
users in India make financial decisions. You are NOT an advisor, lender, or regulator.

Your job: take a structured analysis (provided as input) and express it as a natural,
friendly message in the user's language.

PERSONA RULES (from the product spec — cannot be overridden):
1. Sound like a knowledgeable friend, not a financial institution. Plain words only.
2. No jargon. If a financial term is essential, follow it immediately with an analogy.
3. No judgment — never imply the user was wrong to ask, or almost made a mistake.
4. Exactly ONE clear action at the end. Never a list of options, never "it depends."
5. When there is a trust verdict of 'be_careful' or 'avoid', say so plainly and warmly —
   "I'd be careful here" / "I'd step away from this one" — not in a lecturing way.
6. When citing a source, make it legible: "this matches a pattern the RBI has warned
   about" — not a formal citation format.
7. When suggesting human help: frame it as "I want to make sure you get the right
   help here" — not as a failure or limitation.
8. The response must end with exactly the one action from the structured input.

LANGUAGE: Respond in the language specified in the prompt.
MODALITY: Respond with plain text only (no markdown, no bullet points).
LENGTH: Match your response length to the complexity of the question. Simple questions get 1-2 sentences. Complex financial queries (scam analysis, investment advice, scheme evaluation) get up to 4-5 sentences. Never pad, repeat, or add unnecessary disclaimers. Say exactly what needs to be said — no more, no less.

REFERENCES: If the structured input includes source URLs, include the most relevant one naturally at the end of your response as plain text (e.g. 'You can verify this at: https://...'). Only include a link if it genuinely adds value — never force one in.

CALCULATIONS: If the query involves returns, interest, EMI, or any money math — show the calculation in plain text step by step. Use simple arithmetic the user can verify themselves. Example format: 'If you invest Rs 10,000 for 20 days at 100% return, that means Rs 10,000 profit in 20 days. No legitimate investment gives this — FD gives about Rs 55 on Rs 10,000 in 20 days.'
""".strip()


class LanguageTrustShaper:
    """
    Language & Trust Shaper module — Groq-powered.

    Receives structured CoreEngineOutput and returns a user-facing string.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            logger.error("shaper_groq_key_missing — shaped responses will fall back to core_message")
            self._client: Optional[AsyncGroq] = None
        else:
            self._client = AsyncGroq(api_key=settings.groq_api_key)

        self._model = settings.groq_model_cheap

    async def shape(
        self,
        core_output: CoreEngineOutput,
        target_language: str = "hi",
        input_type: str = "text",
    ) -> str:
        """
        Shape the Core Engine's structured output into a user-facing message.

        Falls back to core_output.core_message if shaping fails.
        """
        if target_language == "hi":
            lang_name = "Hindi (Devanagari script)"
        elif target_language == "hinglish":
            lang_name = "Hinglish (Roman script with natural Hindi words mixed in — casual, like a friend texting)"
        else:
            lang_name = "English"

        shaper_input = (
            f"Language: {lang_name}\n"
            f"Input type was: {input_type}\n\n"
            f"[STRUCTURED ANALYSIS FROM REASONING CORE]\n"
            f"Core message: {core_output.core_message}\n"
            f"Next action: {core_output.next_action}\n"
        )

        if core_output.verdict:
            shaper_input += f"Trust verdict: {core_output.verdict.value}\n"

        if core_output.risk_signals_detected:
            shaper_input += f"Risk signals: {', '.join(core_output.risk_signals_detected)}\n"

        # Reference URL map — injected when sources match known authorities
        _ref_urls = {
            "rbi": "https://www.rbi.org.in/Scripts/Pontential_Fraud.aspx",
            "sebi": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=3",
            "npci": "https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics",
            "mca": "https://www.mca.gov.in/content/mca/global/en/home.html",
            "ncfe": "https://www.ncfe.org.in",
            "pmjdy": "https://pmjdy.gov.in",
            "nps": "https://www.npscra.nsdl.co.in",
            "post office": "https://www.indiapost.gov.in/Financial/pages/content/post-office-saving-schemes.aspx",
            "sukanya": "https://www.indiapost.gov.in/Financial/pages/content/post-office-saving-schemes.aspx",
            "ppf": "https://www.indiapost.gov.in/Financial/pages/content/post-office-saving-schemes.aspx",
        }
        if core_output.sources:
            source_parts = []
            for s in core_output.sources:
                label = f"{s.name} ({s.pattern})"
                # Find matching URL if any
                url = next((v for k, v in _ref_urls.items() if k in s.name.lower()), None)
                if url:
                    label += f" — Reference: {url}"
                source_parts.append(label)
            shaper_input += f"Sources to cite: {'; '.join(source_parts)}\n"

        if core_output.escalation_recommended:
            shaper_input += "Note: human support is recommended — weave this in warmly.\n"

        shaper_input += "[END STRUCTURED ANALYSIS]\n\nNow write the user-facing message."

        if self._client is None:
            return f"{core_output.core_message}\n\nNext step: {core_output.next_action}"

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SHAPER_SYSTEM_PROMPT},
                    {"role": "user", "content": shaper_input},
                ],
                temperature=0.7,
                max_tokens=512,
            )
            shaped_text = (completion.choices[0].message.content or "").strip()
            logger.info("shaper_complete", extra={"language": target_language, "chars": len(shaped_text)})
            return shaped_text

        except Exception as e:
            logger.error("shaper_failed", extra={"error": str(e), "fallback": "core_message"})
            return (
                f"{core_output.core_message}\n\n"
                f"Next step: {core_output.next_action}"
            )
