"""Rule 13 Evaluator: Statement of units of weight, measure or number."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_13(extracted_data: Optional[Any], applicability: str) -> RuleEvaluationResult:
    """Evaluate Rule 13 units and prohibited count names."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="13",
            rule_code="LM013",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="net_quantity",
            severity="HIGH",
        )

    if not extracted_data or not extracted_data.net_quantity:
        return RuleEvaluationResult(
            rule_number="13",
            rule_code="LM013",
            status="FAIL",
            reason="Net quantity declaration is absent.",
            field_name="net_quantity",
            severity="HIGH",
        )

    qty_lower = extracted_data.net_quantity.lower()
    prohibited_counts = ["dozen", "score", "gross", "great gross"]
    for pc in prohibited_counts:
        if pc in qty_lower:
            return RuleEvaluationResult(
                rule_number="13",
                rule_code="LM013",
                status="FAIL",
                reason=f"Prohibited count name '{pc}' detected under Rule 13.",
                field_name="net_quantity",
                detected_value=extracted_data.net_quantity,
                severity="HIGH",
            )

    return RuleEvaluationResult(
        rule_number="13",
        rule_code="LM013",
        status="PASS",
        reason="Net quantity unit statement conforms to Rule 13.",
        field_name="net_quantity",
        detected_value=extracted_data.net_quantity,
        severity="HIGH",
    )
