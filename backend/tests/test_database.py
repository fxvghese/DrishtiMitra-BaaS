"""Tests for database entities, constraints, and relationships."""

import uuid
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.entities import Rule, Inspection, ExtractedData, Violation
from backend.models.enums import (
    InspectionStatus,
    RuleSeverity,
    ValidationType,
    ViolationStatus,
)


def test_database_tables_exist(db_session: Session):
    """Test that all required core tables exist in the schema."""
    inspector = inspect(db_session.bind)
    table_names = inspector.get_table_names()

    assert "rules" in table_names
    assert "inspections" in table_names
    assert "extracted_data" in table_names
    assert "violations" in table_names


def test_seed_rules_retrieval(db_session: Session):
    """Test that all seed rules exist and have expected properties."""
    rules = db_session.query(Rule).all()
    assert len(rules) == 15

    rule_codes = {r.rule_code: r for r in rules}
    assert "LM001" in rule_codes
    assert "LM002" in rule_codes
    assert "LM003" in rule_codes
    assert "LM004" in rule_codes
    assert "LM005" in rule_codes
    assert "LM006" in rule_codes
    assert "LM010" in rule_codes
    assert "LM026" in rule_codes

    # Test LM001 Manufacturer
    lm001 = rule_codes["LM001"]
    assert lm001.field_name == "manufacturer"
    assert lm001.validation_type == ValidationType.PRESENT.value
    assert lm001.severity == RuleSeverity.HIGH.value
    assert lm001.required is True

    # Test LM002 Net Quantity
    lm002 = rule_codes["LM002"]
    assert lm002.field_name == "net_quantity"
    assert lm002.validation_type == ValidationType.VALID_QUANTITY.value
    assert lm002.severity == RuleSeverity.HIGH.value

    # Test LM003 MRP
    lm003 = rule_codes["LM003"]
    assert lm003.field_name == "mrp"
    assert lm003.validation_type == ValidationType.VALID_PRICE.value

    # Test LM004 Date
    lm004 = rule_codes["LM004"]
    assert lm004.field_name == "date"
    assert lm004.validation_type == ValidationType.VALID_DATE.value
    assert lm004.severity == RuleSeverity.MEDIUM.value

    # Test LM005 Consumer Care
    lm005 = rule_codes["LM005"]
    assert lm005.field_name == "consumer_care"
    assert lm005.validation_type == ValidationType.PRESENT.value


def test_inspection_extracted_data_relationship(db_session: Session):
    """Test 1:1 relationship between Inspection and ExtractedData."""
    # 1. Create Inspection
    inspection = Inspection(
        image_url="https://storage.example.com/inspections/pkg_001.jpg",
        status=InspectionStatus.PROCESSING.value,
    )
    db_session.add(inspection)
    db_session.commit()
    db_session.refresh(inspection)

    # 2. Add ExtractedData
    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Sample Premium Cookies",
        manufacturer="Good Bakes Ltd, Mumbai",
        net_quantity="200 g",
        mrp="Rs. 50.00",
        date="07/2026",
        consumer_care="care@goodbakes.com",
        extraction_confidence=94.50,
    )
    db_session.add(extracted)
    db_session.commit()

    # 3. Verify access via relationship
    db_session.refresh(inspection)
    assert inspection.extracted_data is not None
    assert inspection.extracted_data.product_name == "Sample Premium Cookies"
    assert inspection.extracted_data.net_quantity == "200 g"
    assert inspection.extracted_data.extraction_confidence == 94.50


def test_inspection_violations_relationship(db_session: Session):
    """Test 1:many relationship between Inspection and Violations."""
    inspection = Inspection(
        image_url="https://storage.example.com/inspections/pkg_002.jpg",
        status=InspectionStatus.NON_COMPLIANT.value,
    )
    db_session.add(inspection)
    db_session.commit()
    db_session.refresh(inspection)

    lm005_rule = db_session.query(Rule).filter_by(rule_code="LM005").first()
    assert lm005_rule is not None

    # Add Violation
    violation = Violation(
        inspection_id=inspection.id,
        rule_id=lm005_rule.id,
        field_name="consumer_care",
        detected_value=None,
        status=ViolationStatus.FAIL.value,
        severity=RuleSeverity.HIGH.value,
        message="Consumer care details not detected on package label.",
    )
    db_session.add(violation)
    db_session.commit()

    # Verify relationship
    db_session.refresh(inspection)
    assert len(inspection.violations) == 1
    assert inspection.violations[0].field_name == "consumer_care"
    assert inspection.violations[0].status == ViolationStatus.FAIL.value
    assert inspection.violations[0].rule.rule_code == "LM005"


def test_cascade_delete_inspection(db_session: Session):
    """Test that deleting an inspection cascades and deletes associated extracted_data and violations."""
    # Create Inspection + ExtractedData + Violation
    inspection = Inspection(
        image_url="https://storage.example.com/inspections/pkg_cascade.jpg",
        status=InspectionStatus.COMPLIANT.value,
    )
    db_session.add(inspection)
    db_session.commit()

    extracted = ExtractedData(
        inspection_id=inspection.id,
        product_name="Test Product",
    )
    rule = db_session.query(Rule).first()
    violation = Violation(
        inspection_id=inspection.id,
        rule_id=rule.id,
        field_name="manufacturer",
        detected_value="Test Co",
        status=ViolationStatus.REVIEW.value,
        severity=RuleSeverity.LOW.value,
        message="Review address clarity",
    )
    db_session.add_all([extracted, violation])
    db_session.commit()

    inspection_id = inspection.id

    # Verify they exist
    assert db_session.query(ExtractedData).filter_by(inspection_id=inspection_id).first() is not None
    assert db_session.query(Violation).filter_by(inspection_id=inspection_id).first() is not None

    # Delete Inspection
    db_session.delete(inspection)
    db_session.commit()

    # Verify cascading delete
    assert db_session.query(ExtractedData).filter_by(inspection_id=inspection_id).first() is None
    assert db_session.query(Violation).filter_by(inspection_id=inspection_id).first() is None


def test_unique_rule_code_constraint(db_session: Session):
    """Test that rule_code enforces uniqueness."""
    duplicate_rule = Rule(
        rule_code="LM001",  # Already exists in seeds
        name="Duplicate Rule",
        field_name="manufacturer",
        validation_type=ValidationType.PRESENT.value,
        required=True,
        severity=RuleSeverity.HIGH.value,
    )
    db_session.add(duplicate_rule)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
