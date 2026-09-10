"""Rule 11 Evaluator: General provisions relating to declaration of quantity."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_11(extracted_data: Optional[Any], applicability: str) -> RuleEvaluationResult:
    """Evaluate Rule 11 quantity general provisions."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="11",
            rule_code="LM011",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="net_quantity",
            severity="HIGH",
        )

    if not extracted_data or not extracted_data.net_quantity:
        return RuleEvaluationResult(
            rule_number="11",
            rule_code="LM011",
            status="FAIL",
            reason="Net quantity declaration is absent.",
            field_name="net_quantity",
            severity="HIGH",
        )

    net_qty = extracted_data.net_quantity
    if "when packed" in net_qty.lower():
        return RuleEvaluationResult(
            rule_number="11",
            rule_code="LM011",
            status="REVIEW",
            reason="Qualifier 'when packed' detected; Third Schedule applicability requires verification.",
            field_name="net_quantity",
            detected_value=net_qty,
            severity="MEDIUM",
        )

    return RuleEvaluationResult(
        rule_number="11",
        rule_code="LM011",
        status="PASS",
        reason="Net quantity general provisions satisfied.",
        field_name="net_quantity",
        detected_value=net_qty,
        severity="HIGH",
    )
