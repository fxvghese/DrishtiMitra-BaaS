"""Base data structures for Phase 3 rule evaluation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RuleEvaluationResult(BaseModel):
    """Structured evaluation result for an individual legal rule."""
    rule_number: str
    rule_code: str
    status: str  # PASS, FAIL, REVIEW, NOT_APPLICABLE
    reason: str
    field_name: Optional[str] = None
    detected_value: Optional[str] = None
    severity: str = "HIGH"
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class ComplianceEvaluationSummary(BaseModel):
    """Complete compliance evaluation summary for an inspection."""
    inspection_id: str
    applicability_status: str  # NORMAL, PARTIALLY_EXEMPT, EXEMPT, REVIEW
    applicability_reason: str
    overall_status: str  # COMPLIANT, NON_COMPLIANT, REVIEW
    rules: List[RuleEvaluationResult] = Field(default_factory=list)
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    review_items: List[Dict[str, Any]] = Field(default_factory=list)
