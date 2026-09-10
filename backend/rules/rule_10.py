"""Rule 10 Evaluator: Name and address of manufacturer, packer, importer."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_10(extracted_data: Optional[Any], applicability: str) -> RuleEvaluationResult:
    """Evaluate Rule 10 complete address requirements."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="10",
            rule_code="LM010",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="manufacturer",
            severity="HIGH",
        )

    if not extracted_data or not extracted_data.manufacturer:
        return RuleEvaluationResult(
            rule_number="10",
            rule_code="LM010",
            status="FAIL",
            reason="Manufacturer/packer name and address declaration is absent.",
            field_name="manufacturer",
            severity="HIGH",
        )

    addr = extracted_data.manufacturer
    if len(addr.strip()) < 10:
        return RuleEvaluationResult(
            rule_number="10",
            rule_code="LM010",
            status="REVIEW",
            reason="Manufacturer address declaration appears incomplete or truncated.",
            field_name="manufacturer",
            detected_value=addr,
            severity="HIGH",
        )

    return RuleEvaluationResult(
        rule_number="10",
        rule_code="LM010",
        status="PASS",
        reason="Complete address of manufacturer/packer detected.",
        field_name="manufacturer",
        detected_value=addr,
        severity="HIGH",
    )
