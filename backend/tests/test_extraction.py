"""Tests for label extraction and field normalization service."""

from backend.services.extraction.label_extractor import extract_label_fields


def test_extract_label_fields_from_raw_text():
    """Test extracting fields from messy raw OCR text."""
    raw_text = """
    Aashirvaad Whole Wheat Atta
    Net Qty: 5 kg
    MRP ₹ 245.00 incl. of all taxes
    Mfg By: ITC Limited, Kolkata
    Pkd 06/2026
    Consumer Care: support@itc.in
    """
    fields = extract_label_fields(raw_text)
    assert fields["product_name"] == "Aashirvaad Whole Wheat Atta"
    assert "5 kg" in fields["net_quantity"]
    assert "245.00" in fields["mrp"]
    assert "ITC Limited" in fields["manufacturer"]
    assert "06/2026" in fields["date"]
    assert "support@itc.in" in fields["consumer_care"]


def test_extract_label_fields_with_client_hints():
    """Test that client-provided fields override or supplement OCR extraction."""
    raw_text = "Some random OCR text"
    hints = {
        "product_name": "Custom Product",
        "mrp": "Rs. 100",
    }
    fields = extract_label_fields(raw_text, client_fields=hints)
    assert fields["product_name"] == "Custom Product"
    assert fields["mrp"] == "Rs. 100"
