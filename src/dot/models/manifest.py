"""Manifest and Metadata models.

Spec Reference: spec.md#manifest-schema-v1, FR-030, FR-031
"""

from datetime import datetime

from pydantic import BaseModel

from dot.models.concept import Concept
from dot.models.frame import Frame
from dot.models.settings import Settings


class Metadata(BaseModel, frozen=True):
    """Manifest metadata.

    Attributes:
        name: Human-readable name
        description: Optional description
        created_at: ISO 8601 timestamp
        updated_at: ISO 8601 timestamp
    """

    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class Manifest(BaseModel, frozen=True):
    """Root manifest model.

    Attributes:
        manifest_version: User-controlled version (semver)
        schema_version: Manifest schema version (semver)
        metadata: Name, description, timestamps
        settings: Hook prefixes, delimiter
        frames: List of frames (at least one)
        concepts: Optional enrichment definitions
    """

    manifest_version: str
    schema_version: str
    metadata: Metadata
    settings: Settings
    frames: list[Frame]
    concepts: list[Concept] = []
