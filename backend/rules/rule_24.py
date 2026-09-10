"""Rule 24 Evaluator: Declarations applicable to every wholesale package."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_24(extracted_data: Optional[Any], applicability: str, raw_text: str) -> RuleEvaluationResult:
    """Evaluate Rule 24 wholesale package declarations."""
    text_lower = raw_text.lower() if raw_text else ""
    is_wholesale = "wholesale" in text_lower or "bulk" in text_lower or "institutional pack" in text_lower

    if not is_wholesale:
        return RuleEvaluationResult(
            rule_number="24",
            rule_code="LM024",
            status="NOT_APPLICABLE",
            reason="Package is not identified as a wholesale package.",
            field_name="wholesale",
            severity="HIGH",
        )

    if not extracted_data or not extracted_data.manufacturer or not extracted_data.net_quantity:
        return RuleEvaluationResult(
            rule_number="24",
            rule_code="LM024",
            status="FAIL",
            reason="Wholesale package lacks required manufacturer address or total quantity/retail package count.",
            field_name="wholesale",
            severity="HIGH",
        )

    return RuleEvaluationResult(
        rule_number="24",
        rule_code="LM024",
        status="PASS",
        reason="Wholesale package declarations detected under Rule 24.",
        field_name="wholesale",
        severity="HIGH",
    )
