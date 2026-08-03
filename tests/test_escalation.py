"""
tests/test_escalation.py — Tests for escalation record persistence and error handling.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.escalation import create_escalation


@pytest.mark.asyncio
async def test_create_escalation_success():
    """Verify that create_escalation writes to escalations and updates conversation status."""
    mock_db = MagicMock()

    # Mock insert into escalations table
    insert_chain = MagicMock()
    insert_chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": "esc_123", "status": "pending"}]))
    
    # Mock update to conversations table
    update_chain = MagicMock()
    update_chain.eq.return_value = update_chain
    update_chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": "conv_123", "status": "escalated"}]))

    def table_mock(name: str):
        if name == "escalations":
            t = MagicMock()
            t.insert.return_value = insert_chain
            return t
        elif name == "conversations":
            t = MagicMock()
            t.update.return_value = update_chain
            return t
        return MagicMock()

    mock_db.table.side_effect = table_mock

    result = await create_escalation(
        db=mock_db,
        conversation_id="conv_123",
        reason="both",
        risk_signals=["suicide", "high_pressure"],
    )

    assert result == {"id": "esc_123", "status": "pending"}
    
    # Verify escalations insertion
    insert_chain.execute.assert_called_once()
    
    # Verify conversations status update to 'escalated'
    update_chain.eq.assert_called_with("id", "conv_123")
    update_chain.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_escalation_failure_never_raises():
    """Verify that database errors during escalation creation log and return None without raising."""
    mock_db = MagicMock()
    mock_db.table.side_effect = Exception("Database connection timeout")

    result = await create_escalation(
        db=mock_db,
        conversation_id="conv_123",
        reason="keyword",
    )

    assert result is None
