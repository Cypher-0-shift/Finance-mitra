"""
app/services/risk_gate.py — Risk/Distress gate: deterministic keyword layer.

Two-layer gate per 02_System_Architecture.md Section 4.5:
  Layer 1 (this module): deterministic keyword/pattern matching — runs FIRST,
                          no LLM call needed, zero latency.
  Layer 2: CoreEngineOutput.is_high_risk() — LLM-assessed via the Core Engine.

CRITICAL INVARIANT: EITHER layer firing is SUFFICIENT to trigger escalation.
Never requires BOTH. A bug that requires both would silently miss escalations.
This is the highest-consequence invariant in the system.

Keyword list covers:
  - Self-harm / acute distress signals (English + Hindi)
  - Financial coercion / loan-shark threats
  - OTP/PIN sharing requests (always a scam pattern)
  - High-pressure time-limit tactics

The tests in tests/test_risk_gate.py import from this module so there is
ONE source of truth for the keyword list. Never duplicate it.
"""
from __future__ import annotations

from app.schemas.core_engine import CoreEngineOutput

ESCALATION_KEYWORDS: list[str] = [
    # Self-harm / distress (English)
    "suicide", "kill myself", "end my life", "can't go on", "cant go on",
    "want to die", "no reason to live",
    # Self-harm / distress (Hindi / Romanised)
    "mujhe jeena nahi", "khatam karna chahta", "khatam karna chahti",
    "jeena nahi chahta", "jeena nahi chahti",
    # Financial coercion / threats
    "threatening me", "mujhe dhamki", "will hurt", "beating me",
    "mujhe maar", "ghar aayenge", "gaon mein badnami",
    # Repayment distress
    "can't repay", "cant repay", "chuka nahi sakta", "chuka nahi sakti",
    "kaise chukaunga", "kaise chukaungi",
    # OTP / PIN / password sharing requests (always a scam signal)
    "share your otp", "otp bhejo", "apna otp", "apna pin batao",
    "apna password batao", "send me your pin", "send your otp",
    "verification code bhejo", "apna code batao",
    # High-pressure time-limit tactics
    "offer expires today", "last chance", "only today", "abhi bhejo",
    "turant paise bhejo", "emergency transfer", "abhi transfer karo",
    "sirf aaj ke liye", "kal tak band ho jayega",
]


def keyword_layer_fires(text: str) -> bool:
    """
    Returns True if any escalation keyword appears in the text.
    Case-insensitive substring match — conservative (fewer false negatives).
    False negatives here mean missed escalations, which is worse than
    false positives.
    """
    text_lower = text.lower()
    return any(kw in text_lower for kw in ESCALATION_KEYWORDS)


def should_escalate(text: str, core_output: CoreEngineOutput) -> bool:
    """
    Combined gate: EITHER layer is SUFFICIENT. Never requires BOTH.
    Per 02_System_Architecture.md Section 4.5.
    """
    return keyword_layer_fires(text) or core_output.is_high_risk()


def escalation_reason(text: str, core_output: CoreEngineOutput) -> str:
    """
    Returns the reason string for the escalations table.
    Values: 'keyword' | 'llm_flag' | 'both'
    """
    kw = keyword_layer_fires(text)
    llm = core_output.is_high_risk()
    if kw and llm:
        return "both"
    if kw:
        return "keyword"
    return "llm_flag"
