"""OCR package exports."""

from backend.services.ocr.base import BaseOCRService, OCRResult, OCRBlock
from backend.services.ocr.paddleocr_service import PaddleOCRService, get_ocr_service

__all__ = [
    "BaseOCRService",
    "OCRResult",
    "OCRBlock",
    "PaddleOCRService",
    "get_ocr_service",
]
