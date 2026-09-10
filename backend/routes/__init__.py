"""API Routes package."""

from backend.routes.health import router as health_router
from backend.routes.inspections import router as inspections_router
from backend.routes.catalogue import router as catalogue_router

__all__ = ["health_router", "inspections_router", "catalogue_router"]
