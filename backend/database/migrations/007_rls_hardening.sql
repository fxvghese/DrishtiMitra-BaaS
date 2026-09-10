-- ==============================================================================
-- Migration: 007_rls_hardening.sql
-- Description: Enable Row Level Security (RLS) and define security policies for all tables
-- Database: PostgreSQL / Supabase
-- ==============================================================================

-- 1. Rules Table: Public read-only for authenticated/anon users, no mutations from browser
ALTER TABLE rules ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to rules" ON rules;
CREATE POLICY "Allow public read access to rules"
ON rules FOR SELECT
TO public
USING (true);


-- 2. Products Table: Authenticated users can read/insert products
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow authenticated read access to products" ON products;
CREATE POLICY "Allow authenticated read access to products"
ON products FOR SELECT
TO authenticated
USING (true);

DROP POLICY IF EXISTS "Allow authenticated insert to products" ON products;
CREATE POLICY "Allow authenticated insert to products"
ON products FOR INSERT
TO authenticated
WITH CHECK (true);


-- 3. Inspections Table: Owner-only access based on user_id = auth.uid()
ALTER TABLE inspections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own inspections" ON inspections;
CREATE POLICY "Users can view own inspections"
ON inspections FOR SELECT
TO authenticated
USING (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS "Users can insert own inspections" ON inspections;
CREATE POLICY "Users can insert own inspections"
ON inspections FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS "Users can update own inspections" ON inspections;
CREATE POLICY "Users can update own inspections"
ON inspections FOR UPDATE
TO authenticated
USING (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claim.sub', true))
WITH CHECK (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claim.sub', true));

DROP POLICY IF EXISTS "Users can delete own inspections" ON inspections;
CREATE POLICY "Users can delete own inspections"
ON inspections FOR DELETE
TO authenticated
USING (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claim.sub', true));


-- 4. Inspection Images Table: Access via parent inspection owner
ALTER TABLE inspection_images ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access images of own inspections" ON inspection_images;
CREATE POLICY "Users can access images of own inspections"
ON inspection_images FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = inspection_images.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = inspection_images.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
);


-- 5. Extracted Data Table: Access via parent inspection owner
ALTER TABLE extracted_data ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access extracted data of own inspections" ON extracted_data;
CREATE POLICY "Users can access extracted data of own inspections"
ON extracted_data FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = extracted_data.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = extracted_data.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
);


-- 6. Violations Table: Access via parent inspection owner
ALTER TABLE violations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access violations of own inspections" ON violations;
CREATE POLICY "Users can access violations of own inspections"
ON violations FOR ALL
TO authenticated
USING (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = violations.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM inspections
        WHERE inspections.id = violations.inspection_id
        AND (inspections.user_id = auth.uid()::text OR inspections.user_id = current_setting('request.jwt.claim.sub', true))
    )
);


-- 7. Reference Products Table: Public read-only for authenticated/anon users
ALTER TABLE reference_products ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access to reference products" ON reference_products;
CREATE POLICY "Allow public read access to reference products"
ON reference_products FOR SELECT
TO public
USING (true);
