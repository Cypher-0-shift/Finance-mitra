"""
app/engines/intent_router.py — Intent classification via Groq.

Classifies normalised user input into one of three intents:
  - money_decision: "what do I do with money I have?"
  - trust_check: "is this offer/scheme/loan trustworthy?"
  - general: everything else

Per 02_System_Architecture.md Section 4.3:
  "Lightweight, fast, and cheap — this can be a smaller/cheaper model call."

Provider: Groq cheap model (llama-3.1-8b-instant) — fast, deterministic classification.
"""
from __future__ import annotations

import logging
from typing import Literal, Optional

from groq import AsyncGroq

from app.config import Settings

logger = logging.getLogger(__name__)

Intent = Literal["money_decision", "trust_check", "general"]

_VALID_INTENTS = {"money_decision", "trust_check", "general"}

_INTENT_SYSTEM_PROMPT = """
You are a message classifier for a financial advice assistant. Classify the user's
message into EXACTLY ONE of these three categories:

- money_decision: The user is asking what to do with money they have, how to save,
  spend, or invest a sum of money, or asking for financial guidance on a decision
  about their own funds.

- trust_check: The user is asking whether a financial scheme, loan offer, investment,
  chit fund, or business opportunity is legitimate, safe, or trustworthy. This also
  applies when the user describes or shares something a person or company offered them.

- general: Anything that doesn't clearly fit the above two.

Respond with ONLY one word: money_decision, trust_check, or general.
No explanation, no punctuation, just the single category word.
""".strip()


class IntentRouter:
    """Lightweight intent classifier using Groq's cheap/fast model."""

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            logger.error("intent_router_groq_key_missing — all intents will fall back to 'general'")
            self._client: Optional[AsyncGroq] = None
        else:
            self._client = AsyncGroq(api_key=settings.groq_api_key)

        self._model = settings.groq_model_cheap

    async def classify(self, normalized_text: str) -> Intent:
        """
        Classify normalised input into an intent.
        Falls back to 'general' on any error.
        """
        if self._client is None:
            return "general"

        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": normalized_text},
                ],
                temperature=0.0,
                max_tokens=10,
            )
            raw = (completion.choices[0].message.content or "general").strip().lower()

            if raw in _VALID_INTENTS:
                logger.info("intent_classified", extra={"intent": raw})
                return raw  # type: ignore[return-value]

            # Fuzzy match — model returned extra text around the intent word
            for intent in _VALID_INTENTS:
                if intent in raw:
                    logger.warning(
                        "intent_classification_fuzzy_match",
                        extra={"raw": raw, "matched": intent},
                    )
                    return intent  # type: ignore[return-value]

            logger.warning(
                "intent_classification_unrecognised",
                extra={"raw": raw, "fallback": "general"},
            )
            return "general"

        except Exception as e:
            logger.error(
                "intent_router_failed",
                extra={"error": str(e), "fallback": "general"},
            )
            return "general"
