"""Rule 12 Evaluator: Manner in which declaration of quantity shall be made."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_12(extracted_data: Optional[Any], applicability: str) -> RuleEvaluationResult:
    """Evaluate Rule 12 quantity expression and absence of exaggerated wording."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="12",
            rule_code="LM012",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="net_quantity",
            severity="HIGH",
        )

    if not extracted_data or not extracted_data.net_quantity:
        return RuleEvaluationResult(
            rule_number="12",
            rule_code="LM012",
            status="FAIL",
            reason="Net quantity declaration is absent.",
            field_name="net_quantity",
            severity="HIGH",
        )

    qty_lower = extracted_data.net_quantity.lower()
    prohibited = ["minimum", "not less than", "average", "about", "approximately"]
    for p in prohibited:
        if p in qty_lower:
            return RuleEvaluationResult(
                rule_number="12",
                rule_code="LM012",
                status="FAIL",
                reason=f"Prohibited expression '{p}' detected in net quantity declaration under Rule 12(6).",
                field_name="net_quantity",
                detected_value=extracted_data.net_quantity,
                severity="HIGH",
            )

    return RuleEvaluationResult(
        rule_number="12",
        rule_code="LM012",
        status="PASS",
        reason="Quantity declaration manner conforms to Rule 12.",
        field_name="net_quantity",
        detected_value=extracted_data.net_quantity,
        severity="HIGH",
    )
