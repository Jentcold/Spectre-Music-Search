-- Load trigram extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create media table
CREATE TABLE IF NOT EXISTS tracked_media (
    id SERIAL PRIMARY KEY,
    asset_type VARCHAR(50) NOT NULL, -- 'STREAM', 'YOUTUBE', 'FILE'
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    uploader VARCHAR(255) NOT NULL,
    date_shared DATE NOT NULL,
    original_message_url TEXT NOT NULL,
    channel_id BIGINT NOT NULL,
    UNIQUE (original_message_url, url)
);

-- 3. Composite GIN index on lower(title) for both fuzzy similarity AND substring (ILIKE) matching
CREATE INDEX IF NOT EXISTS idx_title_trgm ON tracked_media USING gin (lower(title) gin_trgm_ops);

-- 4. GIN index on lower(uploader) to keep user searches optimized under the fallback system
CREATE INDEX IF NOT EXISTS idx_uploader_trgm ON tracked_media USING gin (lower(uploader) gin_trgm_ops);