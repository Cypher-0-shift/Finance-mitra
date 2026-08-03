"""
app/routers/internal.py — Internal authenticated API endpoints.

Covers:
  - POST /internal/escalate — service-to-service escalation notification
  - GET /internal/escalations — authenticated escalation queue access

Per 02_System_Architecture.md Sections 6.3 and 6.4.

SECURITY:
  - /internal/escalate: service token auth (INTERNAL_SERVICE_TOKEN bearer)
  - /internal/escalations: human user auth + role check (Phase 4)
  - Every GET access to /internal/escalations writes an audit_log row
  - No public, unauthenticated access — ever (PRD FR-12)

Phase 0: /internal/escalate is functional (can receive calls from the escalation
         notifier once it exists). /internal/escalations is stubbed with the
         authenticated-user dependency that intentionally blocks until Phase 4.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.schemas.internal import (
    EscalationReason,
    EscalationRequest,
    EscalationResponse,
    EscalationStatus,
    InternalRole,
)
from app.security.auth import require_authenticated_user, require_role, verify_service_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post(
    "/escalate",
    response_model=EscalationResponse,
    dependencies=[Depends(verify_service_token)],
    summary="Create an escalation record (service-to-service, authenticated)",
)
async def create_escalation(
    body: EscalationRequest,
) -> EscalationResponse:
    """
    Called by the Escalation Notifier (Section 4.8) when the Risk/Distress gate fires.

    Actions:
      1. Write escalations row to Supabase
      2. Notify NGO/MFI partner channel
      3. Update conversation status to 'escalated'
    """
    from app.db.client import get_db
    from app.services.escalation import create_escalation as service_create_escalation

    logger.info(
        "escalation_received",
        extra={
            "conversation_id": str(body.conversation_id),
            "reason": body.reason,
            "risk_signal_count": len(body.risk_signals),
        },
    )
    try:
        db = get_db()
        record = await service_create_escalation(
            db=db,
            conversation_id=str(body.conversation_id),
            reason=body.reason,
            risk_signals=body.risk_signals,
        )
        if record and "id" in record:
            return EscalationResponse(
                escalation_id=record["id"],
                status=EscalationStatus.PENDING,
                message="Escalation recorded and partner alerted.",
            )
    except Exception as e:
        logger.error("escalate_endpoint_error", extra={"error": str(e)})

    return EscalationResponse(
        escalation_id=body.conversation_id,
        status=EscalationStatus.PENDING,
        message="Escalation processed in fallback mode.",
    )


@router.get(
    "/escalations",
    summary="View escalation queue (authenticated team/partner access)",
    dependencies=[Depends(require_role(InternalRole.TEAM_MEMBER))],
)
async def list_escalations(
    request: Request,
    user: dict = Depends(require_authenticated_user),
) -> list:
    """
    Returns the escalation queue. Every access writes an audit_log row.

    Per 02_System_Architecture.md Section 6.4:
    'requires role check (team-member or authorized-partner role);
     every access writes an audit_log entry (who, when, what was viewed)'
    """
    from app.db.client import get_db
    from app.services.audit import write_audit_log

    db = get_db()
    actor_id = str(user.get("id", "unknown"))
    client_ip = request.client.host if request.client else None

    await write_audit_log(
        db=db,
        actor=actor_id,
        action="viewed_escalation_queue",
        resource_type="escalation_list",
        ip_address=client_ip,
    )

    try:
        result = await db.table("escalations").select("*").order("created_at", desc=True).execute()
        return result.data if result and hasattr(result, "data") and result.data else []
    except Exception as e:
        logger.error("list_escalations_query_failed", extra={"error": str(e)})
        return []

