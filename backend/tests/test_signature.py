"""
tests/test_signature.py — Tests for webhook HMAC-SHA256 signature verification.

This is one of the two test suites called out as high-consequence in the spec:
"Write tests for the structured-output schema validation and the risk/distress
gate specifically — these are the two places a silent bug has the highest
real-world consequence."

A bug in signature verification means unverified requests can reach application
code — the most fundamental webhook security control (FR-11).

All tests run without any live credentials — pure logic tests.
"""
from __future__ import annotations

import hashlib
import hmac

import pytest

from app.security.signature import verify_webhook_signature

APP_SECRET = "test_secret_abc123"


def _make_valid_signature(payload: bytes, secret: str = APP_SECRET) -> str:
    """Helper: compute the correct X-Hub-Signature-256 for a payload."""
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


class TestVerifyWebhookSignature:
    """Tests for verify_webhook_signature()."""

    def test_valid_signature_returns_true(self):
        payload = b'{"object":"whatsapp_business_account","entry":[]}'
        sig = _make_valid_signature(payload)
        assert verify_webhook_signature(payload, sig, APP_SECRET) is True

    def test_wrong_secret_returns_false(self):
        payload = b'{"test": "data"}'
        sig = _make_valid_signature(payload, secret="correct_secret")
        result = verify_webhook_signature(payload, sig, "wrong_secret")
        assert result is False

    def test_tampered_payload_returns_false(self):
        original = b'{"amount": "1000"}'
        sig = _make_valid_signature(original)
        tampered = b'{"amount": "9999"}'
        assert verify_webhook_signature(tampered, sig, APP_SECRET) is False

    def test_missing_signature_header_returns_false(self):
        payload = b'{"test": "data"}'
        assert verify_webhook_signature(payload, None, APP_SECRET) is False

    def test_empty_signature_header_returns_false(self):
        payload = b'{"test": "data"}'
        assert verify_webhook_signature(payload, "", APP_SECRET) is False

    def test_missing_sha256_prefix_returns_false(self):
        payload = b'{"test": "data"}'
        # Provide a valid hex digest but without the required 'sha256=' prefix
        raw_digest = hmac.new(
            key=APP_SECRET.encode(), msg=payload, digestmod=hashlib.sha256
        ).hexdigest()
        assert verify_webhook_signature(payload, raw_digest, APP_SECRET) is False

    def test_wrong_prefix_returns_false(self):
        payload = b'{"test": "data"}'
        digest = _make_valid_signature(payload)
        bad_prefix = digest.replace("sha256=", "md5=")
        assert verify_webhook_signature(payload, bad_prefix, APP_SECRET) is False

    def test_empty_payload_valid_signature(self):
        """Empty body with valid signature should still pass — edge case."""
        payload = b""
        sig = _make_valid_signature(payload)
        assert verify_webhook_signature(payload, sig, APP_SECRET) is True

    def test_unicode_payload_valid_signature(self):
        """Non-ASCII content (e.g. Hindi text in JSON) must verify correctly."""
        payload = "{'message': 'मुझे पैसे मिले'}".encode("utf-8")
        sig = _make_valid_signature(payload)
        assert verify_webhook_signature(payload, sig, APP_SECRET) is True

    def test_timing_safe_comparison(self):
        """
        Verify that hmac.compare_digest is used (timing-safe).
        We can't directly test timing, but we can verify that two signatures
        of different lengths don't crash and return False correctly.
        """
        payload = b'{"test": "timing"}'
        short_sig = "sha256=abc123"  # Too short to be a real SHA-256 digest
        assert verify_webhook_signature(payload, short_sig, APP_SECRET) is False
