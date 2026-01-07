"""Manifest and Metadata models.

Spec Reference: spec.md#manifest-schema-v1, FR-030, FR-031
"""

from datetime import datetime

from pydantic import BaseModel, Field

from dot.models.concept import Concept
from dot.models.frame import Frame
from dot.models.settings import Settings


class Metadata(BaseModel, frozen=True):
    """Manifest metadata.

    Attributes:
        name: Human-readable name
        description: Optional description
        owner: Optional owner contact
        version: Optional version string
        tags: Optional list of tags
        created_at: ISO 8601 timestamp (optional)
        updated_at: ISO 8601 timestamp (optional)
    """

    name: str | None = None
    description: str | None = None
    owner: str | None = None
    version: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Manifest(BaseModel, frozen=True):
    """Root manifest model.

    Attributes:
        manifest_version: User-controlled version (semver)
        schema_version: Manifest schema version (semver)
        metadata: Name, description, timestamps (optional)
        settings: Hook prefixes, delimiter (uses defaults if not specified)
        frames: List of frames (at least one)
        concepts: Optional enrichment definitions
    """

    manifest_version: str
    schema_version: str
    metadata: Metadata | None = None
    settings: Settings = Field(default_factory=Settings)
    frames: list[Frame]
    concepts: list[Concept] = Field(default_factory=list)
