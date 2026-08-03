"""
tests/test_internal_api.py — Unit tests for Phase 4 Internal API and authentication.

Verifies:
  - POST /internal/escalate requires valid service token
  - GET /internal/escalations requires valid Bearer token with appropriate role
  - Audit logging is invoked upon viewing escalation queue
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app, get_settings


@pytest.fixture
def test_settings():
    return Settings(
        environment="development",
        internal_service_token="test_service_secret",
        supabase_url="https://dummy.supabase.co",
        supabase_service_role_key="dummy_role_key",
        supabase_anon_key="dummy_anon_key",
        gemini_api_key="AIzaSyDummyTestKey1234567890",
    )


def test_escalation_endpoint_unauthorized():
    """Test that POST /internal/escalate fails without service token."""
    client = TestClient(app)
    payload = {
        "conversation_id": str(uuid4()),
        "reason": "keyword",
        "risk_signals": ["suicide_threat"],
    }
    response = client.post("/internal/escalate", json=payload)
    assert response.status_code == 401
    assert "Invalid or missing service token" in response.text


def test_escalation_endpoint_success(test_settings):
    """Test that POST /internal/escalate succeeds with service token."""
    app.dependency_overrides[get_settings] = lambda: test_settings

    mock_db = MagicMock()
    mock_record = {"id": str(uuid4())}
    with patch("app.db.client.get_db", return_value=mock_db), \
         patch("app.services.escalation.create_escalation", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = mock_record
        client = TestClient(app)
        headers = {"Authorization": "Bearer test_service_secret"}
        payload = {
            "conversation_id": str(uuid4()),
            "reason": "keyword",
            "risk_signals": ["suicide_threat"],
        }
        response = client.post("/internal/escalate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["escalation_id"] == mock_record["id"]
        assert data["status"] == "pending"

    app.dependency_overrides.clear()


def test_list_escalations_unauthorized():
    """Test that GET /internal/escalations fails without authentication."""
    client = TestClient(app)
    response = client.get("/internal/escalations")
    assert response.status_code == 401
    assert "Missing authentication token" in response.text


def test_list_escalations_success_with_service_token(test_settings):
    """Test that GET /internal/escalations succeeds when using service token as team_member."""
    app.dependency_overrides[get_settings] = lambda: test_settings

    mock_db = MagicMock()
    mock_execute = MagicMock(data=[{"id": str(uuid4()), "status": "pending", "reason": "llm_flag"}])
    mock_db.table.return_value.select.return_value.order.return_value.execute = AsyncMock(return_value=mock_execute)

    with patch("app.db.client.get_db", return_value=mock_db), \
         patch("app.services.audit.write_audit_log", new_callable=AsyncMock) as mock_audit:
        
        client = TestClient(app)
        headers = {"Authorization": "Bearer test_service_secret"}
        response = client.get("/internal/escalations", headers=headers)
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["status"] == "pending"
        assert mock_audit.called
        # Confirm audit log actions
        call_kwargs = mock_audit.call_args[1] if mock_audit.call_args[1] else mock_audit.call_args[0]
        assert "viewed_escalation_queue" in str(mock_audit.call_args)

    app.dependency_overrides.clear()
