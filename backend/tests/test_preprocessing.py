"""Tests for image preprocessing service."""

import cv2
import numpy as np
from backend.services.preprocessing import preprocess_image


def test_preprocess_valid_image():
    """Test preprocessing a valid generated image."""
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    cv2.putText(img, "Test Label", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    success, encoded = cv2.imencode(".jpg", img)
    assert success

    processed = preprocess_image(encoded.tobytes())
    assert isinstance(processed, bytes)
    assert len(processed) > 0


def test_preprocess_invalid_image():
    """Test preprocessing invalid/corrupted bytes falls back gracefully."""
    bad_bytes = b"not-an-image"
    processed = preprocess_image(bad_bytes)
    assert processed == bad_bytes
