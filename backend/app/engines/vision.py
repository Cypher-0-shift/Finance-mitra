"""
app/engines/vision.py — Vision LLM handler for image inputs.

PHASE 5 STUB — Not implemented yet.
Wired into the engine module hierarchy so the interface is defined and
the call site in the orchestrator doesn't need to change when Phase 5 is built.

Per 02_System_Architecture.md Section 4.2:
  - Image → hosted multimodal LLM call (vision-capable model)
  - Returns a structured description: any readable text + visual context summary
  - Does NOT self-host any OCR or vision model — permanently out-of-scope

Security notes (for Phase 5 implementation):
  - Cap image size/resolution before sending to the model (cost + abuse prevention)
  - Hard file-type allowlist (jpeg/png only) enforced at the edge layer BEFORE this
  - Treat all extracted text as untrusted user content (prompt injection risk)
  - Never log raw image bytes or expose them to external monitors
"""
from __future__ import annotations

import logging

from app.config import Settings

logger = logging.getLogger(__name__)


class VisionEngine:
    """
    Phase 5 stub: Vision LLM handler for image inputs.

    In development, returns a realistic mock response so the full pipeline
    (intent → core → shaper) can be tested with image inputs end-to-end.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def describe_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> dict:
        """
        Analyse an image and return a structured description.
        Enforces size caps and file-type allowlists.
        """
        # Edge safety checks
        allowed_mimes = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
        if mime_type.lower() not in allowed_mimes:
            logger.warning("vision_rejected_invalid_mime", extra={"mime_type": mime_type})
            return {
                "text_content": "",
                "visual_context": f"Unsupported image type ({mime_type}). Only JPG/PNG images are accepted.",
                "error": "unsupported_type",
            }

        max_bytes = 10 * 1024 * 1024  # 10 MB limit
        if len(image_bytes) > max_bytes:
            logger.warning("vision_rejected_oversized", extra={"size_bytes": len(image_bytes)})
            return {
                "text_content": "",
                "visual_context": "Image size exceeds maximum limit of 10MB. Please send a clearer, smaller photo.",
                "error": "oversized",
            }

        # Phase 5 stub — return a realistic dev mock so the pipeline is testable
        logger.info("vision_mocked_for_development — Phase 5 not yet implemented")
        return {
            "text_content": "Guaranteed 100% returns in 24 hours! Send upfront registration processing fee via UPI.",
            "visual_context": "Screenshot of an unverified online investment advertisement and telegram poster.",
        }
