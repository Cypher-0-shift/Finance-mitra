"""
app/config.py — Application settings for Financial Mitra.

All configuration is read from environment variables (Railway/Render env vars in
production; .env file in local development via python-dotenv).

NEVER add default values for secrets here. If a required secret is missing,
Pydantic Settings will raise a clear error at startup — better than a silent failure.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object. Instantiated once at startup via get_settings()."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # Ignore extra env vars — don't fail on unrecognised keys
    )

    # ── Application ──────────────────────────────────────────────────────────
    environment: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── WhatsApp Cloud API (Meta) ─────────────────────────────────────────────
    # Empty string defaults so the app starts in dev before Meta is provisioned.
    # Production startup_checks() warns (not blocks) if these are missing.
    whatsapp_verify_token: str = "mitra_verify_2024"
    whatsapp_app_secret: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_api_version: str = "v22.0"

    # ── Groq ──────────────────────────────────────────────────────────────────
    # LLM provider for all text pipelines (Core Engine, Shaper, Intent Router).
    # Free tier: ~14,400 requests/day. Get a key at: https://console.groq.com
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key from console.groq.com")
    groq_model_cheap: str = "llama-3.1-8b-instant"       # Intent classification + Shaper
    groq_model_strong: str = "llama-3.3-70b-versatile"   # Core reasoning (all intents)

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_url: str = Field(..., description="https://<project-ref>.supabase.co")
    supabase_service_role_key: str = Field(..., description="Service role key — never expose to client")
    supabase_anon_key: str = Field(..., description="Anon key — for Supabase Auth only")

    # ── Security ──────────────────────────────────────────────────────────────
    # Salt lives in secrets manager, never in the DB — per 03_Security_Compliance.md Section 4.4
    whatsapp_id_hash_salt: str = Field(..., description="Server-side salt for hashing WhatsApp IDs")
    internal_service_token: str = Field(..., description="Bearer token for service-to-service auth")
    render_health_check_token: str = Field(..., description="Token for /health keep-alive pings")

    # ── Phase 4 Partner Notification & Safety SLA ────────────────────────────
    partner_name: str = "Demo NGO / MFI Partner"
    partner_webhook_url: Optional[str] = None      # Webhook URL for alerting NGO/MFI case workers
    partner_webhook_secret: Optional[str] = None   # Secret for signing partner webhooks
    partner_escalation_sla_hours: int = 4          # Written SLA response time required by PRD

    # ── Rate limiting & cost caps ─────────────────────────────────────────────
    rate_limit_requests_per_window: int = 20
    rate_limit_window_seconds: int = 3600        # 1 hour
    per_user_daily_cost_cap_inr: float = 5.0     # ₹5 per user per day

    # ── Media handling ────────────────────────────────────────────────────────
    media_retention_hours: int = 24              # Voice/image deletion window

    @field_validator("environment", mode="before")
    @classmethod
    def normalise_environment(cls, v: str) -> str:
        return v.lower().strip()

    def startup_checks(self) -> None:
        """
        Called once at application startup (app/main.py lifespan).
        Validates invariants that cannot be caught by field-level validators alone.
        """
        import logging as _log
        _logger = _log.getLogger("financial_mitra")

        if not self.groq_api_key:
            _logger.warning(
                "GROQ_API_KEY is not set — all LLM pipeline calls will return fallback responses. "
                "Get a free key at https://console.groq.com"
            )

        # Warn (not block) if WhatsApp credentials are missing
        missing_wa = [f for f in [
            "whatsapp_app_secret", "whatsapp_access_token", "whatsapp_phone_number_id"
        ] if not getattr(self, f)]
        if missing_wa:
            _logger.warning(
                "WhatsApp credentials not set: %s — webhook send/verify will not work.",
                missing_wa,
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the cached Settings singleton. Use this everywhere instead of
    instantiating Settings directly, so the startup checks run exactly once.
    """
    settings = Settings()  # type: ignore[call-arg]
    return settings
