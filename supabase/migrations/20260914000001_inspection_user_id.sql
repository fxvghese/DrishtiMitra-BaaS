-- ==============================================================================
-- Migration: 20260914000001_inspection_user_id.sql
-- Description: Add user_id column to inspections table for ownership and authorization
-- Database: PostgreSQL / Supabase
-- ==============================================================================

ALTER TABLE inspections
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_inspections_user_id ON inspections(user_id);
