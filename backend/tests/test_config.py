"""Tests for settings and configuration loading."""

import os
from contextlib import contextmanager
from backend.database.config import Settings, get_settings


@contextmanager
def _without_testing_env():
    """Context manager to temporarily remove test env vars."""
    old_testing = os.environ.pop("TESTING", None)
    old_pytest = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        yield
    finally:
        if old_testing is not None:
            os.environ["TESTING"] = old_testing
        if old_pytest is not None:
            os.environ["PYTEST_CURRENT_TEST"] = old_pytest


def test_settings_load_defaults():
    """Test default settings load correctly."""
    settings = get_settings()
    assert settings.APP_NAME == "Legal Metrology Compliance API"
    assert settings.PORT == 8000
    assert isinstance(settings.DEBUG, bool)


def test_effective_db_url_resolution():
    """Test that a valid PostgreSQL DATABASE_URL is returned as-is."""
    with _without_testing_env():
        real_url = "postgresql://postgres:real_password@db.cpqiarqoeynrkbstgijs.supabase.co:5432/postgres"
        settings = Settings(
            DATABASE_URL=real_url,
            SUPABASE_URL="https://cpqiarqoeynrkbstgijs.supabase.co",
            SUPABASE_KEY="secret-key",
        )
        assert settings.effective_db_url == real_url
        assert settings.is_supabase_configured is True


def test_effective_db_url_falls_back_to_sqlite_with_placeholder():
    """Test that placeholder DATABASE_URL falls back to SQLite."""
    with _without_testing_env():
        settings = Settings(
            DATABASE_URL="postgresql://postgres:[YOUR-DB-PASSWORD]@db.example.supabase.co:5432/postgres",
        )
        assert settings.effective_db_url == "sqlite:///./legal_metrology.db"


def test_supabase_configured_false_with_placeholders():
    """Test that default/placeholder values do not flag as configured."""
    settings = Settings(
        SUPABASE_URL="https://your-project-id.supabase.co",
        SUPABASE_KEY="your-supabase-anon-or-service-role-key",
    )
    assert settings.is_supabase_configured is False