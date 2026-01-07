"""Diagnostic model for validation results.

Spec Reference: spec.md#diagnostic-format, FR-016
"""

from enum import Enum

from pydantic import BaseModel


class Severity(str, Enum):
    """Severity level for diagnostics."""

    ERROR = "ERROR"  # Exit code 1
    WARN = "WARN"  # Exit code 0, but reported


class Diagnostic(BaseModel, frozen=True):
    """Validation diagnostic with rule ID, message, and fix suggestion.

    Attributes:
        rule_id: Stable identifier (e.g., "HOOK-001")
        severity: ERROR or WARN
        message: Human-readable message
        path: JSONPath to offending field
        fix: Suggested fix
    """

    rule_id: str
    severity: Severity
    message: str
    path: str
    fix: str
