"""Health check API route."""

from datetime import datetime
from fastapi import APIRouter, status
from backend.database.config import get_settings
from backend.database.client import check_db_connectivity
from backend.schemas.health import HealthResponse, DatabaseHealth
from backend import __version__

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health and Database Connectivity Check",
    description="Returns API status, environment, version, and database connectivity state.",
)
async def health_check() -> HealthResponse:
    """Check API service health and database connectivity."""
    db_info = check_db_connectivity()

    return HealthResponse(
        status="healthy" if db_info.get("status") == "CONNECTED" else "degraded",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        version=__version__,
        timestamp=datetime.now(),
        database=DatabaseHealth(
            status=db_info.get("status", "UNKNOWN"),
            engine=db_info.get("engine", "unknown"),
            supabase_configured=db_info.get("supabase_configured", False),
            details=db_info.get("details"),
        ),
    )
