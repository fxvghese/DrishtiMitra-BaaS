"""Tests for inspection scan API endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@patch("backend.routes.inspections.upload_inspection_image")
@patch("backend.routes.inspections.get_signed_url")
def test_scan_label_endpoint_success(mock_get_signed_url, mock_upload, client: TestClient, auth_headers: dict):
    """Test POST /api/v1/inspections/scan processes valid image upload successfully."""
    mock_upload.return_value = {
        "storage_path": "inspections/test-folder/test-label.jpg",
        "bucket": "inspection-images",
        "size_bytes": 1024,
    }
    mock_get_signed_url.return_value = "https://example.com/signed-url.jpg"

    image_bytes = b"fake-image-content"
    response = client.post(
        "/api/v1/inspections/scan",
        files={"image": ("label.jpg", image_bytes, "image/jpeg")},
        data={"ocr_text": "Good Bakes Cookies\nNet Qty: 200g\nMRP: Rs. 50"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    scan_data = data["data"]
    assert scan_data["status"] == "REVIEW"
    assert scan_data["image_url"] == "https://example.com/signed-url.jpg"
    assert scan_data["extracted_data"]["net_quantity"] == "Net Qty: 200 g"
    assert scan_data["extracted_data"]["mrp"] == "MRP: Rs. 50"


def test_scan_label_endpoint_missing_image(client: TestClient, auth_headers: dict):
    """Test scan endpoint returns 400 when image is missing."""
    response = client.post(
        "/api/v1/inspections/scan",
        headers=auth_headers,
    )
    assert response.status_code == 400
