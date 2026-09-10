"""Rule 6 Evaluator: Declarations to be made on every package."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_06(extracted_data: Optional[Any], applicability: str) -> RuleEvaluationResult:
    """Evaluate Rule 6 mandatory declarations (manufacturer, net qty, MRP, date, consumer care)."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="6",
            rule_code="LM006",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="manufacturer",
            severity="HIGH",
        )

    if not extracted_data:
        return RuleEvaluationResult(
            rule_number="6",
            rule_code="LM006",
            status="FAIL",
            reason="No extracted package data available for evaluation.",
            field_name="manufacturer",
            severity="HIGH",
        )

    missing = []
    if not extracted_data.manufacturer:
        missing.append("manufacturer/packer")
    if not extracted_data.net_quantity:
        missing.append("net_quantity")
    if not extracted_data.mrp:
        missing.append("mrp")
    if not extracted_data.date:
        missing.append("date")

    if missing:
        return RuleEvaluationResult(
            rule_number="6",
            rule_code="LM006",
            status="FAIL",
            reason=f"Missing mandatory Rule 6 declarations: {', '.join(missing)}.",
            field_name="manufacturer",
            severity="HIGH",
        )

    return RuleEvaluationResult(
        rule_number="6",
        rule_code="LM006",
        status="PASS",
        reason="Required Rule 6 package declarations (manufacturer, net quantity, MRP, date) were detected.",
        field_name="manufacturer",
        severity="HIGH",
        detected_value="Present",
    )
