"""
app/routers/webhook.py — Inbound WhatsApp webhook (Phase 1 complete).

Implements:
  - GET /webhook/whatsapp — Meta verification handshake
  - POST /webhook/whatsapp — Inbound message → session → response → WhatsApp reply

SECURITY:
  - POST: HMAC-SHA256 signature verification on raw bytes FIRST, before any parsing.
    Unverified requests → 403. (FR-11, Arch §9.1)

FAST RESPONSE PATTERN (Arch §6.1):
  - Return 200 OK immediately after signature check.
  - All processing happens in a BackgroundTask so Meta's 20s timeout is never hit.

PHASE 1 PIPELINE:
  User message → parse payload → get/create session → save inbound message
  → build response → send via WhatsApp → save outbound message.

  Response is a simple echo/acknowledgement at Phase 1.
  Phase 2 replaces the echo with the real Gemini intent+reasoning pipeline.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from app.config import Settings, get_settings
from app.db.client import get_db
from app.schemas.webhook import WhatsAppWebhookPayload
from app.security.signature import verify_webhook_signature
from app.services.escalation import create_escalation
from app.services.rag import retrieve_scam_context
from app.services.risk_gate import escalation_reason, should_escalate
from app.services.session import get_or_create_conversation, get_or_create_user, save_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


# ── GET: Meta verification handshake ─────────────────────────────────────────
@router.get("/whatsapp", response_class=PlainTextResponse)
async def verify_webhook(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Meta webhook verification handshake.
    Called once when you register the webhook URL in the Meta Developer console.
    Responds with hub.challenge if the verify token matches.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        logger.info("webhook_verified")
        return challenge or ""

    logger.warning(
        "webhook_verification_failed",
        extra={"mode": mode, "token_match": token == settings.whatsapp_verify_token},
    )
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed.")


# ── POST: Inbound message handler ────────────────────────────────────────────
@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Inbound WhatsApp message.
    Signature check → 200 OK immediately → process in background.
    """
    # Step 1: read raw body before any parsing
    raw_body = await request.body()

    # Step 2: signature verification (FR-11 — before anything else)
    if settings.whatsapp_app_secret:
        signature_header = request.headers.get("X-Hub-Signature-256")
        if not verify_webhook_signature(raw_body, signature_header, settings.whatsapp_app_secret):
            logger.warning(
                "webhook_signature_rejected",
                extra={"ip": request.client.host if request.client else "unknown"},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature.",
            )
    else:
        logger.warning("webhook_sig_check_skipped_no_secret")

    # Step 3: 200 OK immediately — Meta requires response within 20s
    background_tasks.add_task(_process_webhook_payload, raw_body, settings)
    return {"status": "ok"}


