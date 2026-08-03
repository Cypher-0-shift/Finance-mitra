"""
app/security/signature.py — WhatsApp webhook HMAC-SHA256 signature verification.

This is a Phase 0 / Phase 1 requirement per:
  - FR-11: all inbound webhook requests are cryptographically verified before processing.
  - 02_System_Architecture.md Section 9.1
  - 03_Security_Compliance.md Section 5.1
  - Pilot launch checklist item 1

CRITICAL: This verification MUST run before any processing of the webhook payload.
An invalid or missing signature means the request is rejected entirely — no partial
processing, no logging of payload content.

The verification uses the raw request body bytes (not the parsed JSON) and the
X-Hub-Signature-256 header provided by Meta.

Reference: https://developers.facebook.com/docs/graph-api/webhooks/getting-started#verification-requests
"""
from __future__ import annotations

import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_webhook_signature(
    payload_bytes: bytes,
    signature_header: str | None,
    app_secret: str,
) -> bool:
    """
    Verify the X-Hub-Signature-256 header from a Meta WhatsApp webhook request.

    Args:
        payload_bytes: The raw request body as bytes (read before JSON parsing).
        signature_header: The value of the X-Hub-Signature-256 header.
            Expected format: 'sha256=<hex_digest>'
        app_secret: The WhatsApp App Secret from the Meta App Dashboard.
            Must come from settings, never hardcoded.

    Returns:
        True if the signature is valid, False otherwise.

    Raises:
        Nothing — all error cases return False so the caller can reject cleanly.
    """
    if not signature_header:
        logger.warning(
            "webhook_signature_missing",
            extra={"event": "sig_check_rejected", "reason": "no_header"},
        )
        return False

    if not signature_header.startswith("sha256="):
        logger.warning(
            "webhook_signature_malformed",
            extra={"event": "sig_check_rejected", "reason": "bad_prefix"},
        )
        return False

    received_digest = signature_header[len("sha256="):]

    # Compute expected HMAC-SHA256 digest
    expected_digest = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(received_digest, expected_digest)

    if not is_valid:
        logger.warning(
            "webhook_signature_invalid",
            extra={"event": "sig_check_rejected", "reason": "digest_mismatch"},
        )

    return is_valid
