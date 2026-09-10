"""Tests for multi-image inspection scans, evidence combination, and conflict resolution."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy.orm import Session

from backend.models.entities import Inspection, InspectionImage, ExtractedData
from backend.services.extraction import combine_label_extractions


@patch("backend.routes.inspections.upload_inspection_image")
@patch("backend.routes.inspections.get_signed_url")
def test_multi_image_scan_success(mock_get_signed_url, mock_upload, client: TestClient, auth_headers: dict):
    """Test POST /api/v1/inspections/scan with multiple images for one inspection."""
    mock_upload.side_effect = [
        {"storage_path": "inspections/folder1/img1.jpg", "bucket": "inspection-images", "size_bytes": 500},
        {"storage_path": "inspections/folder1/img2.jpg", "bucket": "inspection-images", "size_bytes": 600},
    ]
    mock_get_signed_url.return_value = "https://example.com/signed.jpg"

    response = client.post(
        "/api/v1/inspections/scan",
        files=[
            ("images", ("img1.jpg", b"image1-bytes", "image/jpeg")),
            ("images", ("img2.jpg", b"image2-bytes", "image/jpeg")),
        ],
        data={"ocr_text": "Good Bakes Cookies\nMRP: ₹ 100\nNet Qty: 200 g"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "REVIEW"


def test_combine_extractions_with_conflicts():
    """Test evidence combination and conflict detection across multiple images."""
    ext1 = {
        "product_name": "Cookies",
        "mrp": "MRP ₹ 120",
        "net_quantity": "200 g",
        "field_details": {
            "mrp": {"value": "MRP ₹ 120", "confidence": 95.0, "status": "CONFIDENT"},
            "net_quantity": {"value": "200 g", "confidence": 90.0, "status": "CONFIDENT"},
        }
    }
    ext2 = {
        "product_name": "Cookies",
        "mrp": "MRP ₹ 150",
        "net_quantity": "200 g",
        "field_details": {
            "mrp": {"value": "MRP ₹ 150", "confidence": 90.0, "status": "CONFIDENT"},
            "net_quantity": {"value": "200 g", "confidence": 90.0, "status": "CONFIDENT"},
        }
    }

    combined = combine_label_extractions([ext1, ext2])
    assert combined["mrp"] is None
    assert combined["field_details"]["mrp"]["status"] == "AMBIGUOUS"
    assert combined["net_quantity"] == "200 g"
    assert combined["field_details"]["net_quantity"]["status"] == "CONFIDENT"
