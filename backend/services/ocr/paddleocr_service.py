"""PaddleOCR implementation service with graceful error handling and safe empty review state."""

import logging
from typing import List, Optional
from backend.services.ocr.base import BaseOCRService, OCRResult, OCRBlock

logger = logging.getLogger(__name__)


class PaddleOCRService(BaseOCRService):
    """PaddleOCR service wrapper."""

    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self._ocr_instance = None
        self._initialized = False

    def _get_engine(self):
        """Lazy initialization of PaddleOCR instance."""
        if not self._initialized:
            try:
                from paddleocr import PaddleOCR
                self._ocr_instance = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang, show_log=False)
                logger.info("PaddleOCR engine initialized successfully.")
            except Exception as exc:
                logger.warning(f"Could not initialize PaddleOCR engine: {exc}")
                self._ocr_instance = None
            self._initialized = True
        return self._ocr_instance

    def extract_text(self, image_bytes: bytes) -> OCRResult:
        """Extract text from image bytes using PaddleOCR."""
        ocr = self._get_engine()
        blocks: List[OCRBlock] = []
        raw_lines: List[str] = []
        confidences: List[float] = []

        if ocr is not None:
            try:
                import numpy as np
                import cv2

                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is None:
                    raise ValueError("Failed to decode image bytes for OCR.")

                result = ocr.ocr(img, cls=self.use_angle_cls)
                if result and result[0]:
                    for line in result[0]:
                        box = line[0]
                        text_conf = line[1]
                        txt = text_conf[0]
                        conf = float(text_conf[1])
                        raw_lines.append(txt)
                        confidences.append(conf)
                        blocks.append(OCRBlock(text=txt, confidence=conf, box=box))
            except Exception as exc:
                logger.error(f"PaddleOCR execution error: {exc}")

        if not raw_lines:
            logger.warning("OCR engine returned no text or is unavailable. Returning empty OCR result (safe REVIEW state).")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                blocks=[],
                provider="paddleocr",
                model="failed-or-empty",
            )

        raw_text = "\n".join(raw_lines)
        avg_confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0

        return OCRResult(
            raw_text=raw_text,
            confidence=round(avg_confidence * 100.0, 2),
            blocks=blocks,
            provider="paddleocr",
            model="PP-OCRv4",
        )


def get_ocr_service() -> BaseOCRService:
    """Factory function to get OCR service instance."""
    return PaddleOCRService()
