"""T058: Tests for YAML I/O reader.

TDD - Write tests FIRST, must FAIL before implementation
"""

from pathlib import Path
from textwrap import dedent

import pytest
from dot.io.yaml import (
    ParseError,
    load_manifest_yaml,
    parse_yaml,
)


class TestYamlReader:
    """Tests for YAML parsing and manifest loading."""

    def test_parse_valid_yaml_returns_dict(self, tmp_path: Path) -> None:
        """Parse valid YAML file returns dictionary."""
        yaml_content = dedent("""\
            manifest_version: "1.0.0"
            schema_version: "1.0.0"
            frames: []
            concepts: []
        """)
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_yaml(yaml_file)

        assert isinstance(result, dict)
        assert result["manifest_version"] == "1.0.0"

    def test_parse_preserves_key_order(self, tmp_path: Path) -> None:
        """YAML parsing preserves key order for ordered output."""
        yaml_content = dedent("""\
            manifest_version: "1.0.0"
            schema_version: "1.0.0"
            metadata:
              name: "test"
            frames: []
            concepts: []
        """)
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        result = parse_yaml(yaml_file)
        keys = list(result.keys())

        assert keys[0] == "manifest_version"
        assert keys[1] == "schema_version"
        assert keys[2] == "metadata"

    def test_load_manifest_yaml_returns_manifest(self, valid_manifest_path: Path) -> None:
        """Load valid manifest YAML returns Manifest object."""
        manifest = load_manifest_yaml(valid_manifest_path)

        assert manifest.manifest_version == "1.0.0"
        assert len(manifest.frames) > 0
        assert len(manifest.concepts) > 0

    def test_load_manifest_yaml_also_returns_raw_data(self, valid_manifest_path: Path) -> None:
        """Load manifest returns both Manifest and raw dict for unknown field detection."""
        manifest, raw_data = load_manifest_yaml(valid_manifest_path, return_raw=True)

        assert manifest is not None
        assert isinstance(raw_data, dict)
        assert "manifest_version" in raw_data


class TestYamlParseErrors:
    """Tests for YAML parse error handling with line/column info."""

    def test_invalid_yaml_syntax_raises_parse_error(self, tmp_path: Path) -> None:
        """Invalid YAML syntax raises ParseError with location."""
        yaml_content = dedent("""\
            manifest_version: "1.0.0"
            frames:
              - name: "test"
                hooks:
                  - invalid: yaml: syntax
        """)
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ParseError) as exc_info:
            parse_yaml(yaml_file)

        error = exc_info.value
        assert error.line is not None
        assert error.column is not None

    def test_parse_error_includes_file_path(self, tmp_path: Path) -> None:
        """ParseError includes the file path that caused the error."""
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("invalid: yaml: :")

        with pytest.raises(ParseError) as exc_info:
            parse_yaml(yaml_file)

        assert str(yaml_file) in str(exc_info.value)

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Non-existent file raises FileNotFoundError."""
        yaml_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            parse_yaml(yaml_file)

    def test_empty_file_raises_parse_error(self, tmp_path: Path) -> None:
        """Empty YAML file raises ParseError."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("")

        with pytest.raises(ParseError):
            parse_yaml(yaml_file)

    def test_parse_error_message_is_helpful(self, tmp_path: Path) -> None:
        """ParseError message includes helpful context."""
        # Use invalid YAML that causes a parse error (duplicate key or bad indentation)
        yaml_content = dedent("""\
            manifest_version: "1.0.0"
            frames:
                - name: test
                    hooks:  # bad indentation
                  - bad indent here
        """)
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text(yaml_content)

        with pytest.raises(ParseError) as exc_info:
            parse_yaml(yaml_file)

        # Error message should be understandable
        error_msg = str(exc_info.value)
        assert len(error_msg) > 10  # Not just a cryptic message


class TestYamlValidation:
    """Tests for YAML validation against Pydantic models."""

    def test_invalid_manifest_data_raises_validation_error(self, tmp_path: Path) -> None:
        """Invalid manifest data raises validation error with field info."""
        # Valid YAML syntax but invalid manifest data
        yaml_content = dedent("""\
            manifest_version: 123
            schema_version: "1.0.0"
            frames: []
            concepts: []
        """)
        yaml_file = tmp_path / "invalid_data.yaml"
        yaml_file.write_text(yaml_content)

        # Should raise due to manifest_version being int instead of string
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            load_manifest_yaml(yaml_file)


@pytest.fixture
def valid_manifest_path() -> Path:
    """Return path to a valid minimal manifest fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "valid" / "minimal.yaml"
    return fixture_path
