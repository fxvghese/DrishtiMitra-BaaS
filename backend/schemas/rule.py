"""Rule Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import Field

from backend.schemas.common import BaseSchema
from backend.models.enums import ValidationType, RuleSeverity


class RuleBase(BaseSchema):
    """Base rule attributes."""

    rule_code: str = Field(..., max_length=50, description="Unique identifier for the rule (e.g. LM001)")
    name: str = Field(..., max_length=255, description="Human-readable rule name")
    description: Optional[str] = Field(None, description="Detailed explanation of the rule")
    field_name: str = Field(..., max_length=100, description="Target field on the label")
    required: bool = Field(True, description="Whether this field is mandatory")
    validation_type: ValidationType = Field(..., description="Validation routine type")
    severity: RuleSeverity = Field(RuleSeverity.HIGH, description="Severity if rule fails")
    active: bool = Field(True, description="Whether rule is currently evaluated")


class RuleCreate(RuleBase):
    """Schema for creating a new compliance rule."""
    pass


class RuleUpdate(BaseSchema):
    """Schema for updating an existing compliance rule."""

    name: Optional[str] = None
    description: Optional[str] = None
    field_name: Optional[str] = None
    required: Optional[bool] = None
    validation_type: Optional[ValidationType] = None
    severity: Optional[RuleSeverity] = None
    active: Optional[bool] = None


class RuleResponse(RuleBase):
    """Schema for returning rule details."""

    id: UUID
    created_at: datetime
    updated_at: datetime
