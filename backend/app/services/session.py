"""
app/services/session.py — Conversation and session persistence.

Manages loading/creating user sessions and conversations from Supabase.

User identity: WhatsApp phone numbers are NEVER stored in plaintext.
They are hashed with HMAC-SHA256 using the WHATSAPP_ID_HASH_SALT secret.
The salt lives in the secrets manager (never in the DB).
See 03_Security_Compliance.md Section 4.4 and 02_System_Architecture.md Section 5.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional
from uuid import UUID

from supabase import AsyncClient

logger = logging.getLogger(__name__)


def hash_whatsapp_id(phone_number: str, salt: str) -> str:
    """
    Hash a raw WhatsApp phone number with HMAC-SHA256 using the server-side salt.

    The salt is never stored in the DB — it lives in WHATSAPP_ID_HASH_SALT.
    Without the salt, the hash is only nominally irreversible.

    Args:
        phone_number: Raw WhatsApp phone number (e.g. '919876543210').
        salt: Server-side secret from settings.whatsapp_id_hash_salt.

    Returns:
        Hex-encoded HMAC-SHA256 digest used as the whatsapp_id_hash.
    """
    return hmac.new(
        key=salt.encode("utf-8"),
        msg=phone_number.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


async def get_or_create_user(
    db: AsyncClient,
    phone_number: str,
    hash_salt: str,
) -> dict:
    """
    Look up a user by their hashed WhatsApp ID, creating them if not found.
    The raw phone number is used only to compute the hash — it is not stored.

    Returns the full users row as a dict.
    """
    id_hash = hash_whatsapp_id(phone_number, hash_salt)

    response = (
        await db.table("users")
        .select("*")
        .eq("whatsapp_id_hash", id_hash)
        .limit(1)
        .execute()
    )

    if response and response.data:
        user = response.data[0]
        # Update last_active_at
        try:
            await (
                db.table("users")
                .update({"last_active_at": "now()"})
                .eq("whatsapp_id_hash", id_hash)
                .execute()
            )
        except Exception as e:
            logger.warning("failed_to_update_last_active_at", extra={"error": str(e)})
        return user

    # Create new user — store hash only, never raw phone number
    create_response = (
        await db.table("users")
        .insert({"whatsapp_id_hash": id_hash, "preferred_language": "hi"})
        .execute()
    )

    logger.info("user_created", extra={"id_hash_prefix": id_hash[:8]})
    return create_response.data[0]


async def get_or_create_conversation(
    db: AsyncClient,
    user_id: UUID,
    intent: Optional[str] = None,
) -> dict:
    """
    Get the most recent open conversation for a user, or create a new one.
    A new conversation is created when there's no open one, or when the
    most recent conversation is resolved/escalated.

    Returns the conversations row as a dict.
    """
    response = (
        await db.table("conversations")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("status", "open")
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        conversation = response.data[0]
        # Update intent if it's been classified now
        if intent and not conversation.get("intent"):
            await (
                db.table("conversations")
                .update({"intent": intent})
                .eq("id", conversation["id"])
                .execute()
            )
            conversation["intent"] = intent
        return conversation

    # Create new conversation
    create_response = (
        await db.table("conversations")
        .insert({"user_id": str(user_id), "intent": intent, "status": "open"})
        .execute()
    )

    logger.info(
        "conversation_created",
        extra={"user_id": str(user_id), "intent": intent},
    )
    return create_response.data[0]


async def save_message(
    db: AsyncClient,
    conversation_id: UUID,
    sender: str,
    input_type: str,
    message_text: Optional[str] = None,
    media_ref: Optional[str] = None,
    core_engine_output: Optional[dict] = None,
    shaped_response: Optional[dict] = None,
) -> dict:
    """
    Persist a message to the messages table.

    SCHEMA NOTE: core_engine_output and shaped_response are stored as SEPARATE
    JSONB columns — never collapsed into one. This is a spec requirement per
    02_System_Architecture.md Sections 4.4, 4.7, and 5.
    """
    row: dict = {
        "conversation_id": str(conversation_id),
        "sender": sender,
        "input_type": input_type,
    }
    if message_text is not None:
        row["message_text"] = message_text
    if media_ref is not None:
        row["media_ref"] = media_ref          # Pointer to transient storage, NOT the media itself
    if core_engine_output is not None:
        row["core_engine_output"] = core_engine_output
    if shaped_response is not None:
        row["shaped_response"] = shaped_response

    response = await db.table("messages").insert(row).execute()
    return response.data[0]
