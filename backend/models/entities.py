"""SQLAlchemy ORM Entities for Legal Metrology Compliance."""

import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR

from backend.database.client import Base
from backend.models.enums import (
    ValidationType,
    RuleSeverity,
    InspectionStatus,
    ViolationStatus,
)


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class Product(Base):
    """Product entity representing a physical commodity being inspected."""

    __tablename__ = "products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_name = Column(Text, nullable=True)
    manufacturer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    inspections = relationship("Inspection", back_populates="product")


class Rule(Base):
    """Compliance rule entity."""

    __tablename__ = "rules"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    field_name = Column(String(100), nullable=False, index=True)
    required = Column(Boolean, nullable=False, default=True)
    validation_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default=RuleSeverity.HIGH.value)
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    violations = relationship("Violation", back_populates="rule", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            f"validation_type IN ('PRESENT', 'NON_EMPTY', 'VALID_QUANTITY', 'VALID_PRICE', 'VALID_DATE', 'VALID_CONTACT')",
            name="chk_rules_validation_type",
        ),
        CheckConstraint(
            f"severity IN ('LOW', 'MEDIUM', 'HIGH')",
            name="chk_rules_severity",
        ),
    )


class Inspection(Base):
    """Inspection record for a scanned product label."""

    __tablename__ = "inspections"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    product_id = Column(
        GUID,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(String(255), nullable=True, index=True)
    image_url = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default=InspectionStatus.PROCESSING.value, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="inspections")
    images = relationship(
        "InspectionImage",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    extracted_data = relationship(
        "ExtractedData",
        uselist=False,
        back_populates="inspection",
        cascade="all, delete-orphan",
    )
    violations = relationship(
        "Violation",
        back_populates="inspection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            f"status IN ('PROCESSING', 'COMPLIANT', 'REVIEW', 'NON_COMPLIANT', 'ERROR')",
            name="chk_inspections_status",
        ),
    )


class InspectionImage(Base):
    """Image associated with an inspection (supports multiple photos per inspection)."""

    __tablename__ = "inspection_images"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    inspection_id = Column(
        GUID,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url = Column(Text, nullable=False)
    sequence = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    inspection = relationship("Inspection", back_populates="images")


class ExtractedData(Base):
    """Structured label data extracted by OCR."""

    __tablename__ = "extracted_data"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    inspection_id = Column(
        GUID,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    product_name = Column(Text, nullable=True)
    manufacturer = Column(Text, nullable=True)
    net_quantity = Column(Text, nullable=True)
    mrp = Column(Text, nullable=True)
    date = Column(Text, nullable=True)
    consumer_care = Column(Text, nullable=True)
    extraction_confidence = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    inspection = relationship("Inspection", back_populates="extracted_data")


class Violation(Base):
    """Specific compliance violation or review requirement."""

    __tablename__ = "violations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    inspection_id = Column(
        GUID,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id = Column(
        GUID,
        ForeignKey("rules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    field_name = Column(String(100), nullable=False)
    detected_value = Column(Text, nullable=True)
    status = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False, default=RuleSeverity.HIGH.value)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    inspection = relationship("Inspection", back_populates="violations")
    rule = relationship("Rule", back_populates="violations")

    __table_args__ = (
        CheckConstraint(
            f"status IN ('FAIL', 'REVIEW')",
            name="chk_violations_status",
        ),
        CheckConstraint(
            f"severity IN ('LOW', 'MEDIUM', 'HIGH')",
            name="chk_violations_severity",
        ),
    )


class ReferenceProduct(Base):
    """Reference product from external catalogues (Open Food Facts, Flipkart)."""

    __tablename__ = "reference_products"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=True, index=True)
    product_name = Column(Text, nullable=False, index=True)
    generic_name = Column(Text, nullable=True)
    brand = Column(Text, nullable=True, index=True)
    category = Column(Text, nullable=True, index=True)
    quantity = Column(Text, nullable=True)
    mrp = Column(Numeric(10, 2), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    product_metadata = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
