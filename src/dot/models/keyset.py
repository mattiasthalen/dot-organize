"""KeySet model for auto-derived key set entries.

Spec Reference: spec.md#manifest-schema-v1, FR-039
"""

from pydantic import BaseModel


class KeySet(BaseModel, frozen=True):
    """Auto-derived key set with frame references.

    Attributes:
        name: Key set string (e.g., "CUSTOMER@CRM", "ORDER~BILLING@SAP~EU")
        concept: Business concept this key set belongs to
        frames: Tuple of frame names where this key set is derived
    """

    name: str
    concept: str
    frames: tuple[str, ...] = ()
