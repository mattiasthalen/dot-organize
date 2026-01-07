"""Pure validation functions for HOOK manifests."""

from dot.core.expression import validate_expr
from dot.core.normalization import (
    is_lower_snake_case,
    is_upper_snake_case,
    is_valid_frame_name,
    is_valid_hook_name,
    is_valid_semver,
)
from dot.core.registry import (
    derive_concepts,
    derive_hook_registry,
    derive_key_sets,
)
from dot.core.validation import (
    filter_errors,
    filter_warnings,
    has_errors,
    validate_manifest,
)

__all__ = [
    # normalization
    "is_lower_snake_case",
    "is_upper_snake_case",
    "is_valid_frame_name",
    "is_valid_hook_name",
    "is_valid_semver",
    # registry
    "derive_concepts",
    "derive_hook_registry",
    "derive_key_sets",
    # expression
    "validate_expr",
    # validation
    "validate_manifest",
    "has_errors",
    "filter_errors",
    "filter_warnings",
]
