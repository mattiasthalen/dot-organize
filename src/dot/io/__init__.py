"""Thin I/O layer for YAML and JSON serialization."""

from dot.io.json import (
    dump_manifest_json,
    load_manifest_json,
    parse_json,
)
from dot.io.yaml import (
    ParseError,
    dump_manifest_yaml,
    load_manifest_yaml,
    parse_yaml,
)

__all__ = [
    # YAML
    "ParseError",
    "parse_yaml",
    "load_manifest_yaml",
    "dump_manifest_yaml",
    # JSON
    "parse_json",
    "load_manifest_json",
    "dump_manifest_json",
]
