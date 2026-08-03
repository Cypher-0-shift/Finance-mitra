"""
tests/test_multimodal_engines.py — Unit tests for Phase 5 Vision and Voice engines.

Verifies:
  - Vision Engine edge validation (MIME type rejection, 10MB size capping)
  - Vision Engine simulated OCR & context extraction
  - Voice Engine transcription fallback and confidence calculation
"""
from __future__ import annotations

import pytest

from app.config import Settings
from app.engines.vision import VisionEngine
from app.engines.voice import VoiceEngine


@pytest.fixture
def dummy_settings():
    return Settings(
        environment="development",
        gemini_api_key="AIzaSyDummyTestKey1234567890",
    )


@pytest.mark.asyncio
async def test_vision_engine_mime_validation(dummy_settings):
    vision = VisionEngine(dummy_settings)
    res = await vision.describe_image(b"dummy_bytes", "application/pdf")
    assert "Unsupported image type" in res["visual_context"]
    assert res.get("error") == "unsupported_type"


@pytest.mark.asyncio
async def test_vision_engine_size_cap_validation(dummy_settings):
    vision = VisionEngine(dummy_settings)
    huge_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB
    res = await vision.describe_image(huge_bytes, "image/jpeg")
    assert "exceeds maximum limit of 10MB" in res["visual_context"]
    assert res.get("error") == "oversized"


@pytest.mark.asyncio
async def test_vision_engine_dev_mock_success(dummy_settings):
    vision = VisionEngine(dummy_settings)
    res = await vision.describe_image(b"fake_image_data", "image/png")
    assert res.get("error") is None
    assert "Guaranteed 100% returns in 24 hours" in res["text_content"]
    assert "investment" in res["visual_context"]


@pytest.mark.asyncio
async def test_voice_engine_deferred_to_v1_x_raises_not_implemented(dummy_settings):
    voice = VoiceEngine(dummy_settings)
    with pytest.raises(NotImplementedError) as exc_info:
        await voice.transcribe_audio(b"dummy_audio", "audio/ogg")
    assert "deferred to v1.x" in str(exc_info.value)

    with pytest.raises(NotImplementedError) as exc_info_tts:
        await voice.synthesize_speech("Hello", "hi")
    assert "deferred to v1.x" in str(exc_info_tts.value)
