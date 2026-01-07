"""Concept model for business concept definitions.

Spec Reference: spec.md#manifest-schema-v1, FR-037
"""

from pydantic import BaseModel


class Concept(BaseModel, frozen=True):
    """Business concept definition with frame references.

    Attributes:
        name: Concept name (derived from hooks)
        frames: Tuple of frame names where this concept appears
        description: Optional enrichment text
        examples: Real-world examples
        is_weak: True if derived from _wk__ hook prefix
    """

    name: str
    frames: tuple[str, ...] = ()
    description: str = ""
    examples: tuple[str, ...] = ()
    is_weak: bool = False
