"""
tests/test_core_schema.py — Tests for the Core Engine Pydantic output schema.

This is one of the two test suites called out as high-consequence in the spec:
"Write tests for the structured-output schema validation and the risk/distress
gate specifically — these are the two places a silent bug has the highest
real-world consequence."

A schema validation bug means malformed LLM output flows downstream to the user —
a corrupted trust verdict or missing next_action is a real safety failure.

Tests cover:
  - Valid schema objects pass validation
  - Invalid/missing required fields are caught
  - TrustVerdict enum normalisation works correctly
  - Null-coercion for list fields (risk_signals_detected, sources) works
  - FALLBACK_CORE_OUTPUT is itself valid (it must always be safe to use)
  - is_high_risk() returns correct values

All tests run without any live credentials.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.core_engine import (
    FALLBACK_CORE_OUTPUT,
    CoreEngineOutput,
    SourceCitation,
    TrustVerdict,
)


class TestCoreEngineOutputSchema:
    """Tests for CoreEngineOutput Pydantic model."""

    def _valid_payload(self) -> dict:
        return {
            "core_message": "The user received ₹5000 after a construction job.",
            "next_action": "Put ₹1000 in a post office recurring deposit today.",
            "verdict": None,
            "risk_signals_detected": [],
            "escalation_recommended": False,
            "sources": [],
        }

    def test_valid_full_object_passes(self):
        output = CoreEngineOutput(**self._valid_payload())
        assert output.core_message
        assert output.next_action
        assert output.verdict is None
        assert output.escalation_recommended is False

    def test_trust_check_verdict_safe_ish(self):
        payload = self._valid_payload()
        payload.update({"verdict": "safe_ish"})
        output = CoreEngineOutput(**payload)
        assert output.verdict == TrustVerdict.SAFE_ISH

    def test_trust_check_verdict_be_careful(self):
        payload = self._valid_payload()
        payload.update({"verdict": "be_careful"})
        output = CoreEngineOutput(**payload)
        assert output.verdict == TrustVerdict.BE_CAREFUL

    def test_trust_check_verdict_avoid(self):
        payload = self._valid_payload()
        payload.update({"verdict": "avoid"})
        output = CoreEngineOutput(**payload)
        assert output.verdict == TrustVerdict.AVOID

    def test_verdict_normalised_to_lowercase(self):
        """The validator should normalise 'AVOID' → 'avoid' before Enum lookup."""
        payload = self._valid_payload()
        payload["verdict"] = "AVOID"
        output = CoreEngineOutput(**payload)
        assert output.verdict == TrustVerdict.AVOID

    def test_invalid_verdict_raises(self):
        payload = self._valid_payload()
        payload["verdict"] = "definitely_safe"
        with pytest.raises(ValidationError):
            CoreEngineOutput(**payload)

    def test_missing_core_message_raises(self):
        payload = self._valid_payload()
        del payload["core_message"]
        with pytest.raises(ValidationError):
            CoreEngineOutput(**payload)

    def test_empty_core_message_raises(self):
        payload = self._valid_payload()
        payload["core_message"] = ""
        with pytest.raises(ValidationError):
            CoreEngineOutput(**payload)

    def test_missing_next_action_raises(self):
        payload = self._valid_payload()
        del payload["next_action"]
        with pytest.raises(ValidationError):
            CoreEngineOutput(**payload)

    def test_missing_escalation_recommended_raises(self):
        payload = self._valid_payload()
        del payload["escalation_recommended"]
        with pytest.raises(ValidationError):
            CoreEngineOutput(**payload)

    def test_null_risk_signals_coerced_to_empty_list(self):
        """LLMs sometimes return null instead of []. Must be coerced."""
        payload = self._valid_payload()
        payload["risk_signals_detected"] = None
        output = CoreEngineOutput(**payload)
        assert output.risk_signals_detected == []

    def test_null_sources_coerced_to_empty_list(self):
        payload = self._valid_payload()
        payload["sources"] = None
        output = CoreEngineOutput(**payload)
        assert output.sources == []

    def test_sources_populated_correctly(self):
        payload = self._valid_payload()
        payload["sources"] = [
            {"name": "RBI Annual Report on Financial Inclusion", "pattern": "upfront fee scam"}
        ]
        output = CoreEngineOutput(**payload)
        assert len(output.sources) == 1
        assert output.sources[0].name == "RBI Annual Report on Financial Inclusion"
        assert output.sources[0].pattern == "upfront fee scam"

    def test_source_citation_missing_name_raises(self):
        with pytest.raises(ValidationError):
            SourceCitation(name="", pattern="some pattern")

    def test_risk_signals_with_content(self):
        payload = self._valid_payload()
        payload["risk_signals_detected"] = ["guaranteed_high_returns", "upfront_fee_demanded"]
        output = CoreEngineOutput(**payload)
        assert len(output.risk_signals_detected) == 2

    def test_escalation_recommended_true_is_high_risk(self):
        payload = self._valid_payload()
        payload["escalation_recommended"] = True
        output = CoreEngineOutput(**payload)
        assert output.is_high_risk() is True

    def test_escalation_recommended_false_is_not_high_risk(self):
        payload = self._valid_payload()
        payload["escalation_recommended"] = False
        output = CoreEngineOutput(**payload)
        assert output.is_high_risk() is False

    def test_fallback_output_is_valid(self):
        """
        FALLBACK_CORE_OUTPUT must always be valid — it's used as the safe response
        when the LLM fails twice. If it's invalid, the fallback itself fails.
        """
        # Pydantic already validated it at import time; this re-asserts explicitly.
        assert FALLBACK_CORE_OUTPUT.core_message
        assert FALLBACK_CORE_OUTPUT.next_action
        assert FALLBACK_CORE_OUTPUT.verdict is None
        assert FALLBACK_CORE_OUTPUT.escalation_recommended is False
        assert FALLBACK_CORE_OUTPUT.risk_signals_detected == []
        assert FALLBACK_CORE_OUTPUT.sources == []

    def test_full_trust_check_response(self):
        """A complete trust_check response with all fields populated."""
        payload = {
            "core_message": (
                "This offer shows multiple high-risk scam signals: guaranteed 40% returns, "
                "upfront registration fee, and pressure to recruit others."
            ),
            "next_action": "Do not pay the registration fee. Report the scheme to the RBI helpline at 14440.",
            "verdict": "avoid",
            "risk_signals_detected": [
                "guaranteed_high_returns",
                "upfront_fee_demanded",
                "recruit_others_for_payment",
            ],
            "escalation_recommended": True,
            "sources": [
                {"name": "RBI Annual Report on Financial Inclusion", "pattern": "pyramid scheme"},
                {"name": "NGO practitioner input", "pattern": "upfront fee scam"},
            ],
        }
        output = CoreEngineOutput(**payload)
        assert output.verdict == TrustVerdict.AVOID
        assert output.is_high_risk() is True
        assert len(output.risk_signals_detected) == 3
        assert len(output.sources) == 2
