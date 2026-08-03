"""
app/dependencies.py — Shared FastAPI dependencies.

Central location for dependencies used across multiple routers.
Keeps individual router files lean and avoids circular imports.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.config import Settings, get_settings
from app.db.client import get_db


def get_settings_dep() -> Settings:
    """Settings dependency — cached singleton."""
    return get_settings()


# Typed aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
