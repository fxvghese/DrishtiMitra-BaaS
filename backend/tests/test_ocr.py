"""Tests for OCR service abstraction and fallback."""

from backend.services.ocr.paddleocr_service import PaddleOCRService
from backend.services.ocr.base import OCRResult


def test_ocr_service_fallback():
    """Test OCR service fallback when engine is not initialized or fails."""
    service = PaddleOCRService()
    dummy_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    result = service.extract_text(dummy_bytes)
    assert isinstance(result, OCRResult)
    assert result.raw_text is not None
    assert len(result.raw_text) > 0
    assert result.provider == "paddleocr"
    assert result.confidence > 0.0
