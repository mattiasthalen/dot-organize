"""YAML I/O for manifests.

T062-T064: Implement YAML reader, parse error handling, and writer

Uses ruamel.yaml for ordered key output per data-model.md
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from dot.models.manifest import Manifest

if TYPE_CHECKING:
    from typing import Literal


class ParseError(Exception):
    """YAML parsing error with location information."""

    def __init__(
        self,
        message: str,
        file_path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Initialize a ParseError with optional location information.

        Args:
            message: Description of the parsing error.
            file_path: Path to the file being parsed.
            line: Line number where the error occurred (1-indexed).
            column: Column number where the error occurred (1-indexed).
        """
        self.message = message
        self.file_path = file_path
        self.line = line
        self.column = column
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with location information."""
        parts = []
        if self.file_path:
            parts.append(str(self.file_path))
        if self.line is not None:
            if self.column is not None:
                parts.append(f"line {self.line}, column {self.column}")
            else:
                parts.append(f"line {self.line}")
        location = " at ".join(filter(None, parts[:1] + parts[1:2]))
        if location:
            return f"{location}: {self.message}"
        return self.message


def _create_yaml() -> YAML:
    """Create configured YAML instance.

    Configures ruamel.yaml to:
    - Preserve key order (default mapping)
    - Use block style (not flow style)
    - No !!omap tags (standard dict output)
    """
    yaml = YAML()
    yaml.default_flow_style = False
    # Use default_style=None to avoid !omap tags
    return yaml


def _convert_ordered_dict_to_dict(data: Any) -> Any:
    """Recursively convert OrderedDict to regular dict for serialization.

    This ensures ruamel.yaml outputs regular mappings without !!omap tags.
    """
    from collections import OrderedDict

    if isinstance(data, dict | OrderedDict):
        return {k: _convert_ordered_dict_to_dict(v) for k, v in data.items()}
    elif isinstance(data, list | tuple):
        return [_convert_ordered_dict_to_dict(item) for item in data]
    return data


def parse_yaml(path: Path) -> dict[str, Any]:
    """Parse YAML file and return dictionary.

    Args:
        path: Path to YAML file.

    Returns:
        Parsed dictionary with preserved key order.

    Raises:
        FileNotFoundError: If file does not exist.
        ParseError: If YAML syntax is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    yaml = _create_yaml()

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.load(f)
    except YAMLError as e:
        # Extract line/column from ruamel.yaml error
        line = None
        column = None
        if hasattr(e, "problem_mark") and e.problem_mark is not None:
            line = e.problem_mark.line + 1  # Convert to 1-based
            column = e.problem_mark.column + 1
        raise ParseError(
            message=str(e),
            file_path=path,
            line=line,
            column=column,
        ) from e

    if data is None:
        raise ParseError(
            message="Empty YAML file",
            file_path=path,
            line=1,
            column=1,
        )

    return dict(data)


@overload
def load_manifest_yaml(
    path: Path,
    *,
    return_raw: Literal[False] = False,
) -> Manifest:
    """Overload: Load manifest only."""
    ...


@overload
def load_manifest_yaml(
    path: Path,
    *,
    return_raw: Literal[True],
) -> tuple[Manifest, dict[str, Any]]:
    """Overload: Load manifest and return raw data."""
    ...


def load_manifest_yaml(
    path: Path,
    *,
    return_raw: bool = False,
) -> Manifest | tuple[Manifest, dict[str, Any]]:
    """Load and validate manifest from YAML file.

    Args:
        path: Path to YAML manifest file.
        return_raw: If True, also return the raw dict for unknown field detection.

    Returns:
        Manifest object, or tuple of (Manifest, raw_data) if return_raw=True.

    Raises:
        FileNotFoundError: If file does not exist.
        ParseError: If YAML syntax is invalid.
        pydantic.ValidationError: If data does not match schema.
    """
    raw_data = parse_yaml(path)
    manifest = Manifest.model_validate(raw_data)

    if return_raw:
        return manifest, raw_data
    return manifest


