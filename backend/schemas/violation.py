"""Violation Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import Field

from backend.schemas.common import BaseSchema
from backend.models.enums import ViolationStatus, RuleSeverity


class ViolationBase(BaseSchema):
    """Base violation attributes."""

    field_name: str = Field(..., description="Field with non-compliance")
    detected_value: Optional[str] = Field(None, description="Physical value detected by OCR, or None if missing")
    status: ViolationStatus = Field(..., description="Compliance check result status (FAIL, REVIEW)")
    severity: RuleSeverity = Field(RuleSeverity.HIGH, description="Severity of the violation")
    message: str = Field(..., description="Explainable violation message for officers")


class ViolationCreate(ViolationBase):
    """Schema for creating a violation record."""

    inspection_id: UUID
    rule_id: UUID


class ViolationResponse(ViolationBase):
    """Schema for returning violation details."""

    id: UUID
    inspection_id: UUID
    rule_id: UUID
    created_at: datetime
