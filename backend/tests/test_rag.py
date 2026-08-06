"""
tests/test_rag.py — Unit tests for Phase 3 Scam Pattern RAG Retrieval.

Verifies:
  - Formatting of retrieved scam cards from Supabase pgvector RPC.
  - Safe fallback to default scam warning when DB/embedding is offline or key is dummy.
  - Handling of empty queries without API/DB overhead.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.config import Settings
from app.services.rag import DEFAULT_SCAM_WARNING, retrieve_scam_context


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        environment="development",
        groq_api_key="gsk_DummyTestKey1234567890",
        supabase_url="https://dummy.supabase.co",
    )


@pytest.mark.asyncio
async def test_retrieve_scam_context_fallback(mock_settings):
    """Test safe fallback to DEFAULT_SCAM_WARNING when embedding vector cannot be generated (dummy key)."""
    mock_db = MagicMock()
    
    context = await retrieve_scam_context(mock_db, "Is this chit fund scheme safe?", mock_settings)
    assert context == DEFAULT_SCAM_WARNING


@pytest.mark.asyncio
async def test_retrieve_scam_context_empty_text(mock_settings):
    """Test that empty or whitespace text immediately returns None."""
    mock_db = MagicMock()
    
    context = await retrieve_scam_context(mock_db, "   ", mock_settings)
    assert context is None


@pytest.mark.asyncio
async def test_retrieve_scam_context_success(mock_settings):
    """Test successful formatting of scam pattern cards returned by Supabase match_scam_cards RPC."""
    mock_db = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": "abc-123",
            "pattern_name": "Unregulated Chit Fund",
            "description": "Unregistered entities asking for recurring deposits with 40% return promises.",
            "example_phrasing": "Double money in 6 months; committee prize.",
            "source": "RBI Investor Advisory",
            "similarity": 0.885,
        },
        {
            "id": "def-456",
            "pattern_name": "Predatory Digital Lending",
            "description": "Unauthorized instant apps harvesting phone contacts to harass borrowers.",
            "example_phrasing": "Instant KYC free loan in 5 min.",
            "source": "RBI Digital Lending Working Group",
            "similarity": 0.723,
        }
    ]
    mock_db.rpc.return_value.execute = AsyncMock(return_value=mock_response)

    with patch("app.services.rag.generate_embedding", new_callable=AsyncMock) as mock_embed:
        # Simulate successful 768-dim vector from Gemini embedding
        mock_embed.return_value = [0.1] * 768

        context = await retrieve_scam_context(mock_db, "Tell me about this chit fund committee loan", mock_settings)

        assert context is not None
        assert "--- SCAM PATTERN #1 (Match: 88.5%) ---" in context
        assert "Pattern: Unregulated Chit Fund" in context
        assert "Source Authority: RBI Investor Advisory" in context
        assert "--- SCAM PATTERN #2 (Match: 72.3%) ---" in context
        assert "Pattern: Predatory Digital Lending" in context
        
        # Ensure correct RPC call was executed
        mock_db.rpc.assert_called_once_with(
            "match_scam_cards",
            {
                "query_embedding": [0.1] * 768,
                "match_threshold": 0.4,
                "match_count": 3,
            }
        )
