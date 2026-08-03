"""
app/services/rag.py — RAG Layer & Scam Pattern Retrieval (Phase 3).

Retrieves relevant financial scam patterns from Supabase pgvector during
'trust_check' conversations.

Architecture Spec §4.6:
  - Retrieves chunked scam cards (name, description, phrasing, source citation).
  - Uses cosine similarity thresholding via Supabase RPC `match_scam_cards`.
  - Guaranteed exception-safe: database timeouts return None so Core Engine
    reasoning can still proceed without failing the user.

Phase 3 Note: Vector embedding requires an embeddings provider.
Until a Groq-compatible embedding model is configured, retrieve_scam_context
returns DEFAULT_SCAM_WARNING as a safe static fallback for trust_check intents.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.config import Settings

logger = logging.getLogger(__name__)

# Fallback scam warning text if RAG storage is empty or unreachable during a live trust check
DEFAULT_SCAM_WARNING = (
    "Pattern: Generic Financial Fraud / Unverified Scheme\n"
    "Description: Offers promising unrealistic returns, immediate loans without paperwork, "
    "or requiring OTPs/upfront deposit fees are often scams.\n"
    "Source: RBI Financial Awareness Guidelines"
)


async def generate_embedding(text: str, settings: Settings, is_query: bool = True) -> Optional[list[float]]:
    """
    Generate a text embedding vector for pgvector similarity search.

    Phase 3 stub — returns None until a Groq-compatible embedding model
    is configured. retrieve_scam_context handles None gracefully by
    returning DEFAULT_SCAM_WARNING.
    """
    logger.debug("embedding_skipped", extra={"reason": "no_embedding_provider_configured"})
    return None


async def retrieve_scam_context(
    db: Any,
    user_text: str,
    settings: Settings,
    match_threshold: float = 0.4,
    limit: int = 3,
) -> Optional[str]:
    """
    Query Supabase pgvector for similar scam cards using user's text message.

    Args:
        db: Supabase async client instance.
        user_text: Normalized message text from user.
        settings: App configuration settings.
        match_threshold: Cosine similarity cutoff (default 0.4 for conversational flexibility).
        limit: Max scam cards to retrieve (default 3 to fit cleanly in context window).

    Returns:
        Formatted multi-line markdown string of retrieved scam patterns, or None if empty/failed.
    """
    if not user_text.strip():
        return None

    try:
        embedding = await generate_embedding(user_text, settings, is_query=True)
        
        # If API key wasn't live or embedding failed, check if we can query without embedding or return fallback
        if not embedding or not db:
            logger.info("rag_using_fallback_context", extra={"reason": "no_embedding_vector_available"})
            return DEFAULT_SCAM_WARNING

        # Call Supabase RPC match_scam_cards
        response = await db.rpc(
            "match_scam_cards",
            {
                "query_embedding": embedding,
                "match_threshold": match_threshold,
                "match_count": limit,
            },
        ).execute()

        rows = getattr(response, "data", None) or []
        if not rows:
            logger.info("rag_no_matching_scam_cards_found", extra={"query_length": len(user_text)})
            return None

        # Format retrieved cards into structured prompt block
        cards_text = []
        for index, row in enumerate(rows, start=1):
            title = row.get("pattern_name", "Unknown Pattern")
            desc = row.get("description", "No description provided.")
            phrasing = row.get("example_phrasing", "")
            source = row.get("source", "Financial Mitra KB")
            similarity = row.get("similarity", 0.0)

            card_lines = [
                f"--- SCAM PATTERN #{index} (Match: {similarity:.1%}) ---",
                f"Pattern: {title}",
                f"Description: {desc}",
            ]
            if phrasing:
                card_lines.append(f"Common Examples / Red Flags: {phrasing}")
            card_lines.append(f"Source Authority: {source}")
            cards_text.append("\n".join(card_lines))

        combined_context = "\n\n".join(cards_text)
        logger.info("rag_retrieved_scams", extra={"count": len(rows)})
        return combined_context

    except Exception as e:
        logger.error("rag_retrieval_error", extra={"error": str(e)}, exc_info=True)
        # Exception-safe: return default generic scam awareness rather than failing
        return DEFAULT_SCAM_WARNING
