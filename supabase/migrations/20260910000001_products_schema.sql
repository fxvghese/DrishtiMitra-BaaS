-- ==============================================================================
-- Migration: 20260910000001_products_schema.sql
-- Description: Add products table and link inspections to products for Phase 2
-- Database: PostgreSQL / Supabase
-- ==============================================================================

-- 1. Table: products
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name TEXT,
    manufacturer TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for products table
CREATE INDEX IF NOT EXISTS idx_products_product_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_manufacturer ON products(manufacturer);

-- 2. Alter inspections table to add product_id
ALTER TABLE inspections
ADD COLUMN IF NOT EXISTS product_id UUID REFERENCES products(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_inspections_product_id ON inspections(product_id);
