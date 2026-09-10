"""Inspection Pydantic Schemas."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import Field

from backend.schemas.common import BaseSchema
from backend.models.enums import InspectionStatus
from backend.schemas.extracted_data import ExtractedDataResponse
from backend.schemas.violation import ViolationResponse


class InspectionBase(BaseSchema):
    """Base inspection attributes."""

    image_url: str = Field(..., description="URL / path to captured label image")
    status: InspectionStatus = Field(InspectionStatus.PROCESSING, description="Inspection status")


class InspectionCreate(BaseSchema):
    """Schema for creating a new inspection."""

    image_url: str = Field(..., description="URL / path to captured label image")


class InspectionResponse(InspectionBase):
    """Schema for inspection response."""

    id: UUID
    created_at: datetime
    updated_at: datetime


class InspectionDetailResponse(InspectionResponse):
    """Detailed inspection response including extracted data and violations."""

    extracted_data: Optional[ExtractedDataResponse] = None
    violations: List[ViolationResponse] = []
