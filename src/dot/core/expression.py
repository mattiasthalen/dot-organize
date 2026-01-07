"""Expression validation for Manifest SQL subset.

T030: Implement expr validation (allowed tokens, forbidden patterns regex)

Spec Reference: data-model.md §Expression Validation
"""

import re

from dot.models.diagnostic import Diagnostic, Severity

# Forbidden patterns - these indicate query operations, not pure expressions
FORBIDDEN_PATTERNS = [
    (re.compile(r"\bSELECT\b", re.IGNORECASE), "SELECT"),
    (re.compile(r"\bFROM\b", re.IGNORECASE), "FROM"),
    (re.compile(r"\bJOIN\b", re.IGNORECASE), "JOIN"),
    (re.compile(r"\bWHERE\b", re.IGNORECASE), "WHERE"),
    (re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE), "GROUP BY"),
    (re.compile(r"\bORDER\s+BY\b", re.IGNORECASE), "ORDER BY"),
    (re.compile(r"\bWITH\b", re.IGNORECASE), "WITH"),
    # Non-deterministic functions
    (re.compile(r"\bRANDOM\b", re.IGNORECASE), "RANDOM"),
    (re.compile(r"\bNEWID\b", re.IGNORECASE), "NEWID"),
    (re.compile(r"\bGETDATE\b", re.IGNORECASE), "GETDATE"),
    (re.compile(r"\bNOW\b", re.IGNORECASE), "NOW"),
    (re.compile(r"\bCURRENT_TIMESTAMP\b", re.IGNORECASE), "CURRENT_TIMESTAMP"),
    (re.compile(r"\bSYSDATE\b", re.IGNORECASE), "SYSDATE"),
    # DDL/DML
    (re.compile(r"\bINSERT\b", re.IGNORECASE), "INSERT"),
    (re.compile(r"\bUPDATE\b", re.IGNORECASE), "UPDATE"),
    (re.compile(r"\bDELETE\b", re.IGNORECASE), "DELETE"),
    (re.compile(r"\bCREATE\b", re.IGNORECASE), "CREATE"),
    (re.compile(r"\bDROP\b", re.IGNORECASE), "DROP"),
    (re.compile(r"\bALTER\b", re.IGNORECASE), "ALTER"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
]


def validate_expr(expr: str, path: str = "expr") -> list[Diagnostic]:
    """Validate that expr is a pure SQL expression (Manifest SQL subset).

    Checks:
    1. Non-empty string
    2. No forbidden patterns (SELECT, FROM, JOIN, etc.)

    Returns empty list if valid, list of diagnostics if invalid.
    """
    diagnostics: list[Diagnostic] = []

    # Check for empty or whitespace-only
    if not expr or not expr.strip():
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-006",
                severity=Severity.ERROR,
                message="Expression must be non-empty",
                path=path,
                fix="Provide a valid SQL expression for the business key",
            )
        )
        return diagnostics

    # Check for forbidden patterns
    for pattern, name in FORBIDDEN_PATTERNS:
        if pattern.search(expr):
            diagnostics.append(
                Diagnostic(
                    rule_id="HOOK-006",
                    severity=Severity.ERROR,
                    message=f"Expression contains forbidden pattern: {name}. "
                    f"Only pure expressions are allowed (Manifest SQL subset)",
                    path=path,
                    fix=f"Remove {name} and use only column references, literals, "
                    f"operators, CASE, CAST, and allowed functions",
                )
            )
            # Return early on first forbidden pattern to avoid noise
            return diagnostics

    return diagnostics
