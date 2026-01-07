"""Unit tests for expression validation.

T018: Tests for expr validation (allowed tokens, forbidden patterns)
"""

import pytest


class TestExpressionValidation:
    """Tests for expr validation."""

    @pytest.mark.parametrize(
        "expr",
        [
            # Column references
            "customer_id",
            "order_id",
            '"Customer ID"',
            "[Column Name]",
            # Literals
            "'string'",
            "123",
            "123.45",
            "NULL",
            "TRUE",
            "FALSE",
            # Operators
            "a || b",
            "a + b",
            "a - b",
            "a * b",
            "a / b",
            "a = b",
            "a <> b",
            "a != b",
            "a < b",
            "a > b",
            "a <= b",
            "a >= b",
            "a AND b",
            "a OR b",
            "NOT a",
            # Parentheses
            "(a + b) * c",
            # CASE expressions
            "CASE WHEN a = 1 THEN 'x' ELSE 'y' END",
            "CASE WHEN a > 0 THEN a ELSE 0 END",
            # CAST expressions
            "CAST(a AS VARCHAR)",
            "CAST(123 AS INTEGER)",
            # Functions
            "COALESCE(a, b)",
            "NULLIF(a, 0)",
            "TRIM(name)",
            "UPPER(name)",
            "LOWER(name)",
            "SUBSTRING(name, 1, 5)",
            "LEFT(name, 3)",
            "RIGHT(name, 3)",
            "ABS(value)",
            "ROUND(value, 2)",
            "FLOOR(value)",
            "CEILING(value)",
            "LEN(name)",
            "LENGTH(name)",
            # Complex expressions
            "UPPER(TRIM(customer_id))",
            "order_id || '-' || line_number",
            "COALESCE(NULLIF(code, ''), 'UNKNOWN')",
        ],
    )
    def test_valid_expressions(self, expr: str) -> None:
        """Valid expressions return no diagnostics."""
        from dot.core.expression import validate_expr

        diagnostics = validate_expr(expr)
        assert diagnostics == [], f"Expected no diagnostics for '{expr}', got {diagnostics}"

    @pytest.mark.parametrize(
        "expr,expected_pattern",
        [
            # SELECT keyword
            ("SELECT customer_id FROM customers", "SELECT"),
            ("(SELECT x FROM y)", "SELECT"),
            # FROM clause
            ("x FROM table", "FROM"),
            # JOIN
            ("LEFT JOIN orders", "JOIN"),
            ("INNER JOIN", "JOIN"),
            # WHERE
            ("x WHERE y = 1", "WHERE"),
            # GROUP BY
            ("x GROUP BY y", "GROUP BY"),
            # ORDER BY
            ("x ORDER BY y", "ORDER BY"),
            # Subquery
            ("(SELECT x FROM y)", "SELECT"),
            # CTE
            ("WITH cte AS", "WITH"),
            # Non-deterministic functions
            ("RANDOM()", "RANDOM"),
            ("NEWID()", "NEWID"),
            ("GETDATE()", "GETDATE"),
            ("NOW()", "NOW"),
            ("CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP"),
            ("SYSDATE", "SYSDATE"),
            # DDL/DML
            ("INSERT INTO table", "INSERT"),
            ("UPDATE table SET", "UPDATE"),
            ("DELETE FROM table", "DELETE"),
            ("CREATE TABLE", "CREATE"),
            ("DROP TABLE", "DROP"),
            ("ALTER TABLE", "ALTER"),
            ("TRUNCATE TABLE", "TRUNCATE"),
        ],
    )
    def test_forbidden_patterns(self, expr: str, expected_pattern: str) -> None:
        """Forbidden patterns return HOOK-006 diagnostic."""
        from dot.core.expression import validate_expr
        from dot.models.diagnostic import Severity

        diagnostics = validate_expr(expr)
        assert len(diagnostics) >= 1, f"Expected diagnostic for '{expr}'"
        assert diagnostics[0].rule_id == "HOOK-006"
        assert diagnostics[0].severity == Severity.ERROR
        # The message should mention the forbidden pattern
        assert expected_pattern.lower() in diagnostics[0].message.lower() or "forbidden" in diagnostics[0].message.lower()

    def test_empty_expression_fails(self) -> None:
        """Empty expression returns diagnostic."""
        from dot.core.expression import validate_expr
        from dot.models.diagnostic import Severity

        diagnostics = validate_expr("")
        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-006"
        assert diagnostics[0].severity == Severity.ERROR

    def test_whitespace_only_expression_fails(self) -> None:
        """Whitespace-only expression returns diagnostic."""
        from dot.core.expression import validate_expr
        from dot.models.diagnostic import Severity

        diagnostics = validate_expr("   ")
        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-006"
        assert diagnostics[0].severity == Severity.ERROR
