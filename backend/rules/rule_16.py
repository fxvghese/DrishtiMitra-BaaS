"""Rule 16 Evaluator: Number of usable sheets."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_16(extracted_data: Optional[Any], applicability: str, raw_text: str) -> RuleEvaluationResult:
    """Evaluate Rule 16 usable sheets for sheet-type commodities."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="16",
            rule_code="LM016",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="sheets",
            severity="MEDIUM",
        )

    text_lower = raw_text.lower() if raw_text else ""
    prod_name = (extracted_data.product_name or "").lower() if extracted_data else ""
    sheet_keywords = ["tissue", "toilet paper", "foil", "waxed paper", "napkin", "sheets"]

    is_sheet = any(kw in prod_name or kw in text_lower for kw in sheet_keywords)
    if not is_sheet:
        return RuleEvaluationResult(
            rule_number="16",
            rule_code="LM016",
            status="NOT_APPLICABLE",
            reason="Commodity is not a sheet-type product subject to Rule 16.",
            field_name="sheets",
            severity="MEDIUM",
        )

    if "sheet" in text_lower or "count" in text_lower or (extracted_data and extracted_data.net_quantity and "sheet" in extracted_data.net_quantity.lower()):
        return RuleEvaluationResult(
            rule_number="16",
            rule_code="LM016",
            status="PASS",
            reason="Number of usable sheets declaration detected under Rule 16.",
            field_name="sheets",
            detected_value=extracted_data.net_quantity if extracted_data else None,
            severity="MEDIUM",
        )

    return RuleEvaluationResult(
        rule_number="16",
        rule_code="LM016",
        status="FAIL",
        reason="Sheet commodity requires usable sheets declaration under Rule 16 but none was detected.",
        field_name="sheets",
        severity="MEDIUM",
    )
