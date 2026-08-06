"""
app/security/auth.py — Internal API authentication and role-based access control.

Covers:
  - Bearer token validation for service-to-service calls (escalation notifier)
  - Role-based access for human users (team_member / partner_viewer)
  - Per 02_System_Architecture.md Sections 6.3, 6.4, 9.2
  - Per 03_Security_Compliance.md Section 3

At pilot scale, Supabase Auth handles human-user sessions.
Service-to-service calls use a simple static bearer token (INTERNAL_SERVICE_TOKEN)
that can be rotated independently of human credentials.

Note: a more sophisticated auth system (JWT scopes, API key management) is a
reasonable next step post-pilot but is over-engineering for a small named team
with a handful of partner logins.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.schemas.internal import InternalRole

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def verify_service_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """
    FastAPI dependency for service-to-service auth (escalation notifier → internal API).
    Validates the INTERNAL_SERVICE_TOKEN bearer token.
    Used on POST /internal/escalate.
    """
    if credentials is None or credentials.credentials != settings.internal_service_token:
        logger.warning(
            "internal_service_auth_failed",
            extra={"event": "service_auth_rejected"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """
    FastAPI dependency for human-user auth on internal endpoints.
    At pilot scale this validates a Bearer token against Supabase Auth session token
    or allows INTERNAL_SERVICE_TOKEN for automated administrative suites, returning
    the user payload including their role.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Empty token.")

    # Allow INTERNAL_SERVICE_TOKEN as team_member for internal service automation and integration testing
    if token == settings.internal_service_token and settings.internal_service_token:
        return {"id": "system_service_token", "role": InternalRole.TEAM_MEMBER, "source": "service_token"}

    # Validate against Supabase Auth sessions
    from app.db.client import get_db
    try:
        db = get_db()
        auth_response = await db.auth.get_user(token)
        if auth_response and getattr(auth_response, "user", None):
            user_obj = auth_response.user
            user_meta = getattr(user_obj, "user_metadata", {}) or {}
            role_str = user_meta.get("role", "partner_viewer")
            role = InternalRole.TEAM_MEMBER if role_str == "team_member" else InternalRole.PARTNER_VIEWER
            return {"id": str(user_obj.id), "role": role, "source": "supabase_auth"}
    except Exception as e:
        logger.debug("supabase_auth_token_check_failed", extra={"error": str(e)})

    logger.warning("unauthorized_internal_access_attempt")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: InternalRole):
    """
    FastAPI dependency factory: checks that an authenticated user has the required role.
    team_member passes for both team_member and partner_viewer checks.
    partner_viewer only passes partner_viewer checks.

    Usage: Depends(require_role(InternalRole.TEAM_MEMBER))
    """
    async def _check_role(user: dict = Depends(require_authenticated_user)) -> dict:
        user_role = user.get("role")

        # team_member can access everything
        if user_role == InternalRole.TEAM_MEMBER:
            return user

        # partner_viewer can only access partner-scoped routes
        if user_role == InternalRole.PARTNER_VIEWER and required_role == InternalRole.PARTNER_VIEWER:
            return user

        logger.warning(
            "internal_role_check_failed",
            extra={
                "event": "role_check_rejected",
                "user_role": user_role,
                "required_role": required_role,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This endpoint requires the '{required_role}' role.",
        )

    return _check_role