def dump_manifest_yaml(manifest: Manifest, path: Path | None = None) -> str | None:
    """Serialize manifest to YAML.

    Args:
        manifest: Manifest to serialize.
        path: Optional path to write to. If None, returns string.

    Returns:
        YAML string if path is None, otherwise None (writes to file).
    """
    yaml = _create_yaml()

    # Convert to dict with proper key order, then to regular dicts to avoid !!omap
    ordered_data = _manifest_to_ordered_dict(manifest)
    data = _convert_ordered_dict_to_dict(ordered_data)

    if path is None:
        from io import StringIO

        stream = StringIO()
        yaml.dump(data, stream)
        return stream.getvalue()

    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    return None


def _manifest_to_ordered_dict(manifest: Manifest) -> dict[str, Any]:
    """Convert Manifest to ordered dict for serialization.

    Key order follows data-model.md specification.
    """
    from collections import OrderedDict

    result: dict[str, Any] = OrderedDict()

    # Top-level fields in order
    result["manifest_version"] = manifest.manifest_version
    result["schema_version"] = manifest.schema_version

    # Optional metadata
    if manifest.metadata is not None:
        result["metadata"] = _metadata_to_dict(manifest.metadata)

    # Optional settings (only if non-default)
    if manifest.settings is not None:
        settings_dict = _settings_to_dict(manifest.settings)
        if settings_dict:  # Only include if non-empty
            result["settings"] = settings_dict

    # Frames
    result["frames"] = [_frame_to_dict(f) for f in manifest.frames]

    # Concepts (FR-037)
    result["concepts"] = [_concept_to_dict(c) for c in manifest.concepts]

    # KeySets (FR-039)
    result["keysets"] = [_keyset_to_dict(ks) for ks in manifest.keysets]

    return result


def _metadata_to_dict(metadata: Any) -> dict[str, Any]:
    """Convert Metadata to dict."""
    result: dict[str, Any] = {}
    if metadata.name:
        result["name"] = metadata.name
    if metadata.description:
        result["description"] = metadata.description
    if metadata.owner:
        result["owner"] = metadata.owner
    if metadata.version:
        result["version"] = metadata.version
    if metadata.tags:
        result["tags"] = list(metadata.tags)
    return result


def _settings_to_dict(settings: Any) -> dict[str, Any]:
    """Convert Settings to dict (only non-default values)."""
    from dot.models.settings import Settings

    defaults = Settings()
    result: dict[str, Any] = {}

    if settings.hook_prefix != defaults.hook_prefix:
        result["hook_prefix"] = settings.hook_prefix
    if settings.weak_hook_prefix != defaults.weak_hook_prefix:
        result["weak_hook_prefix"] = settings.weak_hook_prefix
    if settings.delimiter != defaults.delimiter:
        result["delimiter"] = settings.delimiter

    return result


def _frame_to_dict(frame: Any) -> dict[str, Any]:
    """Convert Frame to dict."""
    result: dict[str, Any] = {"name": frame.name}

    if frame.source:
        source_dict: dict[str, Any] = {}
        if frame.source.relation:
            source_dict["relation"] = frame.source.relation
        if frame.source.path:
            source_dict["path"] = frame.source.path
        result["source"] = source_dict

    result["hooks"] = [_hook_to_dict(h) for h in frame.hooks]

    return result


def _hook_to_dict(hook: Any) -> dict[str, Any]:
    """Convert Hook to dict."""
    result: dict[str, Any] = {
        "name": hook.name,
        "role": hook.role.value,
        "concept": hook.concept,
        "source": hook.source,
        "expr": hook.expr,
    }

    # Optional fields
    if hook.qualifier:
        result["qualifier"] = hook.qualifier
    if hook.tenant:
        result["tenant"] = hook.tenant

    return result


def _concept_to_dict(concept: Any) -> dict[str, Any]:
    """Convert Concept to dict."""
    result: dict[str, Any] = {"name": concept.name}

    # Frames list (FR-037a)
    if concept.frames:
        result["frames"] = list(concept.frames)

    if concept.description:
        result["description"] = concept.description
    if concept.examples:
        result["examples"] = list(concept.examples)
    if concept.is_weak:
        result["is_weak"] = concept.is_weak

    return result


def _keyset_to_dict(keyset: Any) -> dict[str, Any]:
    """Convert KeySet to dict (FR-039)."""
    result: dict[str, Any] = {
        "name": keyset.name,
        "concept": keyset.concept,
    }

    if keyset.frames:
        result["frames"] = list(keyset.frames)

    return result
