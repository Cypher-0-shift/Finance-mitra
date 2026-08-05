"""
app/routers/dev.py — Development-only testing endpoint for Financial Mitra.

Provides POST /dev/chat to exercise the full AI conversational pipeline locally
without requiring Meta/WhatsApp Graph API connectivity. Reuses real session
persistence, Intent Router, RAG Scam Retrieval, Core Reasoning Engine, Risk/Distress Gate,
and Language & Trust Shaper.

Hard Security Gate: Only included in route table when ENVIRONMENT == "development".
"""
from __future__ import annotations

import base64
import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.client import get_db
from app.routers.webhook import _build_phase1_reply
from app.services.analytics import log_financial_action
from app.services.escalation import create_escalation
from app.services.rag import retrieve_scam_context
from app.services.rate_limit import check_and_record_usage
from app.services.risk_gate import escalation_reason, should_escalate
from app.services.session import get_or_create_conversation, get_or_create_user, save_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dev", tags=["development"])


class DevChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique synthetic session ID to maintain continuous conversations across turns")
    message: str = Field(..., description="Message text or description of query")
    input_type: Literal["text", "image"] = "text"
    media_base64: Optional[str] = None
    language: Literal["hi", "en"] = "hi"


class DevChatResponse(BaseModel):
    reply_text: str
    input_type_replied: str
    verdict: Optional[str] = None
    escalation_recommended: bool
    next_action: str


