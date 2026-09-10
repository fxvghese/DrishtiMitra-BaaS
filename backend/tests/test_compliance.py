"""Tests for Phase 3 Legal Metrology Compliance Rule Engine."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models.entities import Inspection, ExtractedData
from backend.models.enums import InspectionStatus
from backend.rules import evaluate_inspection


def test_compliance_engine_compliant(db_session: Session):
    """Test compliance evaluation on a fully compliant package."""
    inspection = Inspection(
        image_url="inspections/test/compliant.jpg",
        status=InspectionStatus.REVIEW.value,
    )
    db_session.add(inspection)
    db_session.commit()
    db_session.refresh(inspection)

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Premium Tea",
        manufacturer="Tea Corp, 12 M.G. Road, Mumbai - 400001",
        net_quantity="500 g",
        mrp="Rs. 250.00",
        date="07/2026",
        consumer_care="support@teacorp.com",
    )
    db_session.add(extracted)
    db_session.commit()

    summary = evaluate_inspection(db_session, str(inspection.id))
    assert summary.overall_status == "COMPLIANT"
    assert summary.applicability_status == "NORMAL"
    assert len(summary.violations) == 0


def test_compliance_engine_non_compliant_missing_mrp(db_session: Session):
    """Test compliance evaluation when MRP is missing (Rule 6 failure)."""
    inspection = Inspection(
        image_url="inspections/test/non_compliant.jpg",
        status=InspectionStatus.REVIEW.value,
    )
    db_session.add(inspection)
    db_session.commit()

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Incomplete Product",
        manufacturer="Some Maker, Delhi",
        net_quantity="100 g",
        mrp=None,
        date="07/2026",
    )
    db_session.add(extracted)
    db_session.commit()

    summary = evaluate_inspection(db_session, str(inspection.id))
    assert summary.overall_status == "NON_COMPLIANT"
    assert any(v["rule_number"] == "6" for v in summary.violations)


def test_compliance_engine_prohibited_count_name(db_session: Session):
    """Test Rule 13 failure when prohibited count name 'dozen' is used."""
    inspection = Inspection(
        image_url="inspections/test/dozen.jpg",
        status=InspectionStatus.REVIEW.value,
    )
    db_session.add(inspection)
    db_session.commit()

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Apples",
        manufacturer="Orchard Ltd, Shimla",
        net_quantity="1 dozen",
        mrp="Rs. 120",
        date="07/2026",
    )
    db_session.add(extracted)
    db_session.commit()

    summary = evaluate_inspection(db_session, str(inspection.id))
    assert summary.overall_status == "NON_COMPLIANT"
    assert any(v["rule_number"] == "13" for v in summary.violations)


def test_compliance_api_endpoint(client: TestClient, db_session: Session, auth_headers: dict):
    """Test POST /api/v1/inspections/{inspection_id}/evaluate API endpoint."""
    inspection = Inspection(
        image_url="inspections/test/api_eval.jpg",
        status=InspectionStatus.REVIEW.value,
        user_id="test-user-id-123",
    )
    db_session.add(inspection)
    db_session.commit()

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="API Test Biscuit",
        manufacturer="Biscuit Co, Pune",
        net_quantity="200 g",
        mrp="Rs. 40",
        date="07/2026",
    )
    db_session.add(extracted)
    db_session.commit()

    response = client.post(
        f"/api/v1/inspections/{inspection.id}/evaluate",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["overall_status"] == "COMPLIANT"
