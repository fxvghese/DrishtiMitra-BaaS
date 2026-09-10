-- ==============================================================================
-- Migration: 20260909000001_storage_bucket.sql
-- Description: Create Supabase Storage bucket for inspection label images
-- ==============================================================================

-- Create the inspection-images storage bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'inspection-images',
    'inspection-images',
    FALSE,                          -- Private: not publicly accessible without a signed URL
    10485760,                       -- 10 MB per file limit
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif']
)
ON CONFLICT (id) DO NOTHING;

-- ------------------------------------------------------------------------------
-- Row Level Security Policies for storage.objects
-- Scope: inspection-images bucket only
-- ------------------------------------------------------------------------------

-- Allow authenticated users to upload images
CREATE POLICY "Authenticated users can upload inspection images"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'inspection-images');

-- Allow authenticated users to read any inspection image
CREATE POLICY "Authenticated users can read inspection images"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'inspection-images');

-- Allow authenticated users to delete their own uploaded images
CREATE POLICY "Authenticated users can delete inspection images"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'inspection-images');
