"""Common schemas and response wrappers."""

from datetime import datetime
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic configuration for all schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class ApiResponse(BaseSchema, Generic[T]):
    """Standardized API response wrapper."""

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    timestamp: datetime = datetime.now()
