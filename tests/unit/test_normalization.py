"""Unit tests for naming validators.

T016: Tests for naming validators (lower_snake_case, UPPER_SNAKE_CASE, hook_name, frame_name, semver)
"""

import pytest


class TestLowerSnakeCase:
    """Tests for is_lower_snake_case validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("customer", True),
            ("order_line", True),
            ("order_line_item", True),
            ("a", True),
            ("a1", True),
            ("abc123", True),
            ("abc_123", True),
            # Invalid cases
            ("Customer", False),
            ("CUSTOMER", False),
            ("order-line", False),
            ("order line", False),
            ("123abc", False),
            ("_customer", False),
            ("customer_", True),  # Trailing underscore is allowed
            ("", False),
            ("1", False),
        ],
    )
    def test_lower_snake_case(self, value: str, expected: bool) -> None:
        """Test lower_snake_case pattern matching."""
        from dot.core.normalization import is_lower_snake_case

        assert is_lower_snake_case(value) == expected


class TestUpperSnakeCase:
    """Tests for is_upper_snake_case validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("CRM", True),
            ("SAP", True),
            ("SAP_FIN", True),
            ("SAP_FIN_2", True),
            ("A", True),
            ("A1", True),
            ("ABC123", True),
            # Invalid cases
            ("crm", False),
            ("Crm", False),
            ("SAP-FIN", False),
            ("SAP FIN", False),
            ("123ABC", False),
            ("_CRM", False),
            ("", False),
            ("1", False),
        ],
    )
    def test_upper_snake_case(self, value: str, expected: bool) -> None:
        """Test UPPER_SNAKE_CASE pattern matching."""
        from dot.core.normalization import is_upper_snake_case

        assert is_upper_snake_case(value) == expected


class TestHookName:
    """Tests for is_valid_hook_name validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            # Strong hooks
            ("_hk__customer", True),
            ("_hk__order", True),
            ("_hk__order_line", True),
            ("_hk__employee__manager", True),
            ("_hk__order__billing", True),
            # Weak hooks
            ("_wk__ref__genre", True),
            ("_wk__epoch__dob", True),
            ("_wk__date", True),
            # Invalid cases
            ("_hk_customer", False),  # Single underscore
            ("hk__customer", False),  # Missing leading underscore
            ("_HK__customer", False),  # Uppercase prefix
            ("_hk__Customer", False),  # Uppercase concept
            ("_hk__", False),  # Missing concept
            ("_hk__customer__", False),  # Trailing double underscore
            ("customer", False),  # No prefix
            ("_xx__customer", False),  # Wrong prefix
            ("", False),
        ],
    )
    def test_hook_name(self, value: str, expected: bool) -> None:
        """Test hook name pattern matching."""
        from dot.core.normalization import is_valid_hook_name

        assert is_valid_hook_name(value) == expected


class TestFrameName:
    """Tests for is_valid_frame_name validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("frame.customer", True),
            ("psa.order", True),
            ("staging.order_header", True),
            ("dw.fact_order", True),
            ("a.b", True),
            ("schema1.table2", True),
            # Invalid cases
            ("customer", False),  # No dot
            ("frame..customer", False),  # Double dot
            (".customer", False),  # Leading dot
            ("frame.", False),  # Trailing dot
            ("Frame.customer", False),  # Uppercase
            ("frame.Customer", False),  # Uppercase
            ("frame-customer", False),  # Hyphen
            ("frame customer", False),  # Space
            ("", False),
            ("frame.order.line", False),  # Multiple dots
        ],
    )
    def test_frame_name(self, value: str, expected: bool) -> None:
        """Test frame name pattern matching."""
        from dot.core.normalization import is_valid_frame_name

        assert is_valid_frame_name(value) == expected


class TestSemver:
    """Tests for is_valid_semver validator."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1.0.0", True),
            ("0.1.0", True),
            ("2.1.3", True),
            ("10.20.30", True),
            ("0.0.0", True),
            # Invalid cases
            ("1.0", False),  # Missing patch
            ("1", False),  # Only major
            ("1.0.0.0", False),  # Extra component
            ("v1.0.0", False),  # Leading 'v'
            ("1.0.0-alpha", False),  # Pre-release (not allowed per spec)
            ("1.0.0+build", False),  # Build metadata (not allowed per spec)
            ("1.0.0-alpha+build", False),  # Both
            ("", False),
            ("a.b.c", False),
            ("1.0.x", False),
        ],
    )
    def test_semver(self, value: str, expected: bool) -> None:
        """Test semver pattern matching."""
        from dot.core.normalization import is_valid_semver

        assert is_valid_semver(value) == expected
