"""Extracted Data Pydantic Schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from pydantic import Field

from backend.schemas.common import BaseSchema


class ExtractedDataBase(BaseSchema):
    """Base extracted data attributes (nullable for missing OCR fields)."""

    product_name: Optional[str] = Field(None, description="Extracted product brand or commodity name")
    manufacturer: Optional[str] = Field(None, description="Extracted manufacturer / packer / importer details")
    net_quantity: Optional[str] = Field(None, description="Extracted net quantity (e.g. 200 g, 1 L)")
    mrp: Optional[str] = Field(None, description="Extracted maximum retail price (e.g. ₹60, Rs. 60.00)")
    date: Optional[str] = Field(None, description="Extracted date of manufacture/packaging")
    consumer_care: Optional[str] = Field(None, description="Extracted consumer care contact details")
    extraction_confidence: Optional[Decimal] = Field(None, description="Confidence score of OCR extraction (0.00-100.00)")


class ExtractedDataCreate(ExtractedDataBase):
    """Schema for inserting extracted data for an inspection."""

    inspection_id: UUID


class ExtractedDataResponse(ExtractedDataBase):
    """Schema for returning extracted data."""

    id: UUID
    inspection_id: UUID
    created_at: datetime
    updated_at: datetime
