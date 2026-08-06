"""
app/schemas/internal.py — Pydantic models for internal API endpoints.

These models cover:
  - POST /internal/escalate (Section 6.3 of architecture doc)
  - GET /internal/escalations (Section 6.4)

All internal endpoints require authenticated access with role checking.
Every access writes an audit_log entry (Section 9.6).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EscalationReason(str, Enum):
    KEYWORD = "keyword"
    LLM_FLAG = "llm_flag"
    BOTH = "both"


class EscalationStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class EscalationRequest(BaseModel):
    """
    Body for POST /internal/escalate.
    Per 02_System_Architecture.md Section 6.3.
    Called by the escalation notifier with a service token.
    """
    conversation_id: UUID
    reason: EscalationReason
    risk_signals: list[str] = Field(default_factory=list)


class EscalationResponse(BaseModel):
    """Response from POST /internal/escalate."""
    escalation_id: UUID
    status: EscalationStatus
    message: str = "Escalation created and partner notified."


class EscalationRecord(BaseModel):
    """
    A single escalation record returned by GET /internal/escalations.
    Viewing this endpoint writes an audit_log entry per Section 9.6.
    """
    id: UUID
    conversation_id: UUID
    reason: EscalationReason
    risk_signals: list[Any] = Field(default_factory=list)
    status: EscalationStatus
    partner_notified_at: Optional[str] = None
    created_at: str


class InternalRole(str, Enum):
    """
    Role-based access per 03_Security_Compliance.md Section 3.
    team_member: full internal access.
    partner_viewer: escalation queue only, scoped to their org's cases.
    """
    TEAM_MEMBER = "team_member"
    PARTNER_VIEWER = "partner_viewer"
