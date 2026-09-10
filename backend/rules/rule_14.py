"""Rule 14 Evaluator: Dimensions of certain commodities (textiles)."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_14(extracted_data: Optional[Any], applicability: str, raw_text: str) -> RuleEvaluationResult:
    """Evaluate Rule 14 textile dimensions if applicable."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="14",
            rule_code="LM014",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="dimensions",
            severity="MEDIUM",
        )

    text_lower = raw_text.lower() if raw_text else ""
    prod_name = (extracted_data.product_name or "").lower() if extracted_data else ""
    textile_keywords = ["saree", "dhoti", "bed sheet", "bedsheet", "towel", "table cloth", "napkin", "pillow cover", "fabric", "textile"]

    is_textile = any(kw in prod_name or kw in text_lower for kw in textile_keywords)
    if not is_textile:
        return RuleEvaluationResult(
            rule_number="14",
            rule_code="LM014",
            status="NOT_APPLICABLE",
            reason="Commodity is not a textile product subject to Rule 14.",
            field_name="dimensions",
            severity="MEDIUM",
        )

    if extracted_data and extracted_data.net_quantity and any(c.isdigit() for c in extracted_data.net_quantity):
        return RuleEvaluationResult(
            rule_number="14",
            rule_code="LM014",
            status="PASS",
            reason="Textile dimensions detected for applicable commodity under Rule 14.",
            field_name="dimensions",
            detected_value=extracted_data.net_quantity,
            severity="MEDIUM",
        )

    return RuleEvaluationResult(
        rule_number="14",
        rule_code="LM014",
        status="FAIL",
        reason="Textile commodity requires dimensions under Rule 14 but none were detected.",
        field_name="dimensions",
        severity="MEDIUM",
    )
