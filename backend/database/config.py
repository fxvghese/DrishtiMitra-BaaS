"""Database and Application Configuration Module."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and database settings loaded from environment or .env file."""

    # Application
    APP_NAME: str = "Legal Metrology Compliance API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None          # Anon/publishable key
    SUPABASE_SERVICE_KEY: Optional[str] = None  # Service role key (server-side ops)

    # Direct Database Connection URL (PostgreSQL / SQLite fallback for tests)
    DATABASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_supabase_configured(self) -> bool:
        """Check if Supabase anon credentials are validly supplied."""
        return bool(
            self.SUPABASE_URL
            and self.SUPABASE_KEY
            and not self.SUPABASE_URL.startswith("https://your-project")
        )

    @property
    def is_storage_configured(self) -> bool:
        """Check if Supabase service role key is set for server-side storage operations."""
        return bool(
            self.is_supabase_configured
            and self.SUPABASE_SERVICE_KEY
            and self.SUPABASE_SERVICE_KEY != "your-service-role-key-here"
        )

    @property
    def effective_db_url(self) -> str:
        """Resolve the effective database URL.

        Priority:
          1. If running in test environment (PYTEST_CURRENT_TEST set) → SQLite in-memory.
          2. DATABASE_URL if set and not a placeholder → use directly (PostgreSQL).
          3. Otherwise → SQLite local fallback (development / tests only).
        """
        import os
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING"):
            return "sqlite:///:memory:"
        placeholder_markers = ("[YOUR-DB-PASSWORD]", "your-password", "localhost:54322")
        if self.DATABASE_URL and not any(m in self.DATABASE_URL for m in placeholder_markers):
            return self.DATABASE_URL
        return "sqlite:///./legal_metrology.db"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
