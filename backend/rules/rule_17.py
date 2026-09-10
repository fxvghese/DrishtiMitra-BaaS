"""Rule 17 Evaluator: Dimensions of container-type commodities."""

from typing import Optional, Any
from backend.rules.base import RuleEvaluationResult


def evaluate_rule_17(extracted_data: Optional[Any], applicability: str, raw_text: str) -> RuleEvaluationResult:
    """Evaluate Rule 17 container dimensions."""
    if applicability == "EXEMPT":
        return RuleEvaluationResult(
            rule_number="17",
            rule_code="LM017",
            status="NOT_APPLICABLE",
            reason="Package is exempt under Rule 26.",
            field_name="container",
            severity="MEDIUM",
        )

    text_lower = raw_text.lower() if raw_text else ""
    prod_name = (extracted_data.product_name or "").lower() if extracted_data else ""
    container_keywords = ["container", "box", "bag", "carton", "pouch"]

    is_container = any(kw in prod_name or kw in text_lower for kw in container_keywords)
    if not is_container:
        return RuleEvaluationResult(
            rule_number="17",
            rule_code="LM017",
            status="NOT_APPLICABLE",
            reason="Commodity is not a container-type product subject to Rule 17.",
            field_name="container",
            severity="MEDIUM",
        )

    return RuleEvaluationResult(
        rule_number="17",
        rule_code="LM017",
        status="REVIEW",
        reason="Container commodity detected; shape-appropriate dimensions and capacity reference require manual review.",
        field_name="container",
        severity="MEDIUM",
    )
