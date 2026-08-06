"""
app/services/whatsapp.py — Meta WhatsApp Cloud API outbound client.

Handles sending messages back to users via the Meta Graph API.
Per 02_System_Architecture.md Section 6.2.

Security:
  - Access token comes from settings (environment variable), never hardcoded.
  - Phone numbers are not logged — only the message ID from the response is.

Reliability:
  - On API failure: log the error and return None (don't raise to the caller).
    The background task that calls this should handle the None case and can
    retry or queue for later per the reliability spec (Arch §8).
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"


class WhatsAppClient:
    """
    Thin async client for the Meta WhatsApp Cloud API outbound send endpoint.

    Instantiated once and reused (httpx.AsyncClient for connection pooling).
    """

    def __init__(self, settings: Settings) -> None:
        self._phone_number_id = settings.whatsapp_phone_number_id
        self._api_version = settings.whatsapp_api_version
        self._headers = {
            "Authorization": f"Bearer {settings.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self._base_url = (
            f"{GRAPH_API_BASE}/{settings.whatsapp_api_version}"
            f"/{settings.whatsapp_phone_number_id}/messages"
        )

    async def send_text(
        self,
        to: str,
        text: str,
        http_client: httpx.AsyncClient,
    ) -> Optional[str]:
        """
        Send a text message to a WhatsApp user.

        Args:
            to: Recipient's WhatsApp phone number (e.g. '919876543210').
            text: Message body. Plain text only at this stage.
            http_client: Shared httpx AsyncClient (from app lifespan).

        Returns:
            The WhatsApp message ID from the API response, or None on failure.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text, "preview_url": False},
        }

        try:
            response = await http_client.post(
                self._base_url,
                json=payload,
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            logger.info("whatsapp_message_sent", extra={"message_id": message_id})
            return message_id

        except httpx.HTTPStatusError as e:
            logger.error(
                "whatsapp_send_failed",
                extra={
                    "status_code": e.response.status_code,
                    "error": e.response.text[:200],  # Truncate — may contain sensitive data
                },
            )
            return None

        except httpx.RequestError as e:
            logger.error(
                "whatsapp_send_network_error",
                extra={"error": str(e)},
            )
            return None

    async def send_audio(
        self,
        to: str,
        audio_url: str,
        http_client: httpx.AsyncClient,
    ) -> Optional[str]:
        """
        Send an audio message (voice note) to a WhatsApp user.
        Used for voice output modality (Phase 5 — FR-6).

        Args:
            to: Recipient phone number.
            audio_url: URL of the pre-uploaded audio file.
            http_client: Shared httpx AsyncClient.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "audio",
            "audio": {"link": audio_url},
        }

        try:
            response = await http_client.post(
                self._base_url,
                json=payload,
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            message_id = data.get("messages", [{}])[0].get("id")
            logger.info("whatsapp_audio_sent", extra={"message_id": message_id})
            return message_id

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.error("whatsapp_audio_send_failed", extra={"error": str(e)})
            return None

    async def download_media(
        self,
        media_id: str,
        http_client: httpx.AsyncClient,
    ) -> tuple[bytes, str] | None:
        """
        Download binary media file from Meta WhatsApp Cloud API using a media ID.
        Used in Phase 5 for retrieving incoming user voice notes and image attachments.

        Args:
            media_id: Media asset UUID provided in inbound webhook payload.
            http_client: Shared httpx AsyncClient instance.

        Returns:
            Tuple of (raw_binary_bytes, mime_type_string) or None upon failure.
        """
        url = f"{GRAPH_API_BASE}/{self._api_version}/{media_id}"
        try:
            # 1. Fetch media download link metadata from Graph API
            response = await http_client.get(url, headers=self._headers, timeout=10.0)
            response.raise_for_status()
            media_info = response.json()
            download_url = media_info.get("url")
            mime_type = media_info.get("mime_type", "application/octet-stream")
            if not download_url:
                logger.error("whatsapp_media_download_failed_no_url", extra={"media_id": media_id})
                return None

            # 2. Download raw binary file bytes
            bin_response = await http_client.get(download_url, headers=self._headers, timeout=20.0)
            bin_response.raise_for_status()
            logger.info(
                "whatsapp_media_downloaded",
                extra={"media_id": media_id, "mime_type": mime_type, "size_bytes": len(bin_response.content)},
            )
            return (bin_response.content, mime_type)
        except Exception as e:
            logger.error("whatsapp_media_download_error", extra={"media_id": media_id, "error": str(e)})
            return None
