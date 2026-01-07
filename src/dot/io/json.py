"""JSON I/O for HOOK manifests.

T065-T066: Implement JSON reader and writer
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from dot.models.manifest import Manifest

if TYPE_CHECKING:
    from typing import Literal


def parse_json(path: Path) -> dict[str, Any]:
    """Parse JSON file and return dictionary.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed dictionary.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If JSON syntax is invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return data


@overload
def load_manifest_json(
    path: Path,
    *,
    return_raw: Literal[False] = False,
) -> Manifest: ...


@overload
def load_manifest_json(
    path: Path,
    *,
    return_raw: Literal[True],
) -> tuple[Manifest, dict[str, Any]]: ...


def load_manifest_json(
    path: Path,
    *,
    return_raw: bool = False,
) -> Manifest | tuple[Manifest, dict[str, Any]]:
    """Load and validate manifest from JSON file.

    Args:
        path: Path to JSON manifest file.
        return_raw: If True, also return the raw dict for unknown field detection.

    Returns:
        Manifest object, or tuple of (Manifest, raw_data) if return_raw=True.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If JSON syntax is invalid.
        pydantic.ValidationError: If data does not match schema.
    """
    raw_data = parse_json(path)
    manifest = Manifest.model_validate(raw_data)

    if return_raw:
        return manifest, raw_data
    return manifest


def dump_manifest_json(
    manifest: Manifest,
    path: Path | None = None,
    *,
    indent: int = 2,
) -> str | None:
    """Serialize manifest to JSON.

    Args:
        manifest: Manifest to serialize.
        path: Optional path to write to. If None, returns string.
        indent: Indentation level for pretty-printing (default 2).

    Returns:
        JSON string if path is None, otherwise None (writes to file).
    """
    # Use Pydantic's model_dump for serialization
    data = manifest.model_dump(mode="json", exclude_none=True)

    json_str = json.dumps(data, indent=indent, ensure_ascii=False)

    if path is None:
        return json_str

    with path.open("w", encoding="utf-8") as f:
        f.write(json_str)
        f.write("\n")  # Trailing newline

    return None
