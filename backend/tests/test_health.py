"""Tests for API health endpoints."""

from fastapi.testclient import TestClient
from unittest.mock import patch


def test_root_endpoint(client: TestClient):
    """Test GET / returns service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


@patch("backend.routes.health.check_db_connectivity")
def test_health_endpoint(mock_check_db, client: TestClient):
    """Test GET /health returns successful status and database connectivity info."""
    mock_check_db.return_value = {
        "status": "CONNECTED",
        "engine": "sqlite",
        "supabase_configured": False,
        "details": "Database connection successful (mocked)",
    }
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "engine" in data["database"]
    assert "supabase_configured" in data["database"]
