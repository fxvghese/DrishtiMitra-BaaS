"""Supabase Storage service for inspection label images.

Responsibilities:
    - Upload an image file to the 'inspection-images' bucket.
    - Generate a signed URL so the image can be retrieved privately.
    - Delete an image when an inspection is removed.

This service wraps the Supabase Storage SDK.  It does NOT perform OCR or
image analysis — that is the responsibility of the OCR service (Phase 2).
"""

import logging
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

from supabase import Client

from backend.database.config import get_settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "inspection-images"
SIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour


def _get_storage_client() -> Client:
    """Return a Supabase client authenticated with the service role key.

    The service role key bypasses RLS and is required for server-side
    storage operations (upload, delete, signed URL generation).

    Raises:
        RuntimeError: If Supabase storage credentials are not configured.
    """
    settings = get_settings()
    if not settings.is_storage_configured:
        raise RuntimeError(
            "Supabase service role key is not configured. "
            "Set SUPABASE_SERVICE_KEY in your .env file. "
            "Get it from: Supabase Dashboard → Project Settings → API → service_role."
        )
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


def upload_inspection_image(
    file_bytes: bytes,
    original_filename: str,
    inspection_id: Optional[str] = None,
) -> dict:
    """Upload a label image to the inspection-images bucket.

    The object is stored at:
        inspections/<inspection_id>/<uuid>.<ext>

    Args:
        file_bytes:        Raw image bytes.
        original_filename: Original filename from the upload (used for extension).
        inspection_id:     Optional inspection UUID to use in the storage path.
                           If not provided, a new UUID is generated.

    Returns:
        dict with keys:
            storage_path (str): Full object path inside the bucket.
            bucket (str):       Bucket name.
            size_bytes (int):   Upload size in bytes.

    Raises:
        ValueError: If the MIME type is not an allowed image type.
        RuntimeError: On Supabase upload failure.
    """
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    mime_type, _ = mimetypes.guess_type(original_filename)
    if not mime_type or mime_type not in allowed_types:
        raise ValueError(
            f"Unsupported file type '{mime_type}'. "
            f"Allowed types: {', '.join(sorted(allowed_types))}"
        )

    ext = Path(original_filename).suffix.lower() or ".jpg"
    folder = str(inspection_id) if inspection_id else str(uuid.uuid4())
    object_name = f"{uuid.uuid4()}{ext}"
    storage_path = f"inspections/{folder}/{object_name}"

    client = _get_storage_client()

    try:
        client.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": mime_type, "upsert": "false"},
        )
        logger.info(f"Uploaded inspection image: {storage_path} ({len(file_bytes)} bytes)")
    except Exception as exc:
        logger.error(f"Failed to upload image to Supabase Storage: {exc}")
        raise RuntimeError(f"Image upload failed: {exc}") from exc

    return {
        "storage_path": storage_path,
        "bucket": BUCKET_NAME,
        "size_bytes": len(file_bytes),
    }


def get_signed_url(storage_path: str, expiry_seconds: int = SIGNED_URL_EXPIRY_SECONDS) -> str:
    """Generate a temporary signed URL for a private bucket object.

    Args:
        storage_path:   Full object path inside the bucket.
        expiry_seconds: URL validity in seconds (default: 1 hour).

    Returns:
        Signed URL string.

    Raises:
        RuntimeError: If the signed URL cannot be generated.
    """
    client = _get_storage_client()
    try:
        response = client.storage.from_(BUCKET_NAME).create_signed_url(
            path=storage_path,
            expires_in=expiry_seconds,
        )
        signed_url: str = response.get("signedURL") or response.get("signed_url", "")
        if not signed_url:
            raise RuntimeError("Supabase returned an empty signed URL.")
        return signed_url
    except Exception as exc:
        logger.error(f"Failed to create signed URL for '{storage_path}': {exc}")
        raise RuntimeError(f"Signed URL generation failed: {exc}") from exc


def delete_inspection_image(storage_path: str) -> None:
    """Delete an image object from the bucket.

    Args:
        storage_path: Full object path inside the bucket.

    Raises:
        RuntimeError: On Supabase deletion failure.
    """
    client = _get_storage_client()
    try:
        client.storage.from_(BUCKET_NAME).remove([storage_path])
        logger.info(f"Deleted inspection image: {storage_path}")
    except Exception as exc:
        logger.error(f"Failed to delete image '{storage_path}': {exc}")
        raise RuntimeError(f"Image deletion failed: {exc}") from exc
