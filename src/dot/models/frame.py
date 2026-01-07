"""Frame and Hook models.

Spec Reference: spec.md#manifest-schema-v1, FR-032, FR-033, FR-034, FR-035
"""

from __future__ import annotations

import sys
from enum import Enum

from pydantic import BaseModel, model_validator

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class HookRole(str, Enum):
    """Role of a hook within a frame."""

    PRIMARY = "primary"  # Defines frame grain
    FOREIGN = "foreign"  # References other concept


class Hook(BaseModel, frozen=True):
    """Hook definition for business key derivation.

    Attributes:
        name: Hook column name (e.g., "_hk__customer")
        role: "primary" or "foreign"
        concept: Business concept (e.g., "customer")
        qualifier: Optional qualifier suffix (e.g., "manager")
        source: Source system (e.g., "CRM")
        tenant: Optional tenant (e.g., "AU")
        expr: SQL expression (Manifest SQL subset)
    """

    name: str
    role: HookRole
    concept: str
    qualifier: str | None = None
    source: str
    tenant: str | None = None
    expr: str


class Source(BaseModel, frozen=True):
    """Frame source specification.

    Exactly one of relation or path must be set.

    Attributes:
        relation: Relational source (e.g., "db.schema.table")
        path: File source (e.g., QVD path)
    """

    relation: str | None = None
    path: str | None = None

    @model_validator(mode="after")
    def validate_exclusivity(self) -> Self:
        """Ensure exactly one of relation or path is set."""
        has_relation = self.relation is not None
        has_path = self.path is not None

        if has_relation and has_path:
            raise ValueError(
                "Source must have exactly one of 'relation' or 'path', not both"
            )
        if not has_relation and not has_path:
            raise ValueError("Source must have exactly one of 'relation' or 'path'")

        return self


class Frame(BaseModel, frozen=True):
    """Frame definition wrapping a source with hooks.

    Attributes:
        name: Frame name (e.g., "frame.customer")
        source: Source specification (relation OR path)
        description: Optional description
        hooks: List of hooks (at least one required)
    """

    name: str
    source: Source
    description: str | None = None
    hooks: list[Hook]
