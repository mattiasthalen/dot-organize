"""T059: Tests for JSON I/O reader/writer.

TDD - Write tests FIRST, must FAIL before implementation
"""

from pathlib import Path
from textwrap import dedent

import pytest

from dot.io.json import (
    dump_manifest_json,
    load_manifest_json,
    parse_json,
)


class TestJsonReader:
    """Tests for JSON parsing and manifest loading."""

    def test_parse_valid_json_returns_dict(self, tmp_path: Path) -> None:
        """Parse valid JSON file returns dictionary."""
        json_content = dedent("""\
            {
                "manifest_version": "1.0.0",
                "schema_version": "1.0.0",
                "frames": [],
                "concepts": []
            }
        """)
        json_file = tmp_path / "test.json"
        json_file.write_text(json_content)

        result = parse_json(json_file)

        assert isinstance(result, dict)
        assert result["manifest_version"] == "1.0.0"

    def test_load_manifest_json_returns_manifest(self, tmp_path: Path) -> None:
        """Load valid manifest JSON returns Manifest object."""
        json_content = dedent("""\
            {
                "manifest_version": "1.0.0",
                "schema_version": "1.0.0",
                "frames": [
                    {
                        "name": "psa.customer",
                        "source": {"relation": "psa.customer"},
                        "hooks": [
                            {
                                "name": "_hk__customer",
                                "role": "primary",
                                "concept": "customer",
                                "source": "CRM",
                                "expr": "customer_id"
                            }
                        ]
                    }
                ],
                "concepts": [
                    {
                        "name": "customer",
                        "description": "A customer entity for testing"
                    }
                ]
            }
        """)
        json_file = tmp_path / "manifest.json"
        json_file.write_text(json_content)

        manifest = load_manifest_json(json_file)

        assert manifest.manifest_version == "1.0.0"
        assert len(manifest.frames) == 1
        assert len(manifest.concepts) == 1

    def test_load_manifest_json_with_raw_data(self, tmp_path: Path) -> None:
        """Load manifest returns both Manifest and raw dict."""
        json_content = dedent("""\
            {
                "manifest_version": "1.0.0",
                "schema_version": "1.0.0",
                "frames": [],
                "concepts": [],
                "unknown_field": true
            }
        """)
        json_file = tmp_path / "manifest.json"
        json_file.write_text(json_content)

        manifest, raw_data = load_manifest_json(json_file, return_raw=True)

        assert manifest is not None
        assert "unknown_field" in raw_data


class TestJsonParseErrors:
    """Tests for JSON parse error handling."""

    def test_invalid_json_syntax_raises_error(self, tmp_path: Path) -> None:
        """Invalid JSON syntax raises JSONDecodeError."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text('{"invalid": json}')

        from json import JSONDecodeError

        with pytest.raises(JSONDecodeError):
            parse_json(json_file)

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Non-existent file raises FileNotFoundError."""
        json_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            parse_json(json_file)


class TestJsonWriter:
    """Tests for JSON output."""

    def test_dump_manifest_json_creates_file(self, tmp_path: Path) -> None:
        """Dump manifest to JSON creates valid JSON file."""
        from dot.models.manifest import Manifest

        # Create a minimal manifest
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        output_path = tmp_path / "output.json"
        dump_manifest_json(manifest, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "manifest_version" in content
        assert "1.0.0" in content

    def test_dump_manifest_json_is_valid_json(self, tmp_path: Path) -> None:
        """Dumped JSON can be parsed back."""
        import json

        from dot.models.manifest import Manifest

        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        output_path = tmp_path / "output.json"
        dump_manifest_json(manifest, output_path)

        # Should parse without error
        content = output_path.read_text()
        parsed = json.loads(content)
        assert parsed["manifest_version"] == "1.0.0"

    def test_dump_manifest_json_is_formatted(self, tmp_path: Path) -> None:
        """Dumped JSON is pretty-printed with indentation."""
        from dot.models.manifest import Manifest

        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        output_path = tmp_path / "output.json"
        dump_manifest_json(manifest, output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")
        # Pretty-printed JSON has multiple lines
        assert len(lines) > 1

    def test_dump_manifest_returns_string_if_no_path(self) -> None:
        """Dump manifest without path returns JSON string."""
        from dot.models.manifest import Manifest

        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        result = dump_manifest_json(manifest)

        assert isinstance(result, str)
        assert "manifest_version" in result
