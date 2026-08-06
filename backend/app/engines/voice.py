"""
app/engines/voice.py — Voice Engine (STT / TTS) stub.

Note: Voice functionality (Phase 5 STT/TTS via Bhashini) has been deferred from v1 MVP scope to v1.x.
MVP supports text and image input only, with text-only responses.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.config import Settings

logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Stub for Voice Engine (STT / TTS), deferred to v1.x release.
    Any call to transcribe or synthesize will raise NotImplementedError in MVP scope.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        mime_type: str,
        http_client: Optional[object] = None,
    ) -> dict:
        """
        Deferred to v1.x. Raises NotImplementedError.
        """
        raise NotImplementedError("Voice input (STT) is deferred to v1.x. MVP supports text and image inputs only.")

    async def synthesize_speech(
        self,
        text: str,
        language: str = "hi",
        http_client: Optional[object] = None,
    ) -> Optional[str]:
        """
        Deferred to v1.x. Raises NotImplementedError.
        """
        raise NotImplementedError("Voice output (TTS) is deferred to v1.x. MVP supports text outputs only.")
