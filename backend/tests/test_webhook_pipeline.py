"""
tests/test_webhook_pipeline.py — End-to-end unit tests for Phase 2 Webhook Pipeline Orchestrator.

Verifies:
  - Intent classification routing -> Core Engine reasoning -> Shaper formatting
  - Separate database column storage for core_engine_output and shaped_response
  - Unconditional Risk/Distress gate triggering during conversation
  - Safe fallback when LLM engines encounter network faults or unconfigured keys
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.config import Settings
from app.routers.webhook import _process_webhook_payload
from app.schemas.core_engine import CoreEngineOutput


@pytest.fixture
def mock_settings() -> Settings:
    # Use dummy valid settings for testing
    return Settings(
        environment="development",
        groq_api_key="gsk_DummyTestKey1234567890",
        supabase_url="https://dummy.supabase.co",
        supabase_service_role_key="dummy_role_key",
        supabase_anon_key="dummy_anon_key",
        whatsapp_access_token="dummy_token",
    )


@pytest.fixture
def sample_whatsapp_payload() -> bytes:
    data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919999999999",
                                "phone_number_id": "123456123",
                            },
                            "messages": [
                                {
                                    "from": "919876543210",
                                    "id": "wamid.HBgLOTE5ODc2NTQzMjEwVhhQOghI",
                                    "timestamp": "1678901234",
                                    "text": {"body": "Should I invest 10,000 rupees in this scheme?"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    return json.dumps(data).encode("utf-8")


@pytest.mark.asyncio
async def test_phase2_webhook_orchestrator_success(sample_whatsapp_payload, mock_settings):
    """Test full Phase 2 execution flow (Groq pipeline) when messages arrive."""
    # Mock database and session calls
    mock_db = MagicMock()
    mock_db.table.return_value.insert.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"id": str(uuid4())}]))
    mock_db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))
    
    # Mock LLM Engines
    mock_router = MagicMock()
    mock_router.classify = AsyncMock(return_value="money_decision")

    mock_core = MagicMock()
    mock_core_out = CoreEngineOutput(
        core_message="Consider low-risk index funds or fixed deposit.",
        next_action="Compare FD interest rates.",
        verdict=None,
        risk_signals_detected=[],
        escalation_recommended=False,
        sources=[],
    )
    mock_core.reason = AsyncMock(return_value=mock_core_out)

    mock_shaper = MagicMock()
    mock_shaper.shape = AsyncMock(return_value="Namaste! 10,000 rupaye invest karne ke liye FD ya Post Office scheme dekhein. 🙏")

    mock_whatsapp = MagicMock()
    mock_whatsapp.send_text = AsyncMock(return_value=None)
    
    mock_http_client = MagicMock(spec=AsyncClient)

    with patch("app.routers.webhook.get_db", return_value=mock_db), \
         patch("app.routers.webhook.get_or_create_user", new_callable=AsyncMock) as mock_user, \
         patch("app.routers.webhook.get_or_create_conversation", new_callable=AsyncMock) as mock_conv, \
         patch("app.routers.webhook.save_message", new_callable=AsyncMock) as mock_save, \
         patch("app.main.get_intent_router", return_value=mock_router), \
         patch("app.main.get_core_engine", return_value=mock_core), \
         patch("app.main.get_shaper", return_value=mock_shaper), \
         patch("app.main.get_whatsapp_client", return_value=mock_whatsapp), \
         patch("app.main.get_http_client", return_value=mock_http_client):
        
        mock_user.return_value = {"id": str(uuid4()), "preferred_language": "hi"}
        mock_conv.return_value = {"id": str(uuid4()), "status": "open"}

        # Perform execution
        await _process_webhook_payload(sample_whatsapp_payload, mock_settings)

        # 1. Assert IntentRouter classified the input
        mock_router.classify.assert_called_once_with("Should I invest 10,000 rupees in this scheme?")

        # 2. Assert CoreEngine reason called with text + intent and optional RAG context
        assert mock_core.reason.call_count == 1
        call_args, call_kwargs = mock_core.reason.call_args
        assert call_args == ("Should I invest 10,000 rupees in this scheme?", "money_decision")
        assert "rag_context" in call_kwargs

        # 3. Assert Shaper called with target language
        mock_shaper.shape.assert_called_once_with(mock_core_out, target_language="hinglish", input_type="text")

        # 4. Assert WhatsApp reply was attempted
        mock_whatsapp.send_text.assert_called_once()
        sent_reply = mock_whatsapp.send_text.call_args[0][1]
        assert "Namaste! 10,000 rupaye invest" in sent_reply

        # 5. Assert save_message stored BOTH inbound user message AND outbound system reply
        assert mock_save.call_count == 2
        
        # Verify outbound save has SEPARATE core_engine_output and shaped_response columns
        outbound_call = mock_save.call_args_list[1][1]
        assert outbound_call["sender"] == "system"
        assert outbound_call["core_engine_output"] == mock_core_out.model_dump()
        assert outbound_call["shaped_response"] == {
            "text": sent_reply,
            "language": "hinglish",
            "intent": "money_decision",
        }


@pytest.mark.asyncio
async def test_phase2_fallback_when_gemini_fails(sample_whatsapp_payload, mock_settings):
    """Test safe fallback to keyword reply if Gemini API call throws network exception."""
    mock_db = MagicMock()
    mock_router = MagicMock()
    mock_router.classify = AsyncMock(side_effect=Exception("Google Gemini API Timeout / Quota exceeded"))

    mock_whatsapp = MagicMock()
    mock_whatsapp.send_text = AsyncMock(return_value=None)

    with patch("app.routers.webhook.get_db", return_value=mock_db), \
         patch("app.routers.webhook.get_or_create_user", new_callable=AsyncMock, return_value={"id": str(uuid4())}), \
         patch("app.routers.webhook.get_or_create_conversation", new_callable=AsyncMock, return_value={"id": str(uuid4()), "status": "open"}), \
         patch("app.routers.webhook.save_message", new_callable=AsyncMock) as mock_save, \
         patch("app.main.get_intent_router", return_value=mock_router), \
         patch("app.main.get_core_engine", return_value=MagicMock()), \
         patch("app.main.get_shaper", return_value=MagicMock()), \
         patch("app.main.get_whatsapp_client", return_value=mock_whatsapp), \
         patch("app.main.get_http_client", return_value=MagicMock(spec=AsyncClient)):

        # Should never raise exception
        await _process_webhook_payload(sample_whatsapp_payload, mock_settings)

        # Ensure outbound message fallback occurred safely
        assert mock_save.call_count == 2
        outbound_call = mock_save.call_args_list[1][1]
        assert "Got your financial question!" in outbound_call["message_text"]
        assert outbound_call.get("core_engine_output") is None
