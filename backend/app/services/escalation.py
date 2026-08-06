"""
app/services/escalation.py — Escalation persistence and NGO/MFI partner notification.

Writes to the escalations table, updates the parent conversation status to 'escalated',
and sends structured safety callback notifications to authorized NGO/MFI case partners.
Per 02_System_Architecture.md Sections 4.5, 4.8, and Phase 4 SLA rules.
"""
from __future__ import annotations

import hmac
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

import httpx
from supabase import AsyncClient

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def notify_partner(
    escalation_id: str,
    conversation_id: str,
    reason: str,
    risk_signals: list[str],
    settings: Settings,
    http_client: Optional[httpx.AsyncClient] = None,
) -> bool:
    """
    Send an authenticated webhook callback to the registered NGO/MFI partner.

    Args:
        escalation_id: UUID string of the escalation record.
        conversation_id: UUID string of the escalated conversation.
        reason: Trigger reason ('keyword', 'llm_flag', 'both').
        risk_signals: List of detected financial distress or coercion patterns.
        settings: Application configuration containing partner URLs and SLA rules.
        http_client: Optional existing async HTTP client.

    Returns:
        True if notified successfully (or simulated in development), False otherwise.
    """
    payload = {
        "event": "financial_mitra.escalation_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "escalation_id": escalation_id,
        "conversation_id": conversation_id,
        "reason": reason,
        "risk_signals": risk_signals,
        "sla_response_required_hours": settings.partner_escalation_sla_hours,
        "partner_name": settings.partner_name,
    }

    # If no live webhook URL is configured (local dev/MVP mode), log simulated alert
    if not settings.partner_webhook_url:
        logger.warning(
            "partner_notification_simulated_no_url",
            extra={
                "escalation_id": escalation_id,
                "partner": settings.partner_name,
                "sla_hours": settings.partner_escalation_sla_hours,
                "payload": payload,
            },
        )
        return True

    headers = {"Content-Type": "application/json"}
    payload_bytes = json.dumps(payload).encode("utf-8")

    # Sign payload with HMAC-SHA256 if partner secret is configured
    if settings.partner_webhook_secret:
        sig = hmac.new(
            settings.partner_webhook_secret.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers["X-Mitra-Signature"] = f"sha256={sig}"

    close_client = False
    client = http_client
    if client is None:
        client = httpx.AsyncClient(timeout=10.0)
        close_client = True

    try:
        response = await client.post(settings.partner_webhook_url, content=payload_bytes, headers=headers)
        response.raise_for_status()
        logger.info(
            "partner_webhook_notified_successfully",
            extra={"escalation_id": escalation_id, "status_code": response.status_code},
        )
        return True
    except Exception as e:
        logger.error(
            "partner_webhook_notification_failed",
            extra={"escalation_id": escalation_id, "url": settings.partner_webhook_url, "error": str(e)},
        )
        return False
    finally:
        if close_client and client:
            await client.aclose()


async def create_escalation(
    db: AsyncClient,
    conversation_id: str,
    reason: str,
    risk_signals: Optional[list[str]] = None,
    settings: Optional[Settings] = None,
    http_client: Optional[httpx.AsyncClient] = None,
) -> Optional[dict]:
    """
    Write an escalation record, mark conversation 'escalated', and notify NGO partner.

    Args:
        db: Supabase async client.
        conversation_id: UUID string of the conversation.
        reason: 'keyword' | 'llm_flag' | 'both'
        risk_signals: List of specific patterns detected (from CoreEngineOutput).
        settings: Application config settings (defaults to get_settings()).
        http_client: Optional reusable HTTP client for webhook callback.

    Returns:
        The created escalation record dict, or None if DB write failed.
        Guaranteed exception-safe: never raises to user conversational pipeline.
    """
    if risk_signals is None:
        risk_signals = []
    if settings is None:
        settings = get_settings()

    try:
        result = await (
            db.table("escalations")
            .insert({
                "conversation_id": conversation_id,
                "reason": reason,
                "risk_signals": risk_signals,
                "status": "pending",
            })
            .execute()
        )
        
        record = result.data[0] if result.data else None
        if not record or not isinstance(record, dict):
            logger.error("escalation_insert_returned_empty_data", extra={"conversation_id": conversation_id})
            return None

        escalation_id = str(record["id"])

        # Update conversation status so it's instantly visible in safety dashboards
        await (
            db.table("conversations")
            .update({"status": "escalated"})
            .eq("id", conversation_id)
            .execute()
        )

        logger.info(
            "escalation_created",
            extra={
                "escalation_id": escalation_id,
                "conversation_id": conversation_id,
                "reason": reason,
                "risk_signal_count": len(risk_signals),
            },
        )

        # Phase 4: Notify NGO/MFI case worker & update partner_notified_at
        notified = await notify_partner(
            escalation_id=escalation_id,
            conversation_id=conversation_id,
            reason=reason,
            risk_signals=risk_signals,
            settings=settings,
            http_client=http_client,
        )

        if notified:
            notified_time = datetime.utcnow().isoformat()
            try:
                await (
                    db.table("escalations")
                    .update({"partner_notified_at": notified_time})
                    .eq("id", escalation_id)
                    .execute()
                )
                record["partner_notified_at"] = notified_time
            except Exception as update_err:
                logger.warning("failed_to_update_partner_notified_at", extra={"error": str(update_err)})

        return record

    except Exception as e:
        logger.error(
            "escalation_write_failed",
            extra={"conversation_id": conversation_id, "error": str(e)},
        )
        return None
