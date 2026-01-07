"""
Integration tests for dot examples command (T090).

Tests the examples command workflow:
- dot examples list → lists available examples
- dot examples show minimal → prints example to stdout
- dot examples show typical --output ./my-manifest.yaml → writes to file
- dot examples show nonexistent → exit 1 with error
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from dot.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change to a temporary directory for file operations."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# =============================================================================
# Test: Examples List
# =============================================================================


class TestExamplesList:
    """Test examples list command."""

    def test_list_shows_available_examples(self) -> None:
        """examples list shows available examples."""
        result = runner.invoke(app, ["examples", "list"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "minimal" in result.output.lower()

    def test_list_shows_descriptions(self) -> None:
        """examples list shows descriptions for each example."""
        result = runner.invoke(app, ["examples", "list"])

        assert result.exit_code == 0
        # Should show some descriptive text
        assert len(result.output.strip()) > 20


# =============================================================================
# Test: Examples Show
# =============================================================================


class TestExamplesShow:
    """Test examples show command."""

    def test_show_minimal_prints_to_stdout(self) -> None:
        """examples show minimal prints YAML to stdout."""
        result = runner.invoke(app, ["examples", "show", "minimal"])

        assert result.exit_code == 0, f"Failed: {result.output}"
        # Should contain YAML-like content
        assert "manifest_version" in result.output or "frames" in result.output

    def test_show_minimal_is_valid_yaml(self) -> None:
        """examples show minimal outputs valid YAML."""
        result = runner.invoke(app, ["examples", "show", "minimal"])

        assert result.exit_code == 0

        # Should parse as valid YAML
        data = yaml.safe_load(result.output)
        assert isinstance(data, dict)
        assert "frames" in data

    def test_show_with_output_writes_to_file(self, temp_cwd: Path) -> None:
        """examples show --output writes to file."""
        output_path = temp_cwd / "my-manifest.yaml"

        result = runner.invoke(
            app,
            ["examples", "show", "minimal", "--output", str(output_path)],
        )

        assert result.exit_code == 0
        assert output_path.exists()

        # Verify content
        content = yaml.safe_load(output_path.read_text())
        assert "frames" in content

    def test_show_nonexistent_example_error(self) -> None:
        """examples show nonexistent returns error."""
        result = runner.invoke(app, ["examples", "show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_show_file_based_example(self) -> None:
        """examples show file_based returns valid example."""
        result = runner.invoke(app, ["examples", "show", "file_based"])

        assert result.exit_code == 0
        data = yaml.safe_load(result.output)

        # Should have path source
        assert "frames" in data
        frame = data["frames"][0]
        assert "path" in frame.get("source", {})

    def test_show_typical_example(self) -> None:
        """examples show typical returns valid example."""
        result = runner.invoke(app, ["examples", "show", "typical"])

        assert result.exit_code == 0
        data = yaml.safe_load(result.output)

        # Should have multiple frames (header/line pattern)
        assert len(data.get("frames", [])) >= 2

    def test_show_complex_example(self) -> None:
        """examples show complex returns valid example."""
        result = runner.invoke(app, ["examples", "show", "complex"])

        assert result.exit_code == 0
        data = yaml.safe_load(result.output)

        # Should have concepts, qualifiers, etc.
        assert "frames" in data


# =============================================================================
# Test: Examples Validation
# =============================================================================


class TestExamplesValidation:
    """Test that all examples pass validation."""

    def test_minimal_example_passes_validation(self) -> None:
        """Minimal example passes validation."""
        # Get example content
        result = runner.invoke(app, ["examples", "show", "minimal"])
        assert result.exit_code == 0

        # This test verifies the example is valid YAML that could pass validation
        data = yaml.safe_load(result.output)
        assert "manifest_version" in data or "schema_version" in data
        assert "frames" in data
        assert len(data["frames"]) >= 1

    def test_file_based_example_passes_validation(self) -> None:
        """File-based example passes validation."""
        result = runner.invoke(app, ["examples", "show", "file_based"])
        assert result.exit_code == 0

        data = yaml.safe_load(result.output)
        assert "frames" in data
        assert len(data["frames"]) >= 1

    def test_typical_example_passes_validation(self) -> None:
        """Typical example passes validation."""
        result = runner.invoke(app, ["examples", "show", "typical"])
        assert result.exit_code == 0

        data = yaml.safe_load(result.output)
        assert "frames" in data
        assert len(data["frames"]) >= 1

    def test_complex_example_passes_validation(self) -> None:
        """Complex example passes validation."""
        result = runner.invoke(app, ["examples", "show", "complex"])
        assert result.exit_code == 0

        data = yaml.safe_load(result.output)
        assert "frames" in data
        assert len(data["frames"]) >= 1


# =============================================================================
# Test: Output Formatting
# =============================================================================


class TestExamplesOutput:
    """Test examples output formatting."""

    def test_show_no_trailing_garbage(self) -> None:
        """examples show output is clean YAML without extra text."""
        result = runner.invoke(app, ["examples", "show", "minimal"])

        assert result.exit_code == 0

        # Should be pure YAML - parseable without errors
        data = yaml.safe_load(result.output)
        assert data is not None

    def test_list_uses_table_or_clean_format(self) -> None:
        """examples list uses clean formatted output."""
        result = runner.invoke(app, ["examples", "list"])

        assert result.exit_code == 0
        # Should contain example names
        assert "minimal" in result.output.lower()


# =============================================================================
# Test: Golden Tests - Examples Pass Full Validation (T098)
# =============================================================================


class TestExamplesGoldenValidation:
    """Golden tests: all bundled examples pass full validation pipeline."""

    def test_minimal_example_passes_full_validation(self, temp_cwd: Path) -> None:
        """Minimal example passes full dot validate pipeline."""
        # Write example to temp file
        show_result = runner.invoke(app, ["examples", "show", "minimal"])
        assert show_result.exit_code == 0

        manifest_path = temp_cwd / "minimal.yaml"
        manifest_path.write_text(show_result.output)

        # Run full validation
        validate_result = runner.invoke(app, ["validate", str(manifest_path)])
        assert validate_result.exit_code == 0, f"Validation failed: {validate_result.output}"

    def test_file_based_example_passes_full_validation(self, temp_cwd: Path) -> None:
        """File-based example passes full dot validate pipeline."""
        show_result = runner.invoke(app, ["examples", "show", "file_based"])
        assert show_result.exit_code == 0

        manifest_path = temp_cwd / "file_based.yaml"
        manifest_path.write_text(show_result.output)

        validate_result = runner.invoke(app, ["validate", str(manifest_path)])
        assert validate_result.exit_code == 0, f"Validation failed: {validate_result.output}"

    def test_typical_example_passes_full_validation(self, temp_cwd: Path) -> None:
        """Typical example passes full dot validate pipeline."""
        show_result = runner.invoke(app, ["examples", "show", "typical"])
        assert show_result.exit_code == 0

        manifest_path = temp_cwd / "typical.yaml"
        manifest_path.write_text(show_result.output)

        validate_result = runner.invoke(app, ["validate", str(manifest_path)])
        assert validate_result.exit_code == 0, f"Validation failed: {validate_result.output}"

    def test_complex_example_passes_full_validation(self, temp_cwd: Path) -> None:
        """Complex example passes full dot validate pipeline."""
        show_result = runner.invoke(app, ["examples", "show", "complex"])
        assert show_result.exit_code == 0

        manifest_path = temp_cwd / "complex.yaml"
        manifest_path.write_text(show_result.output)

        validate_result = runner.invoke(app, ["validate", str(manifest_path)])
        assert validate_result.exit_code == 0, f"Validation failed: {validate_result.output}"

    def test_all_examples_pass_validation(self, temp_cwd: Path) -> None:
        """Parametric test: ALL bundled examples pass validation."""
        examples = ["minimal", "file_based", "typical", "complex"]

        for example_name in examples:
            show_result = runner.invoke(app, ["examples", "show", example_name])
            assert show_result.exit_code == 0, f"Failed to show {example_name}"

            manifest_path = temp_cwd / f"{example_name}.yaml"
            manifest_path.write_text(show_result.output)

            validate_result = runner.invoke(app, ["validate", str(manifest_path)])
            assert (
                validate_result.exit_code == 0
            ), f"Example '{example_name}' failed validation:\n{validate_result.output}"
