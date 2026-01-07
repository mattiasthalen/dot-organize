"""T061: CLI integration tests for validate command.

TDD - Write tests FIRST, must FAIL before implementation
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from dot.cli.main import app

runner = CliRunner()


class TestValidateCommandSuccess:
    """Tests for successful validation scenarios."""

    def test_valid_manifest_exits_0(self, valid_manifest_path: Path) -> None:
        """Valid manifest exits with code 0."""
        result = runner.invoke(app, ["validate", str(valid_manifest_path)])

        assert result.exit_code == 0

    def test_valid_manifest_shows_success_message(
        self, valid_manifest_path: Path
    ) -> None:
        """Valid manifest shows success message."""
        result = runner.invoke(app, ["validate", str(valid_manifest_path)])

        assert "valid" in result.stdout.lower()

    def test_manifest_with_warnings_exits_0(self, warn_manifest_path: Path) -> None:
        """Manifest with only warnings exits with code 0."""
        result = runner.invoke(app, ["validate", str(warn_manifest_path)])

        # Warnings should not cause failure
        assert result.exit_code == 0

    def test_manifest_with_warnings_shows_warnings(
        self, warn_manifest_path: Path
    ) -> None:
        """Manifest with warnings shows warning messages."""
        result = runner.invoke(app, ["validate", str(warn_manifest_path)])

        # Should mention WARN
        assert "WARN" in result.stdout or "warning" in result.stdout.lower()


class TestValidateCommandErrors:
    """Tests for validation error scenarios."""

    def test_invalid_manifest_exits_1(self, invalid_manifest_path: Path) -> None:
        """Invalid manifest exits with code 1."""
        result = runner.invoke(app, ["validate", str(invalid_manifest_path)])

        assert result.exit_code == 1

    def test_invalid_manifest_shows_error_rule_id(
        self, invalid_manifest_path: Path
    ) -> None:
        """Invalid manifest shows rule ID in error message."""
        result = runner.invoke(app, ["validate", str(invalid_manifest_path)])

        # Should contain rule ID like FRAME-001, HOOK-002, etc.
        assert any(
            rule in result.stdout
            for rule in ["FRAME-", "HOOK-", "CONCEPT-", "MANIFEST-"]
        )

    def test_invalid_manifest_shows_path(self, invalid_manifest_path: Path) -> None:
        """Invalid manifest shows path to problematic field."""
        result = runner.invoke(app, ["validate", str(invalid_manifest_path)])

        # Should contain field path like "frames[0].hooks"
        assert "." in result.stdout or "[" in result.stdout

    def test_parse_error_shows_line_column(self, tmp_path: Path) -> None:
        """YAML parse error shows line and column."""
        yaml_file = tmp_path / "bad.yaml"
        yaml_file.write_text("invalid: yaml: :")

        result = runner.invoke(app, ["validate", str(yaml_file)])

        assert result.exit_code == 1
        # Should contain line reference in output (may be stderr)
        output = result.output  # Combined stdout + stderr
        assert "line" in output.lower() or ":" in output


class TestValidateCommandUsageErrors:
    """Tests for usage errors."""

    def test_file_not_found_exits_2(self, tmp_path: Path) -> None:
        """Non-existent file exits with code 2."""
        result = runner.invoke(app, ["validate", str(tmp_path / "nonexistent.yaml")])

        assert result.exit_code == 2

    def test_file_not_found_shows_error(self, tmp_path: Path) -> None:
        """Non-existent file shows clear error message."""
        path = tmp_path / "nonexistent.yaml"
        result = runner.invoke(app, ["validate", str(path)])

        output = result.output  # Combined stdout + stderr
        assert "not found" in output.lower() or "does not exist" in output.lower()


class TestValidateCommandJsonOutput:
    """Tests for --json flag machine-readable output."""

    def test_json_flag_outputs_json(self, valid_manifest_path: Path) -> None:
        """--json flag outputs valid JSON."""
        import json

        result = runner.invoke(app, ["validate", str(valid_manifest_path), "--json"])

        # Should be parseable JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_json_output_has_valid_field(self, valid_manifest_path: Path) -> None:
        """JSON output has 'valid' boolean field."""
        import json

        result = runner.invoke(app, ["validate", str(valid_manifest_path), "--json"])

        output = json.loads(result.stdout)
        assert "valid" in output
        assert output["valid"] is True

    def test_json_output_has_errors_field(self, invalid_manifest_path: Path) -> None:
        """JSON output has 'errors' array for invalid manifest."""
        import json

        result = runner.invoke(app, ["validate", str(invalid_manifest_path), "--json"])

        output = json.loads(result.stdout)
        assert "errors" in output
        assert isinstance(output["errors"], list)
        assert len(output["errors"]) > 0

    def test_json_output_error_has_rule_id(self, invalid_manifest_path: Path) -> None:
        """JSON error object has rule_id field."""
        import json

        result = runner.invoke(app, ["validate", str(invalid_manifest_path), "--json"])

        output = json.loads(result.stdout)
        error = output["errors"][0]
        assert "rule_id" in error


class TestValidateCommandAccessibility:
    """Tests for accessibility (NFR-010)."""

    def test_default_output_no_ansi_escapes(self, valid_manifest_path: Path) -> None:
        """Default output contains no ANSI escape codes for screen reader compatibility."""
        result = runner.invoke(app, ["validate", str(valid_manifest_path)])

        # ANSI escape codes start with \x1b[
        assert "\x1b[" not in result.stdout

    def test_no_color_flag_disables_colors(self, valid_manifest_path: Path) -> None:
        """--no-color flag disables ANSI escape codes."""
        result = runner.invoke(
            app, ["validate", str(valid_manifest_path), "--no-color"]
        )

        assert "\x1b[" not in result.stdout


@pytest.fixture
def valid_manifest_path() -> Path:
    """Return path to a valid minimal manifest fixture."""
    return Path(__file__).parent.parent / "fixtures" / "valid" / "minimal.yaml"


@pytest.fixture
def invalid_manifest_path() -> Path:
    """Return path to an invalid manifest fixture."""
    return Path(__file__).parent.parent / "fixtures" / "invalid" / "missing_hooks.yaml"


@pytest.fixture
def warn_manifest_path() -> Path:
    """Return path to a manifest with warnings."""
    return Path(__file__).parent.parent / "fixtures" / "warn" / "unknown_fields.yaml"
