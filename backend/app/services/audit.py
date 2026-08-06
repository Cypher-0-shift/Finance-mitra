"""
app/services/audit.py — Audit log writer for Finance Mitra.

Every access to raw conversation data, the escalation queue, or any
internal admin view MUST call write_audit_log() before returning data.

Per 02_System_Architecture.md Section 9.6 and pilot launch checklist item 8.

This is intentionally a thin wrapper — the complexity is in ensuring every
call site that touches sensitive data actually calls it, not in the writer itself.
Structured logging in the background catches any calls that are missed
(logged events are cross-referenced against audit_log rows in review).
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from supabase import AsyncClient

logger = logging.getLogger(__name__)


async def write_audit_log(
    db: AsyncClient,
    actor: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
) -> None:
    """
    Write a single row to the audit_log table.

    Args:
        db: Supabase async client.
        actor: Authenticated identity — user ID, service name, or 'system'.
        action: What was done, e.g. 'viewed_escalation', 'accessed_raw_conversation'.
        resource_type: Type of the accessed resource, e.g. 'escalation', 'message'.
        resource_id: UUID of the specific resource accessed.
        ip_address: Request IP where available (may be None for internal service calls).

    Raises:
        Logs errors but does not re-raise — a failing audit write should not
        block the response. However, every failure IS logged at ERROR level
        so it's visible in the structured log stream.
    """
    row: dict = {
        "actor": actor,
        "action": action,
    }
    if resource_type:
        row["resource_type"] = resource_type
    if resource_id:
        row["resource_id"] = str(resource_id)
    if ip_address:
        row["ip_address"] = ip_address

    try:
        await db.table("audit_log").insert(row).execute()
        logger.info(
            "audit_log_written",
            extra={
                "actor": actor,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id) if resource_id else None,
            },
        )
    except Exception as e:
        logger.error(
            "audit_log_write_failed",
            extra={
                "actor": actor,
                "action": action,
                "error": str(e),
            },
        )
