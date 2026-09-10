-- ==============================================================================
-- Migration: 20260913000001_reference_products.sql
-- Description: Create reference_products table for Phase 5B Reference Catalogue
-- Database: PostgreSQL / Supabase
-- ==============================================================================

CREATE TABLE IF NOT EXISTS reference_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(255),
    product_name TEXT NOT NULL,
    generic_name TEXT,
    brand TEXT,
    category TEXT,
    quantity TEXT,
    mrp NUMERIC(10, 2),
    description TEXT,
    image_url TEXT,
    source_url TEXT,
    metadata TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for reference_products table
CREATE INDEX IF NOT EXISTS idx_reference_products_source ON reference_products(source);
CREATE INDEX IF NOT EXISTS idx_reference_products_external_id ON reference_products(external_id);
CREATE INDEX IF NOT EXISTS idx_reference_products_product_name ON reference_products(product_name);
CREATE INDEX IF NOT EXISTS idx_reference_products_brand ON reference_products(brand);
CREATE INDEX IF NOT EXISTS idx_reference_products_category ON reference_products(category);
