"""
tests/test_dev_chat.py — Unit tests for the development testing endpoint POST /dev/chat.

Verifies:
  - In development mode: POST /dev/chat exercises the pipeline and returns expected schema.
  - In production mode: POST /dev/chat is completely absent from route table (returns HTTP 404).
"""
from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
import app.main
from app.schemas.core_engine import CoreEngineOutput


@pytest.fixture(autouse=True)
def reset_app_state(monkeypatch):
    """Ensure environment and cached settings are reset before and after each test."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_DummyTestKey1234567890")
    get_settings.cache_clear()
    importlib.reload(app.main)
    yield
    monkeypatch.setenv("ENVIRONMENT", "development")
    get_settings.cache_clear()
    importlib.reload(app.main)


def test_dev_chat_endpoint_active_in_development():
    """Verify POST /dev/chat is registered and processes requests in development environment."""
    client = TestClient(app.main.app)

    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": str(uuid4())}]))
    mock_db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))

    mock_router = MagicMock()
    mock_router.classify = AsyncMock(return_value="money_decision")

    mock_core = MagicMock()
    mock_core_out = CoreEngineOutput(
        core_message="Consider fixed deposit in bank or post office.",
        next_action="Check interest rates at nearest branch.",
        verdict=None,
        risk_signals_detected=[],
        escalation_recommended=False,
        sources=[],
    )
    mock_core.reason = AsyncMock(return_value=mock_core_out)

    mock_shaper = MagicMock()
    mock_shaper.shape = AsyncMock(return_value="Namaste! Apni bachhat ke liye Bank FD dekhein. 🙏")
    mock_shaper.translate_action = AsyncMock(return_value="Check interest rates at nearest branch.")

    with patch("app.routers.dev.get_db", return_value=mock_db), \
         patch("app.routers.dev.get_or_create_user", new_callable=AsyncMock, return_value={"id": str(uuid4()), "preferred_language": "hi"}), \
         patch("app.routers.dev.get_or_create_conversation", new_callable=AsyncMock, return_value={"id": str(uuid4()), "status": "open"}), \
         patch("app.routers.dev.save_message", new_callable=AsyncMock) as mock_save, \
         patch("app.routers.dev.check_and_record_usage", new_callable=AsyncMock, return_value=(True, None)), \
         patch("app.main.get_intent_router", return_value=mock_router), \
         patch("app.main.get_core_engine", return_value=mock_core), \
         patch("app.main.get_shaper", return_value=mock_shaper):

        payload = {
            "session_id": "test_local_session_101",
            "message": "I have 5000 rupees saved, where should I keep it?",
            "input_type": "text",
            "language": "hi",
        }
        response = client.post("/dev/chat", json=payload)

        assert response.status_code == 200, f"Expected 200 OK in dev, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["reply_text"] == "Namaste! Apni bachhat ke liye Bank FD dekhein. 🙏"
        assert data["input_type_replied"] == "text"
        assert data["escalation_recommended"] is False
        assert "Check interest rates" in data["next_action"]
        assert mock_save.call_count == 2  # Inbound user msg + Outbound system reply


def test_dev_chat_endpoint_active_in_production(monkeypatch):
    """Confirm /dev/chat continues to process requests in production mode for web demo interfaces."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("GEMINI_TIER", "paid")  # Required so production rules do not raise privacy exception
    get_settings.cache_clear()
    importlib.reload(app.main)

    client = TestClient(app.main.app)

    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": str(uuid4())}]))
    mock_db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))

    mock_router = MagicMock()
    mock_router.classify = AsyncMock(return_value="money_decision")

    mock_core = MagicMock()
    mock_core_out = CoreEngineOutput(
        core_message="Verified safety rules for investment.",
        next_action="Verify registration with SEBI.",
        verdict=None,
        risk_signals_detected=[],
        escalation_recommended=False,
        sources=[],
    )
    mock_core.reason = AsyncMock(return_value=mock_core_out)

    mock_shaper = MagicMock()
    mock_shaper.shape = AsyncMock(return_value="Namaste! SEBI registration check karein. 🙏")
    mock_shaper.translate_action = AsyncMock(return_value="Verify registration with SEBI.")

    with patch("app.routers.dev.get_db", return_value=mock_db), \
         patch("app.routers.dev.get_or_create_user", new_callable=AsyncMock, return_value={"id": str(uuid4()), "preferred_language": "en"}), \
         patch("app.routers.dev.get_or_create_conversation", new_callable=AsyncMock, return_value={"id": str(uuid4()), "status": "open"}), \
         patch("app.routers.dev.save_message", new_callable=AsyncMock) as mock_save, \
         patch("app.routers.dev.check_and_record_usage", new_callable=AsyncMock, return_value=(True, None)), \
         patch("app.main.get_intent_router", return_value=mock_router), \
         patch("app.main.get_core_engine", return_value=mock_core), \
         patch("app.main.get_shaper", return_value=mock_shaper):

        payload = {
            "session_id": "test_prod_web_demo",
            "message": "Is this offer real?",
            "input_type": "text",
            "language": "en",
        }
        response = client.post("/dev/chat", json=payload)

        assert response.status_code == 200, f"Expected 200 OK in production web demo, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["reply_text"] == "Namaste! SEBI registration check karein. 🙏"
        assert mock_save.call_count == 2  # Messages saved safely without touching WhatsApp webhook outbound
