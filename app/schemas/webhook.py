"""
app/schemas/webhook.py — Pydantic models for inbound Meta WhatsApp webhook payloads.

These models cover the standard WhatsApp Cloud API webhook structure.
See: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples

Design note: we model only the fields we use — extra fields are ignored via
model_config extra='ignore'. This is intentional: Meta adds fields over time and
we should not break on unknown fields.

SECURITY: These models are used AFTER signature verification, not before.
The signature check in app/security/signature.py runs on the raw bytes before
Pydantic ever sees the payload. Never deserialise an unverified payload.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    body: str

    model_config = {"extra": "ignore"}


class AudioContent(BaseModel):
    id: str                         # Media object ID — used to download via Graph API
    mime_type: str = ""

    model_config = {"extra": "ignore"}


class ImageContent(BaseModel):
    id: str                         # Media object ID
    mime_type: str = ""
    sha256: str = ""                # Integrity check for downloaded media

    model_config = {"extra": "ignore"}


class InboundMessage(BaseModel):
    """A single message object from Meta's webhook payload."""
    id: str                         # Unique message ID from Meta
    from_: str = Field(alias="from", description="Sender's WhatsApp phone number (raw)")
    timestamp: str
    type: str                       # 'text' | 'audio' | 'image' | ...

    text: Optional[TextContent] = None
    audio: Optional[AudioContent] = None
    image: Optional[ImageContent] = None

    model_config = {"extra": "ignore", "populate_by_name": True}

    @property
    def input_type(self) -> str:
        """Normalise Meta's 'audio' type to internal 'voice' label."""
        if self.type == "audio":
            return "voice"
        if self.type in ("text", "image"):
            return self.type
        return "unknown"


class Contact(BaseModel):
    wa_id: str
    profile: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}


class Value(BaseModel):
    messaging_product: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    contacts: list[Contact] = Field(default_factory=list)
    messages: list[InboundMessage] = Field(default_factory=list)
    statuses: list[dict[str, Any]] = Field(default_factory=list)  # delivery receipts etc.

    model_config = {"extra": "ignore"}


class Change(BaseModel):
    value: Value
    field: str

    model_config = {"extra": "ignore"}


class Entry(BaseModel):
    id: str
    changes: list[Change]

    model_config = {"extra": "ignore"}


class WhatsAppWebhookPayload(BaseModel):
    """Top-level webhook payload from Meta."""
    object: str                     # Should be 'whatsapp_business_account'
    entry: list[Entry]

    model_config = {"extra": "ignore"}

    def get_messages(self) -> list[InboundMessage]:
        """Flatten all messages across all entries and changes."""
        messages: list[InboundMessage] = []
        for entry in self.entry:
            for change in entry.changes:
                messages.extend(change.value.messages)
        return messages
