"""Tests for OCR text normalization layer."""

from backend.services.extraction.label_extractor import normalize_ocr_text, extract_label_fields


def test_normalize_ocr_text_artifacts():
    """Test normalizing various OCR formatting artifacts."""
    raw = "NetQty:1kg\nMRP₹120\nRs.120\n500g"
    normalized = normalize_ocr_text(raw)
    assert "Net Qty: 1 kg" in normalized
    assert "500 g" in normalized


def test_extraction_field_status_and_confidence():
    """Test field extraction returns confidence and status details."""
    raw = "Good Bakes Cookies\nNet Qty: 250 g\nMRP: ₹90"
    fields = extract_label_fields(raw)
    assert "field_details" in fields
    assert fields["field_details"]["mrp"]["status"] == "CONFIDENT"
    assert fields["field_details"]["net_quantity"]["confidence"] == 90.0
