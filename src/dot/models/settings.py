"""Settings model for manifest configuration.

Spec Reference: spec.md#manifest-schema-v1, FR-038
"""

from pydantic import BaseModel


class Settings(BaseModel, frozen=True):
    """Manifest settings for hook naming conventions.

    Attributes:
        hook_prefix: Prefix for strong hooks (default: "_hk__")
        weak_hook_prefix: Prefix for weak hooks (default: "_wk__")
        delimiter: Separator between key set and business key (default: "|")
    """

    hook_prefix: str = "_hk__"
    weak_hook_prefix: str = "_wk__"
    delimiter: str = "|"