@router.post("/chat", response_model=DevChatResponse)
async def dev_chat(request: DevChatRequest) -> DevChatResponse:
    """
    Execute full multi-turn conversational reasoning pipeline for developer debugging and demoing.
    Bypasses Meta webhook signature check and Graph API outbound transmission.
    """
    from app.main import (
        get_core_engine,
        get_http_client,
        get_intent_router,
        get_shaper,
        get_vision_engine,
    )

    settings = get_settings()
    db = get_db()

    # ── 1. Session Management (Synthetic WhatsApp ID) ────────────────────────
    synthetic_phone = f"dev_user_{request.session_id}"
    user = await get_or_create_user(db, synthetic_phone, settings.whatsapp_id_hash_salt)
    conversation = await get_or_create_conversation(db, str(user["id"]))

    # ── 2. Rate Limiting & Daily Cost Cap Check ──────────────────────────────
    is_allowed, throttle_msg = await check_and_record_usage(db, str(user["id"]), settings)
    if not is_allowed and throttle_msg:
        await save_message(
            db,
            conversation_id=conversation["id"],
            sender="system",
            input_type="text",
            message_text=throttle_msg,
        )
        return DevChatResponse(
            reply_text=throttle_msg,
            input_type_replied="text",
            verdict=None,
            escalation_recommended=False,
            next_action="Rate limit or cost cap reached. Try again after reset window.",
        )

    user_text = ""
    http_client = get_http_client()

    # ── 3. Multimodal Input Processing ───────────────────────────────────────
    if request.input_type == "text":
        user_text = request.message.strip()
        await save_message(
            db,
            conversation_id=conversation["id"],
            sender="user",
            input_type="text",
            message_text=user_text,
        )

    elif request.input_type == "image":
        vision_engine = get_vision_engine()
        if request.media_base64 and vision_engine:
            try:
                raw_bytes = base64.b64decode(request.media_base64)
                vis_result = await vision_engine.describe_image(raw_bytes, "image/jpeg")
                if vis_result.get("error"):
                    reply_text = vis_result.get(
                        "visual_context",
                        "I received your photo but had difficulty analyzing it. Please send as text.",
                    )
                    await save_message(
                        db,
                        conversation_id=conversation["id"],
                        sender="user",
                        input_type="image",
                        message_text="[image attachment — invalid]",
                    )
                    await save_message(
                        db,
                        conversation_id=conversation["id"],
                        sender="system",
                        input_type="text",
                        message_text=reply_text,
                    )
                    return DevChatResponse(
                        reply_text=reply_text,
                        input_type_replied="text",
                        verdict=None,
                        escalation_recommended=False,
                        next_action="Submit query as text description.",
                    )
                ocr_part = vis_result.get("text_content", "")
                vis_part = vis_result.get("visual_context", "")
                user_text = f"User submitted an image. Extracted OCR text: '{ocr_part}'. Visual Context: '{vis_part}'".strip()
            except Exception as e:
                logger.error("dev_chat_image_decode_error", extra={"error": str(e)})
                user_text = request.message or "User submitted an image. Extracted OCR text: 'Guaranteed 100% returns in 24 hours via UPI!'. Visual Context: 'Unverified Telegram scheme banner.'"
        else:
            user_text = request.message or "User submitted an image. Extracted OCR text: 'Guaranteed 100% returns in 24 hours via UPI!'. Visual Context: 'Unverified Telegram scheme banner.'"

        await save_message(
            db,
            conversation_id=conversation["id"],
            sender="user",
            input_type="image",
            message_text=user_text or "[image attachment]",
        )

    # ── 4. Core AI Pipeline (Intent Router -> RAG -> Core Engine -> Shaper) ──
    intent_router = get_intent_router()
    core_engine = get_core_engine()
    shaper = get_shaper()

    verdict_val = None
    escalation_val = False
    next_action_val = "Continue financial companion guidance."
    core_out_dict = None
    shaped_out_dict = None
    reply_text = ""

    if user_text and intent_router and core_engine and shaper and settings.groq_api_key:
        try:
            # a) Intent Classification
            intent_str = await intent_router.classify(user_text)
            if conversation.get("status") == "open":
                try:
                    await (
                        db.table("conversations")
                        .update({"intent": intent_str})
                        .eq("id", str(conversation["id"]))
                        .execute()
                    )
                except Exception as e:
                    logger.error("failed_to_update_conversation_intent", extra={"error": str(e)})

            # b) RAG Scam Context Retrieval
            rag_context = None
            if intent_str == "trust_check" or any(w in user_text.lower() for w in ["scam", "fraud", "dhokha", "fake", "scheme", "chit", "invest"]):
                rag_context = await retrieve_scam_context(db, user_text, settings)

            # c) Core Engine Reasoning
            core_out = await core_engine.reason(user_text, intent_str, rag_context=rag_context)
            core_out_dict = core_out.model_dump()

            verdict_val = core_out.verdict
            escalation_val = bool(core_out.escalation_recommended)
            next_action_val = core_out.next_action

            # d) North Star Metric Logging
            verdict_str = str(core_out.verdict or "").lower()
            if "avoid" in verdict_str or "scam" in verdict_str:
                await log_financial_action(db, str(user["id"]), "scam_avoided", str(conversation["id"]))
            elif any(w in str(core_out.next_action).lower() for w in ["save", "deposit", "fd", "scheme", "invest", "post office"]):
                await log_financial_action(db, str(user["id"]), "savings_started", str(conversation["id"]))

            # e) Risk / Distress Gate & Escalation
            if should_escalate(user_text, core_out):
                esc_reason = escalation_reason(user_text, core_out)
                await create_escalation(
                    db,
                    conversation_id=str(conversation["id"]),
                    reason=esc_reason,
                    risk_signals=core_out.risk_signals_detected,
                )
                escalation_val = True
                logger.warning(
                    "dev_chat_conversation_escalated",
                    extra={"conversation_id": str(conversation["id"]), "reason": esc_reason},
                )

            # f) Language & Trust Shaper
            user_lang = request.language or "hi"
            reply_text = await shaper.shape(core_out, target_language=user_lang, input_type=request.input_type)
            if user_lang != "en" and next_action_val:
                next_action_val = await shaper.translate_action(next_action_val, target_language=user_lang)
            shaped_out_dict = {"text": reply_text, "language": user_lang, "intent": intent_str}

        except Exception as e:
            logger.error("dev_chat_gemini_pipeline_failed_falling_back", extra={"error": str(e)}, exc_info=True)
            user_lang = request.language or "hi"
            if user_lang == "hi":
                reply_text = "नमस्ते! मैं अभी आपके प्रश्न का उत्तर देने के लिए सर्वर से संपर्क कर रहा हूँ। कृपया किसी भी अनधिकृत निवेश या लोन स्कीम से सावधान रहें और सत्यापित बैंक विकल्पों का ही चयन करें। 🙏"
                next_action_val = "अपने नज़दीकी बैंक या वित्तीय अधिकारी से सलाह लें।"
            else:
                reply_text = "Namaste! I am evaluating your query against verified safety guidelines. Always exercise caution with unfamiliar investment schemes or instant loan apps. 🙏"
                next_action_val = "Verify registration with RBI or SEBI before transferring any funds."
    else:
        user_lang = request.language or "hi"
        if user_lang == "hi":
            reply_text = "नमस्ते! आपका स्वागत है। सुरक्षित भविष्य के लिए बैंक फिक्स्ड डिपॉजिट (FD) और पोस्ट ऑफिस योजनाएं सबसे विश्वसनीय विकल्प हैं। 🙏"
            next_action_val = "अपने नज़दीकी बैंक या डाकघर जाकर ब्याज दरें जांचें।"
        else:
            reply_text = "Namaste! For secure growth and capital safety, Nationalized Bank FDs and Government Post Office schemes are trusted options. 🙏"
            next_action_val = "Visit your nearest banking branch to compare FDs."

    # ── 5. Save Outbound Message ─────────────────────────────────────────────
    await save_message(
        db,
        conversation_id=conversation["id"],
        sender="system",
        input_type="text",
        message_text=reply_text,
        core_engine_output=core_out_dict,
        shaped_response=shaped_out_dict,
    )

    return DevChatResponse(
        reply_text=reply_text,
        input_type_replied="text",
        verdict=verdict_val,
        escalation_recommended=escalation_val,
        next_action=next_action_val,
    )
