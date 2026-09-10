-- ==============================================================================
-- Migration: 20260912000001_inspection_images.sql
-- Description: Create inspection_images table to support multiple images per inspection
-- Database: PostgreSQL / Supabase
-- ==============================================================================

CREATE TABLE IF NOT EXISTS inspection_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id UUID NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    sequence INTEGER NOT NULL DEFAULT 0,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for inspection_images table
CREATE INDEX IF NOT EXISTS idx_inspection_images_inspection_id ON inspection_images(inspection_id);
