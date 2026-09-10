"""Compliance Engine coordinating applicability and rule evaluations."""

import logging
from typing import List
from sqlalchemy.orm import Session

from backend.models.entities import Inspection, ExtractedData, Violation, Rule
from backend.models.enums import InspectionStatus, ViolationStatus
from backend.rules.base import RuleEvaluationResult, ComplianceEvaluationSummary
from backend.rules.applicability import evaluate_applicability
from backend.rules.rule_06 import evaluate_rule_06
from backend.rules.rule_10 import evaluate_rule_10
from backend.rules.rule_11 import evaluate_rule_11
from backend.rules.rule_12 import evaluate_rule_12
from backend.rules.rule_13 import evaluate_rule_13
from backend.rules.rule_14 import evaluate_rule_14
from backend.rules.rule_16 import evaluate_rule_16
from backend.rules.rule_17 import evaluate_rule_17
from backend.rules.rule_24 import evaluate_rule_24

logger = logging.getLogger(__name__)


def evaluate_inspection(db: Session, inspection_id: str) -> ComplianceEvaluationSummary:
    """Execute complete compliance evaluation pipeline for an inspection."""
    inspection = db.query(Inspection).filter_by(id=inspection_id).first()
    if not inspection:
        raise ValueError(f"Inspection with id '{inspection_id}' not found.")

    extracted_data = db.query(ExtractedData).filter_by(inspection_id=inspection_id).first()
    raw_text_parts = []
    if extracted_data:
        for field in ["product_name", "manufacturer", "net_quantity", "mrp", "date", "consumer_care"]:
            val = getattr(extracted_data, field, None)
            if val:
                raw_text_parts.append(val)
    full_raw_text = "\n".join(raw_text_parts)

    applicability_status, applicability_reason, app_eval = evaluate_applicability(extracted_data, full_raw_text)

    rule_results: List[RuleEvaluationResult] = [
        app_eval,
        evaluate_rule_06(extracted_data, applicability_status),
        evaluate_rule_10(extracted_data, applicability_status),
        evaluate_rule_11(extracted_data, applicability_status),
        evaluate_rule_12(extracted_data, applicability_status),
        evaluate_rule_13(extracted_data, applicability_status),
        evaluate_rule_14(extracted_data, applicability_status, full_raw_text),
        evaluate_rule_16(extracted_data, applicability_status, full_raw_text),
        evaluate_rule_17(extracted_data, applicability_status, full_raw_text),
        evaluate_rule_24(extracted_data, applicability_status, full_raw_text),
    ]

    has_fail = any(r.status == "FAIL" for r in rule_results)
    has_review = any(r.status == "REVIEW" for r in rule_results) or applicability_status == "REVIEW"

    if has_fail:
        overall_status = InspectionStatus.NON_COMPLIANT.value
    elif has_review:
        overall_status = InspectionStatus.REVIEW.value
    else:
        overall_status = InspectionStatus.COMPLIANT.value

    inspection.status = overall_status

    db.query(Violation).filter_by(inspection_id=inspection_id).delete()

    violations_data = []
    review_items = []

    for r in rule_results:
        if r.status in ("FAIL", "REVIEW"):
            rule_entity = db.query(Rule).filter_by(rule_code=r.rule_code).first()
            rule_id = rule_entity.id if rule_entity else None

            if rule_id:
                violation = Violation(
                    inspection_id=inspection_id,
                    rule_id=rule_id,
                    field_name=r.field_name or "general",
                    detected_value=r.detected_value,
                    status=ViolationStatus.FAIL.value if r.status == "FAIL" else ViolationStatus.REVIEW.value,
                    severity=r.severity,
                    message=r.reason,
                )
                db.add(violation)

            v_dict = {
                "rule_number": r.rule_number,
                "rule_code": r.rule_code,
                "status": r.status,
                "reason": r.reason,
                "field_name": r.field_name,
                "detected_value": r.detected_value,
                "severity": r.severity,
            }
            if r.status == "FAIL":
                violations_data.append(v_dict)
            else:
                review_items.append(v_dict)

    db.commit()

    return ComplianceEvaluationSummary(
        inspection_id=str(inspection.id),
        applicability_status=applicability_status,
        applicability_reason=applicability_reason,
        overall_status=overall_status,
        rules=rule_results,
        violations=violations_data,
        review_items=review_items,
    )
