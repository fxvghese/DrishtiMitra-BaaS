"""Image preprocessing service for label OCR enhancement."""

import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def preprocess_image(image_bytes: bytes) -> bytes:
    """Preprocess image bytes for optimal OCR recognition.

    Operations:
        1. Decode image.
        2. Resize if resolution is too small.
        3. Denoise and enhance contrast (CLAHE).
        4. Encode back to JPEG bytes.
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            logger.warning("Failed to decode image for preprocessing; returning original bytes.")
            return image_bytes

        h, w = img.shape[:2]

        min_dim = min(h, w)
        if min_dim < 800 and min_dim > 0:
            scale = 800.0 / min_dim
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            h, w = new_h, new_w
            logger.info(f"Resized image for OCR to {w}x{h}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
        processed_bgr = cv2.cvtColor(denoised, cv2.COLOR_GRAY2BGR)

        success, encoded_img = cv2.imencode(".jpg", processed_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if not success:
            return image_bytes

        return encoded_img.tobytes()

    except Exception as exc:
        logger.error(f"Image preprocessing failed: {exc}; falling back to original image bytes.")
        return image_bytes