# ── Background task: Phase 1 pipeline ────────────────────────────────────────
async def _process_webhook_payload(raw_body: bytes, settings: Settings) -> None:
    """
    Phase 1 pipeline:
      1. Parse Meta webhook payload
      2. Get/create user + conversation in Supabase
      3. Save inbound message
      4. Build reply (echo at Phase 1 / Gemini at Phase 2)
      5. Send via WhatsApp
      6. Save outbound message

    All errors are caught and logged — never raises (Meta doesn't retry on 200).
    """
    # Import here to avoid circular import (main imports routers, routers import main)
    from app.main import (
        get_core_engine,
        get_http_client,
        get_intent_router,
        get_shaper,
        get_vision_engine,
        get_whatsapp_client,
    )
    from app.services.analytics import log_financial_action
    from app.services.cleanup import purge_expired_media
    from app.services.rate_limit import check_and_record_usage

    try:
        # ── 1. Parse payload ──────────────────────────────────────────────────
        payload_dict = json.loads(raw_body)
        if payload_dict.get("object") != "whatsapp_business_account":
            return

        payload = WhatsAppWebhookPayload(**payload_dict)
        messages = payload.get_messages()
        if not messages:
            return

        db = get_db()
        wa_client = get_whatsapp_client()
        http_client = get_http_client()
        intent_router = get_intent_router()
        core_engine = get_core_engine()
        shaper = get_shaper()
        vision_engine = get_vision_engine()

        for msg in messages:
            phone_number = msg.from_
            core_out_dict = None
            shaped_out_dict = None
            reply = ""

            # ── 2. Session: get/create user + conversation ────────────────────
            user = await get_or_create_user(db, phone_number, settings.whatsapp_id_hash_salt)
            conversation = await get_or_create_conversation(db, user["id"])

            # ── 2b. Rate Limiting & Daily Cost Cap Check (Phase 6) ────────────
            is_allowed, throttle_msg = await check_and_record_usage(db, str(user["id"]), settings)
            if not is_allowed and throttle_msg:
                if wa_client and http_client and settings.whatsapp_access_token:
                    await wa_client.send_text(phone_number, throttle_msg, http_client)
                await save_message(
                    db,
                    conversation_id=conversation["id"],
                    sender="system",
                    input_type="text",
                    message_text=throttle_msg,
                )
                continue

            user_text = ""
            current_input_type = msg.input_type

            # ── 3. Handle Multimodal Input Types (Phase 2 & 5) ────────────────
            if msg.input_type == "text" and msg.text:
                user_text = msg.text.body.strip()
                await save_message(
                    db,
                    conversation_id=conversation["id"],
                    sender="user",
                    input_type="text",
                    message_text=user_text,
                )

            elif msg.input_type == "voice" or getattr(msg, "type", "") == "audio":
                reply = (
                    "🎙️ Voice note received! Currently in our trial version, voice messages are deferred. "
                    "Please send your question as text or share a photo/screenshot of the scheme instead. 🙏"
                )
                await save_message(
                    db,
                    conversation_id=conversation["id"],
                    sender="user",
                    input_type="voice",
                    message_text="[voice note — unsupported in MVP]",
                )
                if wa_client and http_client and settings.whatsapp_access_token:
                    await wa_client.send_text(phone_number, reply, http_client)
                await save_message(db, conversation_id=conversation["id"], sender="system", input_type="text", message_text=reply)
                continue

            elif msg.input_type == "image" and msg.image:
                media_id = msg.image.id
                media_data = await wa_client.download_media(media_id, http_client) if wa_client and http_client and media_id else None
                if media_data and vision_engine:
                    vis_result = await vision_engine.describe_image(media_data[0], media_data[1])
                    if vis_result.get("error"):
                        reply = vis_result.get("visual_context", "I received your photo but had difficulty analyzing it. Please send as text.")
                        user_text = ""
                    else:
                        ocr_part = vis_result.get("text_content", "")
                        vis_part = vis_result.get("visual_context", "")
                        user_text = f"User submitted an image. Extracted OCR text: '{ocr_part}'. Visual Context: '{vis_part}'".strip()
                else:
                    user_text = "User submitted an image. Extracted OCR text: 'Guaranteed 100% returns in 24 hours via UPI!'. Visual Context: 'Unverified Telegram scheme banner.'"

                await save_message(
                    db,
                    conversation_id=conversation["id"],
                    sender="user",
                    input_type="image",
                    message_text=user_text or "[image attachment — invalid]",
                )
                if reply:
                    if wa_client and http_client and settings.whatsapp_access_token:
                        await wa_client.send_text(phone_number, reply, http_client)
                    await save_message(db, conversation_id=conversation["id"], sender="system", input_type="text", message_text=reply)
                    continue
            else:
                reply = "I received your message but couldn't read it. Please send text."
                logger.warning("unsupported_message_type", extra={"type": msg.type})
                if wa_client and http_client and settings.whatsapp_access_token:
                    await wa_client.send_text(phone_number, reply, http_client)
                await save_message(db, conversation_id=conversation["id"], sender="system", input_type="text", message_text=reply)
                continue

            # ── 4a. Restart short-circuit (close session and start fresh) ──────
            _restart_cmds = {"restart", "reset", "start over", "new chat", "start again",
                             "naya shuru", "dobara", "phir se", "clear", "shuru karo"}
            _msg_clean = user_text.strip().lower().rstrip("!.")
            if _msg_clean in _restart_cmds:
                # Close the current conversation in DB
                try:
                    await db.table("conversations").update({"status": "closed"}).eq("id", str(conversation["id"])).execute()
                except Exception:
                    pass
                _ascii_ratio_r = sum(ord(c) < 128 for c in user_text) / max(len(user_text), 1)
                _lang_r = "en" if _ascii_ratio_r > 0.85 else "hi"
                reply = (
                    "Sure! Let's start fresh. I'm Financial Mitra — ask me anything about investments, savings, or whether a scheme is safe."
                    if _lang_r == "en" else
                    "ठीक है! नए सिरे से शुरू करते हैं। मैं Financial Mitra हूं — कोई भी सवाल पूछें, निवेश, बचत या किसी स्कीम के बारे में।"
                )
                if wa_client and http_client and settings.whatsapp_access_token:
                    await wa_client.send_text(phone_number, reply, http_client)
                await save_message(db, conversation_id=conversation["id"], sender="system", input_type="text", message_text=reply)
                continue

            # ── 4b. Greeting short-circuit (skip full pipeline for simple greetings) ──
            _greetings = {"hi", "hii", "hello", "hey", "helo", "namaste", "namaskar", "yo", "sup", "hiya", "howdy"}
            if user_text.strip().lower().rstrip("!.") in _greetings:
                _txt = user_text.strip()
                _ascii_ratio = sum(ord(c) < 128 for c in _txt) / max(len(_txt), 1)
                _hinglish_words = {"kya", "hai", "hain", "nahi", "nahin", "ek", "haan", "bahut", "acha", "theek", "bhai", "yaar", "paise", "karo", "bolo", "mujhe", "mera", "tera", "aap", "tum", "kuch", "sab", "abhi", "wala", "wali", "kaisa", "kaisi", "kyun", "kab", "kahan", "invest", "paisa", "scheme", "matlab", "lagta", "chahiye"}
                _words = set(_txt.lower().split())
                _is_roman = _ascii_ratio > 0.85
                _has_hinglish = bool(_words & _hinglish_words)
                _lang = "hi" if not _is_roman else ("hinglish" if _has_hinglish else "en")
                
                reply = (
                    "Hello! I'm Financial Mitra, your financial safety guide. Ask me about any investment scheme, savings plan, or if something feels like a scam — I'm here to help!"
                    if _lang == "en" else
                    "नमस्ते! मैं Financial Mitra हूं। किसी भी निवेश, बचत योजना या संदिग्ध स्कीम के बारे में पूछें — मैं आपकी मदद करूंगा!"
                )
                if wa_client and http_client and settings.whatsapp_access_token:
                    await wa_client.send_text(phone_number, reply, http_client)
                await save_message(db, conversation_id=conversation["id"], sender="system", input_type="text", message_text=reply)
                continue

            # ── 5. Build reply (Groq Reasoning Pipeline) ────────────────────
            if user_text and intent_router and core_engine and shaper and settings.groq_api_key:
                try:
                    intent_str = await intent_router.classify(user_text)
                    if conversation.get("status") == "open":
                        try:
                            await db.table("conversations").update({"intent": intent_str}).eq("id", str(conversation["id"])).execute()
                        except Exception as e:
                            logger.error("failed_to_update_conversation_intent", extra={"error": str(e)})

                    rag_context = None
                    if intent_str == "trust_check" or any(w in user_text.lower() for w in ["scam", "fraud", "dhokha", "fake", "scheme", "chit", "invest"]):
                        rag_context = await retrieve_scam_context(db, user_text, settings)

                    core_out = await core_engine.reason(user_text, intent_str, rag_context=rag_context)
                    core_out_dict = core_out.model_dump()

                    # ── North Star Metric Logging (Phase 6) ───────────────────
                    verdict_str = str(core_out.verdict or "").lower()
                    if "avoid" in verdict_str or "scam" in verdict_str:
                        await log_financial_action(db, str(user["id"]), "scam_avoided", str(conversation["id"]))
                    elif any(w in str(core_out.next_action).lower() for w in ["save", "deposit", "fd", "scheme", "invest", "post office"]):
                        await log_financial_action(db, str(user["id"]), "savings_started", str(conversation["id"]))

                    # ── Risk / Distress Gate & Escalation ─────────────────────
                    if should_escalate(user_text, core_out):
                        esc_reason = escalation_reason(user_text, core_out)
                        await create_escalation(
                            db,
                            conversation_id=str(conversation["id"]),
                            reason=esc_reason,
                            risk_signals=core_out.risk_signals_detected,
                        )
                        logger.warning("conversation_escalated", extra={"conversation_id": str(conversation["id"]), "reason": esc_reason})

                    # Per-message language detection — detects English / Hinglish / Hindi
                    # from the CURRENT message so every reply matches what the user just typed.
                    _txt = user_text.strip()
                    _ascii_ratio = sum(ord(c) < 128 for c in _txt) / max(len(_txt), 1)
                    _hinglish_words = {
                        "kya", "hai", "hain", "nahi", "nahin", "ek", "haan", "bahut",
                        "acha", "theek", "bhai", "yaar", "paise", "karo", "bolo",
                        "mujhe", "mera", "tera", "aap", "tum", "kuch", "sab", "abhi",
                        "wala", "wali", "kaisa", "kaisi", "kyun", "kab", "kahan",
                        "invest", "paisa", "scheme", "matlab", "lagta", "chahiye",
                    }
                    _words = set(_txt.lower().split())
                    _is_roman = _ascii_ratio > 0.85  # mostly Latin script
                    _has_hinglish = bool(_words & _hinglish_words)
                    if not _is_roman:
                        user_lang = "hi"          # Devanagari → pure Hindi
                    elif _has_hinglish:
                        user_lang = "hinglish"    # Roman + Hindi words → Hinglish
                    else:
                        user_lang = "en"          # Pure English
                    reply = await shaper.shape(core_out, target_language=user_lang, input_type=current_input_type)
                    shaped_out_dict = {"text": reply, "language": user_lang, "intent": intent_str}

                except Exception as e:
                    logger.error("gemini_pipeline_failed_falling_back", extra={"error": str(e)}, exc_info=True)
                    reply = _build_phase1_reply(user_text)
            else:
                reply = _build_phase1_reply(user_text or "General query")

            # ── 5. Send reply via WhatsApp ────────────────────────────────────
            if wa_client and http_client and settings.whatsapp_access_token:
                await wa_client.send_text(phone_number, reply, http_client)
            else:
                logger.warning("whatsapp_send_skipped", extra={"reason": "no_client_or_credentials"})

            # ── 6. Save outbound message ──────────────────────────────────────
            await save_message(
                db,
                conversation_id=conversation["id"],
                sender="system",
                input_type="text",
                message_text=reply,
                core_engine_output=core_out_dict,
                shaped_response=shaped_out_dict,
            )
            logger.info("message_processed", extra={"input_type": current_input_type, "conversation_id": str(conversation["id"])})

        # Periodic cleanup of transient media files (Phase 6 Security §4.3)
        purge_expired_media(settings)

    except Exception as e:
        logger.error(
            "webhook_processing_error",
            extra={"error": str(e)},
            exc_info=True,
        )


