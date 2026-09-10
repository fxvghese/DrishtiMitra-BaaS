"""Tests for OCR service abstraction and safe empty review state."""

from backend.services.ocr.paddleocr_service import PaddleOCRService
from backend.services.ocr.base import OCRResult


def test_ocr_service_safe_empty_result():
    """Test OCR service returns safe empty result when engine is uninitialized/empty."""
    service = PaddleOCRService()
    dummy_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    result = service.extract_text(dummy_bytes)
    assert isinstance(result, OCRResult)
    assert result.raw_text == ""
    assert result.confidence == 0.0
    assert result.provider == "paddleocr"
    assert result.model == "failed-or-empty"
