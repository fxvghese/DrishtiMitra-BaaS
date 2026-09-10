"""Database and Compliance Enums."""

from enum import Enum


class ValidationType(str, Enum):
    """Validation type for compliance rules."""

    PRESENT = "PRESENT"
    NON_EMPTY = "NON_EMPTY"
    VALID_QUANTITY = "VALID_QUANTITY"
    VALID_PRICE = "VALID_PRICE"
    VALID_DATE = "VALID_DATE"
    VALID_CONTACT = "VALID_CONTACT"


class RuleSeverity(str, Enum):
    """Severity classification for violations and rules."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InspectionStatus(str, Enum):
    """Lifecycle status of a product inspection."""

    PROCESSING = "PROCESSING"
    COMPLIANT = "COMPLIANT"
    REVIEW = "REVIEW"
    NON_COMPLIANT = "NON_COMPLIANT"
    ERROR = "ERROR"


class ViolationStatus(str, Enum):
    """Status of an individual compliance violation."""

    FAIL = "FAIL"
    REVIEW = "REVIEW"
