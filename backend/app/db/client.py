"""
app/db/client.py — Supabase client initialisation for Financial Mitra.

Provides a single shared async Supabase client instance used across all services.
The client is initialised once at application startup (app/main.py lifespan) and
reused across all requests — not re-created per request.

IMPORTANT: the service role key gives elevated access — it bypasses RLS policies.
This is intentional for server-side operations, but:
  1. Never expose this key to client-side code or logs.
  2. When implementing user-specific queries, use RLS policies to scope access
     correctly at the DB level even when using the service role key at the
     application level — defence in depth.
  3. See 02_System_Architecture.md Section 5, Design notes.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from supabase import AsyncClient, acreate_client

from app.config import Settings

logger = logging.getLogger(__name__)

# Module-level singleton — set once during startup lifespan, used everywhere.
_supabase_client: AsyncClient | None = None


async def init_supabase(settings: Settings) -> AsyncClient:
    """
    Initialise the Supabase async client. Called once from app/main.py lifespan.
    Raises on connection failure so the app refuses to start with a bad config,
    rather than discovering it at first request.
    """
    global _supabase_client

    logger.info("supabase_client_init", extra={"url": settings.supabase_url})

    _supabase_client = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_role_key,
    )

    # Smoke-test: confirm DB is reachable (keep-alive ping also does this at runtime)
    try:
        await _supabase_client.table("users").select("id").limit(1).execute()
        logger.info("supabase_connected")
    except Exception as e:
        logger.error("supabase_connection_failed", extra={"error": str(e)})
        raise RuntimeError(
            f"Supabase connection failed at startup. Check SUPABASE_URL and "
            f"SUPABASE_SERVICE_ROLE_KEY. Error: {e}"
        ) from e

    return _supabase_client


def get_db() -> AsyncClient:
    """
    Returns the shared Supabase client.
    Raises RuntimeError if called before init_supabase() completes.
    Use as a FastAPI dependency via Depends(get_db).
    """
    if _supabase_client is None:
        raise RuntimeError(
            "Supabase client not initialised. "
            "This should not happen — check lifespan in app/main.py."
        )
    return _supabase_client
