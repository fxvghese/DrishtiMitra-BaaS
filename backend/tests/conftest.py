"""Pytest configuration and fixtures for backend test suite."""

import os
import pytest
import jwt
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

# Set testing environment variable BEFORE importing app modules
os.environ["TESTING"] = "1"

from backend.main import app
from backend.database.client import Base, get_db_session
from backend.models.entities import Rule, Inspection, ExtractedData, Violation
from backend.models.enums import ValidationType, RuleSeverity


# Setup SQLite in-memory engine for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Enable foreign keys in SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all database tables for testing session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh database session for each test with seeded prototype rules."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed Prototype Rules
    seed_rules = [
        Rule(
            rule_code="LM001",
            name="Manufacturer Name and Address Declaration",
            description="Verifies that the name and complete address of the manufacturer is present.",
            field_name="manufacturer",
            validation_type=ValidationType.PRESENT.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM002",
            name="Net Quantity Declaration and Standard Units",
            description="Verifies that net quantity is declared in standard units.",
            field_name="net_quantity",
            validation_type=ValidationType.VALID_QUANTITY.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM003",
            name="Maximum Retail Price (MRP) Declaration",
            description="Verifies that MRP inclusive of all taxes is declared.",
            field_name="mrp",
            validation_type=ValidationType.VALID_PRICE.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM004",
            name="Date of Manufacture/Packaging/Import",
            description="Verifies that the month and year of packaging is declared.",
            field_name="date",
            validation_type=ValidationType.VALID_DATE.value,
            required=True,
            severity=RuleSeverity.MEDIUM.value,
            active=True,
        ),
        Rule(
            rule_code="LM005",
            name="Consumer Care Details Declaration",
            description="Verifies that consumer care contact details are declared.",
            field_name="consumer_care",
            validation_type=ValidationType.PRESENT.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM006",
            name="Rule 6 - Declarations to be made on every package",
            description="Verifies mandatory package declarations.",
            field_name="manufacturer",
            validation_type=ValidationType.PRESENT.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM010",
            name="Rule 10 - Name and address of manufacturer, packer, importer",
            description="Verifies complete address declaration.",
            field_name="manufacturer",
            validation_type=ValidationType.PRESENT.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM011",
            name="Rule 11 - General provisions relating to declaration of quantity",
            description="Verifies quantity exclusions and when-packed qualifiers.",
            field_name="net_quantity",
            validation_type=ValidationType.VALID_QUANTITY.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM012",
            name="Rule 12 - Manner in which declaration of quantity shall be made",
            description="Verifies unit mode and absence of exaggerated wording.",
            field_name="net_quantity",
            validation_type=ValidationType.VALID_QUANTITY.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM013",
            name="Rule 13 - Statement of units of weight, measure or number",
            description="Verifies permitted SI units and symbols.",
            field_name="net_quantity",
            validation_type=ValidationType.VALID_QUANTITY.value,
            required=True,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM014",
            name="Rule 14 - Dimensions of certain commodities",
            description="Verifies finished dimensions for textiles.",
            field_name="dimensions",
            validation_type=ValidationType.PRESENT.value,
            required=False,
            severity=RuleSeverity.MEDIUM.value,
            active=True,
        ),
        Rule(
            rule_code="LM016",
            name="Rule 16 - Declarations with regard to number of usable sheets",
            description="Verifies usable sheets count.",
            field_name="sheets",
            validation_type=ValidationType.PRESENT.value,
            required=False,
            severity=RuleSeverity.MEDIUM.value,
            active=True,
        ),
        Rule(
            rule_code="LM017",
            name="Rule 17 - Dimensions of container-type commodities",
            description="Verifies container dimensions and capacity references.",
            field_name="container",
            validation_type=ValidationType.PRESENT.value,
            required=False,
            severity=RuleSeverity.MEDIUM.value,
            active=True,
        ),
        Rule(
            rule_code="LM024",
            name="Rule 24 - Declarations applicable to every wholesale package",
            description="Verifies wholesale package declarations.",
            field_name="wholesale",
            validation_type=ValidationType.PRESENT.value,
            required=False,
            severity=RuleSeverity.HIGH.value,
            active=True,
        ),
        Rule(
            rule_code="LM026",
            name="Rule 26 - Exemption in respect of certain packages",
            description="Assesses applicability and exemption conditions.",
            field_name="exemption",
            validation_type=ValidationType.PRESENT.value,
            required=False,
            severity=RuleSeverity.LOW.value,
            active=True,
        ),
    ]
    session.add_all(seed_rules)
    session.commit()

    yield session

    if transaction.is_active:
        transaction.rollback()
    session.close()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db_session] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict:
    """Provide valid cryptographically signed JWT authorization headers for testing."""
    from backend.database.config import get_settings
    settings = get_settings()
    jwt_secret = getattr(settings, "SUPABASE_JWT_SECRET", None) or settings.SUPABASE_KEY or "fallback-secret"
    token = jwt.encode({"sub": "test-user-id-123", "role": "authenticated"}, jwt_secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
