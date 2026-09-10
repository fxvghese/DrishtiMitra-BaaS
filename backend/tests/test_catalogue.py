"""Tests for Phase 5B Reference Product Catalogue, Importers, and Search."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.entities import ReferenceProduct, Inspection, ExtractedData
from backend.services.catalogue import search_reference_catalogue
from backend.rules import evaluate_inspection


def test_create_and_search_reference_product(db_session: Session):
    """Test creating and searching reference products."""
    ref = ReferenceProduct(
        source="open_food_facts",
        external_id="123456789",
        product_name="Organic Whole Milk",
        brand="Amul",
        category="Dairy",
        quantity="1 L",
        mrp=65.00,
    )
    db_session.add(ref)
    db_session.commit()

    matches = search_reference_catalogue(db_session, "Organic Whole Milk")
    assert len(matches) > 0
    assert matches[0]["product_name"] == "Organic Whole Milk"
    assert matches[0]["brand"] == "Amul"


def test_catalogue_search_api(client: TestClient, db_session: Session):
    """Test GET /api/v1/catalogue/search endpoint."""
    ref = ReferenceProduct(
        source="flipkart",
        external_id="fk_123",
        product_name="Wireless Bluetooth Headphones",
        brand="Boat",
        category="Electronics",
        mrp=1499.00,
    )
    db_session.add(ref)
    db_session.commit()

    response = client.get("/api/v1/catalogue/search?q=Headphones")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0
    assert data["data"][0]["product_name"] == "Wireless Bluetooth Headphones"


def test_reference_mrp_discrepancy_does_not_override_compliance(db_session: Session):
    """Test that reference MRP discrepancy does not automatically force non-compliant legal result."""
    ref = ReferenceProduct(
        source="open_food_facts",
        external_id="987654",
        product_name="Biscuit",
        brand="Sunfeast",
        mrp=30.00,
    )
    db_session.add(ref)
    db_session.commit()

    inspection = Inspection(image_url="test.jpg")
    db_session.add(inspection)
    db_session.commit()

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Biscuit",
        manufacturer="ITC Ltd, Kolkata",
        net_quantity="100 g",
        mrp="Rs. 40",
        date="07/2026",
    )
    db_session.add(extracted)
    db_session.commit()

    summary = evaluate_inspection(db_session, str(inspection.id))
    assert summary.overall_status == "COMPLIANT"
