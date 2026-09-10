"""Health check Pydantic Schemas."""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Database connectivity details."""

    status: str = Field(..., description="CONNECTED, DISCONNECTED, or UNKNOWN")
    engine: str = Field(..., description="Database engine type (e.g. postgresql, sqlite)")
    supabase_configured: bool = Field(..., description="Whether Supabase client is configured")
    details: Optional[str] = Field(None, description="Diagnostic details")


class HealthResponse(BaseModel):
    """System and service health response."""

    status: str = Field("healthy", description="Overall API health status")
    app_name: str
    environment: str
    version: str
    timestamp: datetime
    database: DatabaseHealth
