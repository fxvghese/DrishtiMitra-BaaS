"""Database connection and client management."""

import logging
from typing import Generator, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from supabase import create_client, Client

from backend.database.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# SQLAlchemy Base Declarative Model
Base = declarative_base()

# SQLAlchemy Engine & Session Setup
connect_args = {}
if settings.effective_db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.effective_db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_supabase_client() -> Optional[Client]:
    """Get Supabase client instance if configured."""
    if settings.is_supabase_configured:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as exc:
            logger.warning(f"Could not initialize Supabase client: {exc}")
            return None
    return None


def check_db_connectivity() -> Dict[str, Any]:
    """Verify database connectivity and return status details."""
    db_status = {
        "status": "UNKNOWN",
        "engine": "postgresql" if "postgres" in settings.effective_db_url else "sqlite",
        "supabase_configured": settings.is_supabase_configured,
        "details": None,
    }

    # Test SQLAlchemy database connection
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            db_status["status"] = "CONNECTED"
            db_status["details"] = "Database connection successful (SELECT 1 passed)"
    except Exception as exc:
        db_status["status"] = "DISCONNECTED"
        db_status["details"] = f"Database connection error: {str(exc)}"

    return db_status
