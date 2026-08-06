"""
app/services/analytics.py — North Star Metric Logging (FR-9 / Architecture Section 4.10).

Logs positive user financial actions and scam avoidance milestones without preserving
raw conversational text or personally identifying message contents.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from supabase import Client

logger = logging.getLogger(__name__)


async def log_financial_action(
    db: Client,
    user_id: str,
    action_type: str,
    conversation_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """
    Record a North Star financial milestone or action in financial_actions_log table.

    Valid action_types:
      - 'scam_avoided': User identified and avoided an fraudulent offer or loan app.
      - 'savings_started': User selected a tangible savings or investment step.
      - 'scheme_explored': User received actionable eligibility info on govt schemes.
      - 'budget_created': User aligned on a concrete debt/expense action.
    """
    if not user_id:
        return

    payload = {
        "user_id": user_id,
        "action_type": action_type,
        "conversation_id": conversation_id,
        "metadata": metadata or {},
    }

    try:
        await db.table("financial_actions_log").insert(payload).execute()
        logger.info(
            "north_star_action_logged",
            extra={"action_type": action_type, "user_id_preview": user_id[:8]},
        )
    except Exception as e:
        logger.error("north_star_logging_failed", extra={"error": str(e), "action_type": action_type})
