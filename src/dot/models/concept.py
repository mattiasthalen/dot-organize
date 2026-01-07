"""Concept model for business concept definitions.

Spec Reference: spec.md#manifest-schema-v1, FR-037
"""

from pydantic import BaseModel


class Concept(BaseModel, frozen=True):
    """Business concept definition for enrichment.

    Attributes:
        name: Concept name (must match a concept used in frames)
        description: 1-2 sentence definition
        examples: Real-world examples
        is_weak: True for reference/time concepts
    """

    name: str
    description: str
    examples: list[str] = []
    is_weak: bool = False
