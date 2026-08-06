-- 002_scam_kb_match.sql — Phase 3 RAG Similarity Search & Migration
--
-- 1. Ensure embedding vector column matches Gemini models/text-embedding-004 (768 dimensions).
-- 2. Create RPC function for pgvector similarity searches over Supabase client.

-- Alter embedding column type if table already existed with 1536 dimensions
DO $$
BEGIN
    ALTER TABLE scam_kb_cards ALTER COLUMN embedding TYPE VECTOR(768);
EXCEPTION
    WHEN undefined_table THEN
        -- Table doesn't exist yet, 001_initial.sql will create it properly
        NULL;
    WHEN others THEN
        NULL;
END $$;

-- RPC Function: match_scam_cards
-- Called from app.services.rag via db.rpc("match_scam_cards", {...})
-- Returns matching scam pattern cards ordered by cosine similarity.
CREATE OR REPLACE FUNCTION match_scam_cards(
    query_embedding VECTOR(768),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 3
)
RETURNS TABLE (
    id UUID,
    pattern_name TEXT,
    description TEXT,
    example_phrasing TEXT,
    source TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        skc.id,
        skc.pattern_name,
        skc.description,
        skc.example_phrasing,
        skc.source,
        (1 - (skc.embedding <=> query_embedding))::FLOAT AS similarity
    FROM scam_kb_cards skc
    WHERE skc.embedding IS NOT NULL
      AND (1 - (skc.embedding <=> query_embedding)) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
END;
$$;