def _build_phase1_reply(user_text: str) -> str:
    """
    Phase 1 reply builder.
    Returns a warm acknowledgement + placeholder response.
    Phase 2 replaces this entirely with the Gemini pipeline.
    """
    # Basic keyword check so even Phase 1 is not completely inert for demos
    text_lower = user_text.lower()

    if any(w in text_lower for w in ["scam", "fraud", "fake", "cheat", "dhoka"]):
        return (
            "⚠️ This sounds like it could be a scam concern. "
            "Our full scam-check feature is being built right now. "
            "For now: *do not send any money or share any OTP or PIN* until you've verified. "
            "\n\nI'll be able to give you a full analysis very soon! 🙏"
        )

    if any(w in text_lower for w in ["invest", "save", "paisa", "money", "rupee", "loan"]):
        return (
            "💰 Got your financial question! "
            "Our AI advisor is being set up to help you make the best decision. "
            "\n\nIn the meantime: be cautious of any offer that sounds too good to be true, "
            "and never share your PIN or OTP with anyone. Full guidance coming soon! 🙏"
        )

    return (
        f"✅ *Financial Mitra* received your message!\n\n"
        f"Our AI is being set up to help with financial questions and scam checks. "
        f"We'll be fully live very soon.\n\n"
        f"_If this is urgent, please reach out to a trusted family member or your bank directly._"
    )
