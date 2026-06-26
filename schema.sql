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
    message_content TEXT NOT NULL DEFAULT '',
    UNIQUE (original_message_url, url)
);

-- Ensure column exists on older tables that pre-date this field
ALTER TABLE tracked_media ADD COLUMN IF NOT EXISTS message_content TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_title_trgm ON tracked_media USING gin (lower(title) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_uploader_trgm ON tracked_media USING gin (lower(uploader) gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_content_trgm ON tracked_media USING gin (lower(message_content) gin_trgm_ops);