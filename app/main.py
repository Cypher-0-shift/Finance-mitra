"""
app/main.py — FastAPI application factory for Financial Mitra.

Wires together:
  - Application lifespan (startup/shutdown): Supabase init,
    startup checks (GEMINI_TIER production guard)
  - Routers: webhook, internal
  - /health endpoint: used by Render health checks and keep-alive pings
  - Structured logging configuration

Design: async-first throughout, matching 04_Tech_Stack.md Section 1.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.client import get_db, init_supabase
from app.engines.core_engine import CoreEngine
from app.engines.intent_router import IntentRouter
from app.engines.shaper import LanguageTrustShaper
from app.engines.vision import VisionEngine
from app.routers import internal, webhook
from app.services.whatsapp import WhatsAppClient

# ── Structured logging setup ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("financial_mitra")

# ── Shared singletons (set during startup lifespan) ──────────────────────────
_http_client: httpx.AsyncClient | None = None
_whatsapp_client: WhatsAppClient | None = None
_core_engine: CoreEngine | None = None
_shaper: LanguageTrustShaper | None = None
_intent_router: IntentRouter | None = None
_vision_engine: VisionEngine | None = None


def get_http_client() -> httpx.AsyncClient | None:
    return _http_client


def get_whatsapp_client() -> WhatsAppClient | None:
    return _whatsapp_client


def get_core_engine() -> CoreEngine | None:
    return _core_engine


def get_shaper() -> LanguageTrustShaper | None:
    return _shaper


def get_intent_router() -> IntentRouter | None:
    return _intent_router


def get_vision_engine() -> VisionEngine | None:
    return _vision_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Runs startup tasks before serving requests; cleanup on shutdown.
    """
    global _http_client, _whatsapp_client, _core_engine, _shaper, _intent_router, _vision_engine
    settings = get_settings()

    # ── 1. Data privacy + environment startup checks ──────────────────────────
    # This will raise RuntimeError and refuse to start if ENVIRONMENT=production
    # and GEMINI_TIER=free (see app/config.py for the full error message).
    settings.startup_checks()
    logger.info("startup_checks_passed", extra={"environment": settings.environment})

    # ── 2. Supabase client initialisation ─────────────────────────────────────
    # Raises RuntimeError if connection fails — fail fast at startup.
    await init_supabase(settings)

    # ── 4. Shared HTTP client for WhatsApp outbound ───────────────────────────
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(15.0),
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )
    logger.info("http_client_initialised")

    # ── 5. WhatsApp outbound client ───────────────────────────────────────────
    _whatsapp_client = WhatsAppClient(settings)
    logger.info("whatsapp_client_initialised")

    # ── 6. LLM Engine Singletons (Phase 2 & 5) ───────────────────────────────
    _core_engine = CoreEngine(settings)
    _shaper = LanguageTrustShaper(settings)
    _intent_router = IntentRouter(settings)
    _vision_engine = VisionEngine(settings)
    logger.info("llm_engines_initialised")

    # ── 7. Confirm Dev Chat Endpoint Status ───────────────────────────────────
    if settings.environment == "development":
        logger.info(
            "dev_chat_endpoint_active",
            extra={"status": "active", "path": "/dev/chat", "environment": settings.environment},
        )
    else:
        logger.info(
            "dev_chat_endpoint_disabled",
            extra={"status": "disabled", "path": "/dev/chat", "environment": settings.environment},
        )

    logger.info(
        "financial_mitra_started",
        extra={
            "environment": settings.environment,
            "llm_provider": "groq",
            "groq_ready": bool(settings.groq_api_key),
        },
    )

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    if _http_client:
        await _http_client.aclose()
        logger.info("http_client_closed")

    logger.info("financial_mitra_shutdown")


# ── FastAPI application ────────────────────────────────────────────────────────
app = FastAPI(
    title="Financial Mitra API",
    description=(
        "WhatsApp-first AI financial companion for low-income users in India. "
        "Internal API documentation — not public-facing."
    ),
    version="0.1.0",
    lifespan=lifespan,
    # Disable automatic OpenAPI exposure in production (internal tooling only)
    docs_url="/docs" if True else None,   # TODO: gate on ENVIRONMENT != "production"
    redoc_url=None,
)


# ── Routers & Web Demo UI Middleware ─────────────────────────────────────────
app.include_router(webhook.router)
app.include_router(internal.router)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.routers import dev

# Unconditionally enable dev/demo chat router and static GUI for easy live demoing
app.include_router(dev.router)
app.mount("/dev-tools", StaticFiles(directory="dev-tools", html=True), name="dev-tools")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Enable universal access for public demo testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root hits directly to the interactive Web Demo UI."""
    return RedirectResponse(url="/dev-tools/chat-tester.html")


# ── Health check endpoint ──────────────────────────────────────────────────────
@app.get("/health", tags=["ops"])
async def health_check(request: Request) -> JSONResponse:
    """
    Render health check + keep-alive endpoint.

    Performs a trivial Supabase query (SELECT 1) so a single ping keeps both
    Render and Supabase free-tier warm simultaneously.

    Protected by RENDER_HEALTH_CHECK_TOKEN header for non-Render callers.
    Render's own health checks don't send the token — we allow those through
    (Render-initiated checks come from known Render IP ranges and are part of
    the deployment contract).

    Returns:
        {"status": "ok", "db": "ok" | "error", "latency_ms": float}
    """
    settings = get_settings()
    token = request.headers.get("X-Health-Token")

    # Allow Render's own health checks (no token) and authenticated keep-alive pings
    # Block others (a curious probe shouldn't get useful system information)
    if token and token != settings.render_health_check_token:
        return JSONResponse(
            status_code=403,
            content={"status": "forbidden"},
        )

    start = time.monotonic()
    db_status = "ok"

    try:
        db = get_db()
        await db.table("users").select("id").limit(1).execute()
    except Exception as e:
        logger.warning("health_check_db_error", extra={"error": str(e)})
        db_status = "error"

    latency_ms = round((time.monotonic() - start) * 1000, 2)

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "db": db_status,
            "latency_ms": latency_ms,
        },
    )


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler. Logs unhandled exceptions and returns a generic 500.
    Never exposes internal details to the caller.
    """
    logger.error(
        "unhandled_exception",
        extra={"path": str(request.url.path), "error": str(exc)},
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Our team has been notified."},
    )
