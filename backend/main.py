"""FastAPI main entrypoint for Legal Metrology Packaged Commodity Compliance Backend."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend import __version__
from backend.database.config import get_settings
from backend.database.client import check_db_connectivity
from backend.routes.health import router as health_router
from backend.routes.inspections import router as inspections_router
from backend.routes.catalogue import router as catalogue_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("drishtimitra.backend")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{__version__} [{settings.APP_ENV}]")
    db_status = check_db_connectivity()
    logger.info(f"Initial Database Status: {db_status.get('status')} ({db_status.get('engine')})")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


# FastAPI Application Instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API system for Legal Metrology (Packaged Commodities) Rules, 2011 compliance inspection.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for prototype inspection clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(inspections_router, prefix=settings.API_V1_PREFIX)
app.include_router(catalogue_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"], summary="Root info endpoint")
async def root():
    """Root endpoint returning basic service metadata."""
    return {
        "service": settings.APP_NAME,
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
