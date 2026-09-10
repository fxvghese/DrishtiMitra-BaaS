"""Tests for authentication and ownership authorization."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.entities import Inspection


def test_scan_missing_auth_header(client: TestClient):
    """Test POST /api/v1/inspections/scan without Authorization header returns 401."""
    response = client.post(
        "/api/v1/inspections/scan",
        files={"image": ("label.jpg", b"fake", "image/jpeg")},
    )
    assert response.status_code == 401


def test_evaluate_unauthorized_owner(client: TestClient, db_session: Session, auth_headers: dict):
    """Test evaluating another user's inspection returns 403 Forbidden."""
    inspection = Inspection(
        image_url="inspections/test/other.jpg",
        user_id="user-owner-999",
    )
    db_session.add(inspection)
    db_session.commit()

    response = client.post(
        f"/api/v1/inspections/{inspection.id}/evaluate",
        headers=auth_headers,
    )
    assert response.status_code == 403
