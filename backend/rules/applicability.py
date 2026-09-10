"""Rule 26 Exemption and Applicability Evaluator."""

import logging
import re
from typing import Optional, Tuple, Any
from backend.rules.base import RuleEvaluationResult

logger = logging.getLogger(__name__)


def evaluate_applicability(extracted_data: Optional[Any], raw_text: str) -> Tuple[str, str, RuleEvaluationResult]:
    """Evaluate Rule 26 applicability and exemptions.

    Returns:
        Tuple of (applicability_status, applicability_reason, rule_evaluation_result)
    """
    text_lower = raw_text.lower() if raw_text else ""
    product_name = (extracted_data.product_name or "").lower() if extracted_data else ""
    net_qty = (extracted_data.net_quantity or "").lower() if extracted_data else ""

    is_pan_masala = "pan masala" in product_name or "pan masala" in text_lower

    is_small_qty = False
    if "g" in net_qty or "ml" in net_qty or "gram" in net_qty:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gm|gms|ml)', net_qty)
        if match:
            val = float(match.group(1))
            if val <= 10.0:
                is_small_qty = True

    if is_small_qty:
        if is_pan_masala:
            status = "NORMAL"
            reason = "Small quantity detected but Rule 26(a) exemption does not apply to pan masala (2026 amendment proviso)."
        else:
            status = "EXEMPT"
            reason = "Package qualifies for Rule 26(a) small quantity exemption (<=10g/10ml)."
    elif "fast food" in text_lower or "restaurant" in text_lower:
        status = "EXEMPT"
        reason = "Package qualifies for Rule 26(b) fast food exemption."
    elif "agricultural" in text_lower or "farm produce" in text_lower:
        status = "EXEMPT"
        reason = "Package qualifies for Rule 26(d) agricultural farm produce exemption."
    elif not net_qty and not raw_text:
        status = "REVIEW"
        reason = "Insufficient evidence to determine applicability/exemption status."
    else:
        status = "NORMAL"
        reason = "Package is subject to normal Legal Metrology compliance rules."

    eval_result = RuleEvaluationResult(
        rule_number="26",
        rule_code="LM026",
        status="PASS" if status != "REVIEW" else "REVIEW",
        reason=reason,
        field_name="exemption",
        detected_value=status,
        severity="LOW",
        evidence=[{"source": "OCR_TEXT", "value": raw_text[:200]}] if raw_text else [],
    )

    return status, reason, eval_result
