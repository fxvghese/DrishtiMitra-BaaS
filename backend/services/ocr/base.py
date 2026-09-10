"""OCR Service base abstract interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OCRBlock(BaseModel):
    """Structured representation of an OCR text block or line."""
    text: str
    confidence: float
    box: Optional[List[List[float]]] = None


class OCRResult(BaseModel):
    """Structured OCR output containing raw text, confidence, blocks, and provider metadata."""
    raw_text: str
    confidence: float
    blocks: List[OCRBlock] = []
    provider: str
    model: str = "default"


class BaseOCRService(ABC):
    """Abstract base class for OCR engines."""

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """Process image bytes and return structured OCR result."""
        pass
