-- DocFlow database initialization
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- for fuzzy vendor matching

-- Confirm extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');
