-- ==============================================================================
-- Migration: 008_unique_source_external_id.sql
-- Description: Add unique constraint on (source, external_id) for reference_products
-- This enables ON CONFLICT (source, external_id) DO UPDATE in the importer
-- ==============================================================================

-- Add unique constraint on (source, external_id) for reference_products
ALTER TABLE reference_products
ADD CONSTRAINT uq_reference_products_source_external_id UNIQUE (source, external_id);