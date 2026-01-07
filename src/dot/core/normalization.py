"""Naming convention validators.

T026: Implement naming validators (is_lower_snake_case, is_upper_snake_case,
is_valid_hook_name, is_valid_frame_name, is_valid_semver)

Spec Reference: data-model.md §Naming Conventions
"""

import re

# Compiled regex patterns for performance
# lower_snake_case: starts with letter, followed by letters/digits/underscores,
# ending with letter/digit
LOWER_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
UPPER_SNAKE_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
# Hook name: _hk__<concept> or _wk__<concept> optionally followed by __<qualifier>
# concept and qualifier must be lower_snake_case without trailing underscore
HOOK_NAME = re.compile(
    r"^_(hk|wk)__[a-z][a-z0-9]*(_[a-z0-9]+)*(__[a-z][a-z0-9]*(_[a-z0-9]+)*)?$"
)
FRAME_NAME = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def is_lower_snake_case(s: str) -> bool:
    """Check if string matches lower_snake_case pattern.

    Examples: customer, order_line, abc_123
    """
    if not s:
        return False
    return bool(LOWER_SNAKE_CASE.match(s))


def is_upper_snake_case(s: str) -> bool:
    """Check if string matches UPPER_SNAKE_CASE pattern.

    Examples: CRM, SAP, SAP_FIN
    """
    if not s:
        return False
    return bool(UPPER_SNAKE_CASE.match(s))


def is_valid_hook_name(s: str) -> bool:
    """Check if string matches hook name pattern.

    Pattern: <prefix><concept>[__<qualifier>]
    Examples: _hk__customer, _hk__employee__manager, _wk__ref__genre
    """
    if not s:
        return False
    return bool(HOOK_NAME.match(s))


def is_valid_frame_name(s: str) -> bool:
    """Check if string matches frame name pattern.

    Pattern: <schema>.<table> in lower_snake_case
    Examples: frame.customer, psa.order, staging.order_header
    """
    if not s:
        return False
    return bool(FRAME_NAME.match(s))


def is_valid_semver(s: str) -> bool:
    """Check if string matches semver pattern (MAJOR.MINOR.PATCH only).

    Pre-release and build metadata are NOT allowed per spec.
    Examples: 1.0.0, 0.1.0, 2.1.3
    """
    if not s:
        return False
    return bool(SEMVER.match(s))
