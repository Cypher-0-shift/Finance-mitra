"""
tests/test_rate_limit.py — Unit tests for Phase 6 Rate Limiting, Cost Cap, and North Star Analytics.

Verifies:
  - Rate limiting counter enforcement and throttling notification delivery
  - Cost cap calculation and protection when daily spending ceiling is crossed
  - North Star milestone event logging (financial_actions_log)
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.config import Settings
from app.services.analytics import log_financial_action
from app.services.rate_limit import check_and_record_usage


@pytest.fixture
def pilot_settings():
    return Settings(
        environment="development",
        rate_limit_requests_per_window=5,
        per_user_daily_cost_cap_inr=1.0,
    )


@pytest.mark.asyncio
async def test_rate_limit_first_request_allows(pilot_settings):
    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": 1}]))

    is_allowed, msg = await check_and_record_usage(mock_db, "test_user", pilot_settings)
    assert is_allowed is True
    assert msg is None


@pytest.mark.asyncio
async def test_rate_limit_hourly_exceeded(pilot_settings):
    mock_db = MagicMock()
    now_iso = datetime.now(timezone.utc).isoformat()
    mock_record = {
        "id": "1",
        "request_count": 5,
        "daily_cost_inr": 0.5,
        "window_start": now_iso,
        "daily_window_start": now_iso,
    }
    mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = AsyncMock(return_value=MagicMock(data=[mock_record]))

    is_allowed, msg = await check_and_record_usage(mock_db, "test_user", pilot_settings, estimated_cost_inr=0.1)
    assert is_allowed is False
    assert msg is not None
    assert "faster than I can keep up" in msg


@pytest.mark.asyncio
async def test_cost_cap_daily_exceeded(pilot_settings):
    mock_db = MagicMock()
    now_iso = datetime.now(timezone.utc).isoformat()
    mock_record = {
        "id": "1",
        "request_count": 2,
        "daily_cost_inr": 0.95,
        "window_start": now_iso,
        "daily_window_start": now_iso,
    }
    mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute = AsyncMock(return_value=MagicMock(data=[mock_record]))

    is_allowed, msg = await check_and_record_usage(mock_db, "test_user", pilot_settings, estimated_cost_inr=0.15)
    assert is_allowed is False
    assert msg is not None
    assert "daily message limit" in msg


@pytest.mark.asyncio
async def test_north_star_action_logging():
    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": str(uuid4())}]))

    await log_financial_action(
        mock_db,
        user_id=str(uuid4()),
        action_type="scam_avoided",
        conversation_id=str(uuid4()),
    )
    assert mock_db.table.called
    assert "financial_actions_log" in str(mock_db.table.call_args)
