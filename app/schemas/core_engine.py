"""
app/schemas/core_engine.py — Pydantic schema for Core Engine structured output.

This schema is the EXACT structure specified in 02_System_Architecture.md Section 4.4.
Do not change field names, types, or optionality without updating the spec first.

Every LLM response from the Core Engine MUST be validated against this schema before
it is allowed to proceed downstream (to the Shaper, the Risk/Distress gate, or storage).
Validation failures trigger the retry-then-fallback behaviour defined in main pipeline.

This schema is also the primary defence against prompt injection: the structured output
constrains what the model can do with a response regardless of what injected content
tries to instruct it to do (03_Security_Compliance.md Section 5.3).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TrustVerdict(str, Enum):
    """Verdict field for trust_check intent. Null for non-trust-check intents."""
    SAFE_ISH = "safe_ish"
    BE_CAREFUL = "be_careful"
    AVOID = "avoid"


class SourceCitation(BaseModel):
    """A named, plain-language source reference for a trust verdict."""
    name: str = Field(
        ...,
        min_length=1,
        description="Name of the source (e.g. 'RBI Annual Report on Financial Inclusion')",
    )
    pattern: str = Field(
        ...,
        min_length=1,
        description="The specific scam pattern this source describes (e.g. 'upfront fee scam')",
    )


class CoreEngineOutput(BaseModel):
    """
    Exact structured output schema from 02_System_Architecture.md Section 4.4.

    The Core Engine's LLM call must return JSON matching this schema.
    Validated by Pydantic before the output is allowed to:
      - Flow to the Language & Trust Shaper
      - Be evaluated by the Risk/Distress gate
      - Be written to messages.core_engine_output

    If validation fails: retry once with a stricter prompt, then fall back to a
    canned safe response. Never pass malformed content downstream.
    """

    core_message: str = Field(
        ...,
        min_length=1,
        description=(
            "The substance of the answer in neutral/English-internal form. "
            "Language-agnostic — the Shaper localises this. "
            "MUST NOT contain user-facing phrasing, jargon, or modality-specific formatting."
        ),
    )

    next_action: str = Field(
        ...,
        min_length=1,
        description=(
            "Exactly ONE specific, concrete next action for the user. "
            "FR-7: every response ends with exactly one action, never more. "
            "Never left empty — if uncertain, the action is 'speak to a trusted person first'."
        ),
    )

    verdict: Optional[TrustVerdict] = Field(
        default=None,
        description=(
            "Trust verdict for trust_check intent. "
            "Must be null for money_decision and general intents. "
            "Must be non-null for trust_check intent."
        ),
    )

    risk_signals_detected: list[str] = Field(
        default_factory=list,
        description=(
            "List of specific scam-pattern signals detected. "
            "Empty list if none detected (not null). "
            "Each string should name the pattern, not describe it verbosely."
        ),
    )

    escalation_recommended: bool = Field(
        ...,
        description=(
            "Whether the Core Engine recommends human escalation. "
            "True triggers the Risk/Distress gate's LLM-layer — combined with "
            "the keyword layer, EITHER one firing is sufficient to escalate (not both). "
            "02_System_Architecture.md Section 4.5."
        ),
    )

    sources: list[SourceCitation] = Field(
        default_factory=list,
        description=(
            "Named source references for trust verdicts. "
            "Empty for non-trust-check intents. "
            "The Shaper converts these into plain-language trust cues for the user."
        ),
    )

    @field_validator("verdict", mode="before")
    @classmethod
    def validate_verdict_string(cls, v: str | None) -> str | None:
        """Normalise verdict strings to lowercase before Enum validation."""
        if v is None:
            return v
        return v.lower().strip() if isinstance(v, str) else v

    @field_validator("risk_signals_detected", mode="before")
    @classmethod
    def ensure_list(cls, v: object) -> list:
        """Coerce null → empty list to avoid downstream None checks."""
        if v is None:
            return []
        return v

    @field_validator("sources", mode="before")
    @classmethod
    def ensure_sources_list(cls, v: object) -> list:
        if v is None:
            return []
        return v

    def is_high_risk(self) -> bool:
        """
        Returns True if this output should trigger the escalation branch.
        Per 02_System_Architecture.md Section 4.5:
        'either one triggers escalation, never requiring both'
        — so this is an OR of the LLM flag and the keyword layer result,
        but the keyword layer check is performed in the orchestrator separately.
        This method covers only the LLM-assessed layer.
        """
        return self.escalation_recommended

    def model_post_init(self, __context: object) -> None:
        """Post-init validation: trust_check intents should have verdicts."""
        # We can't enforce this here without knowing the intent — the orchestrator
        # is responsible for asserting verdict is non-null when intent == trust_check.
        pass


# ── Canned fallback response ──────────────────────────────────────────────────
# Used when Core Engine validation fails twice (retry exhausted).
# Per 02_System_Architecture.md Section 4.4: "fall back to a safe canned response
# rather than passing malformed content downstream."
FALLBACK_CORE_OUTPUT = CoreEngineOutput(
    core_message=(
        "I ran into a problem understanding that. Your financial situation matters — "
        "please try again, or speak to someone you trust about this directly."
    ),
    next_action="Send the message again, or call a trusted family member or NGO helpline.",
    verdict=None,
    risk_signals_detected=[],
    escalation_recommended=False,
    sources=[],
)
