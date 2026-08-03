"""
app/services/rate_limit.py — Rate Limiting and Cost Cap Protection Service.

Performs stateless DB checking and incrementing against rate_limit_counters
to protect LLM processing budgets and prevent abuse (Security Section 5.2).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from supabase import Client
from app.config import Settings

logger = logging.getLogger(__name__)


async def check_and_record_usage(
    db: Client,
    user_id: str,
    settings: Settings,
    estimated_cost_inr: float = 0.15,  # Estimated per-turn average LLM cost in ₹
) -> tuple[bool, Optional[str]]:
    """
    Check if user has exceeded hourly rate limit window or daily cost threshold.
    If acceptable, increments the usage metrics.

    Returns:
      Tuple of (is_allowed: bool, throttle_message: str | None)
    """
    if not user_id:
        return (True, None)

    now_ts = int(datetime.now(timezone.utc).timestamp())
    window_start_target = now_ts - settings.rate_limit_window_seconds
    day_start_target = now_ts - 86400

    try:
        # Fetch current record for user
        res = await db.table("rate_limit_counters").select("*").eq("user_id", user_id).limit(1).execute()
        records = res.data if res and hasattr(res, "data") else []

        if not records:
            # First turn: insert initializing row
            new_row = {
                "user_id": user_id,
                "window_start": datetime.fromtimestamp(now_ts, timezone.utc).isoformat(),
                "request_count": 1,
                "daily_cost_inr": estimated_cost_inr,
                "daily_window_start": datetime.fromtimestamp(now_ts, timezone.utc).isoformat(),
            }
            try:
                await db.table("rate_limit_counters").insert(new_row).execute()
            except Exception:
                pass  # Ignore rare insert race condition
            return (True, None)

        record = records[0]
        rec_id = record["id"]
        req_count = int(record.get("request_count", 0))
        daily_cost = float(record.get("daily_cost_inr", 0.0))

        # Check window timestamps and reset if expired
        win_start_str = record.get("window_start")
        try:
            win_start_ts = int(datetime.fromisoformat(str(win_start_str).replace("Z", "+00:00")).timestamp())
        except Exception:
            win_start_ts = now_ts

        if win_start_ts < window_start_target:
            req_count = 0
            new_win_start = datetime.fromtimestamp(now_ts, timezone.utc).isoformat()
        else:
            new_win_start = str(win_start_str)

        # Check daily cost timestamp and reset if > 24 hours
        daily_start_str = record.get("daily_window_start") or new_win_start
        try:
            daily_start_ts = int(datetime.fromisoformat(str(daily_start_str).replace("Z", "+00:00")).timestamp())
        except Exception:
            daily_start_ts = now_ts

        if daily_start_ts < day_start_target:
            daily_cost = 0.0
            new_daily_start = datetime.fromtimestamp(now_ts, timezone.utc).isoformat()
        else:
            new_daily_start = str(daily_start_str)

        # 1. Enforce hourly frequency rate limiting
        if req_count >= settings.rate_limit_requests_per_window:
            logger.warning("rate_limit_exceeded_hourly", extra={"user_id_preview": user_id[:8]})
            return (
                False,
                "You're sending messages faster than I can keep up — give me a moment to process everything! Please write again in some time. 🙏",
            )

        # 2. Enforce per-user daily financial cost cap (₹5/day per Security Section 5.2)
        if daily_cost + estimated_cost_inr > settings.per_user_daily_cost_cap_inr:
            logger.warning("cost_cap_exceeded_daily", extra={"user_id_preview": user_id[:8], "cost": daily_cost})
            return (
                False,
                "You have reached the daily message limit for free usage today. Our AI advisor will be refreshed and ready to assist you tomorrow! 🙏",
            )

        # Update counter increments
        update_payload = {
            "request_count": req_count + 1,
            "daily_cost_inr": round(daily_cost + estimated_cost_inr, 4),
            "window_start": new_win_start,
            "daily_window_start": new_daily_start,
        }
        await db.table("rate_limit_counters").update(update_payload).eq("id", rec_id).execute()
        return (True, None)

    except Exception as e:
        logger.error("rate_limit_check_db_error", extra={"error": str(e)})
        # On database connection failure during rate limit check, fail open so conversation doesn't break
        return (True, None)
