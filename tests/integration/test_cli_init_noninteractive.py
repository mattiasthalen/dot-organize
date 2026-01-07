"""
Integration tests for dot init non-interactive mode (T084).

Tests the non-interactive manifest creation:
- --from-config with valid seed → complete manifest
- --from-config with invalid seed → exit 1 with errors
- --concept and --source flags → minimal manifest with auto-derived key set
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import yaml
from typer.testing import CliRunner

from dot.cli.main import app

if TYPE_CHECKING:
    pass

runner = CliRunner()


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Change to a temporary directory for file operations."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def valid_seed(temp_cwd: Path) -> Path:
    """Create a valid seed config file."""
    seed_path = temp_cwd / "seed.yaml"
    seed_content = {
        "frames": [
            {
                "name": "frame.customers",
                "source": {
                    "relation": "raw.customers",
                },
                "hooks": [
                    {
                        "concept": "customer",
                        "source": "CRM",
                        "expr": "customer_id",
                    },
                ],
            },
        ],
    }
    seed_path.write_text(yaml.dump(seed_content))
    return seed_path


@pytest.fixture
def invalid_seed(temp_cwd: Path) -> Path:
    """Create an invalid seed config file."""
    seed_path = temp_cwd / "invalid_seed.yaml"
    seed_content = {
        "frames": [],  # Empty frames = invalid
    }
    seed_path.write_text(yaml.dump(seed_content))
    return seed_path


@pytest.fixture
def seed_missing_source(temp_cwd: Path) -> Path:
    """Create a seed with missing source."""
    seed_path = temp_cwd / "missing_source.yaml"
    seed_content = {
        "frames": [
            {
                "name": "frame.customers",
                # Missing source
                "hooks": [
                    {
                        "concept": "customer",
                        "source": "CRM",
                        "expr": "customer_id",
                    },
                ],
            },
        ],
    }
    seed_path.write_text(yaml.dump(seed_content))
    return seed_path


# =============================================================================
# Test: --from-config with Valid Seed
# =============================================================================


class TestFromConfigValid:
    """Test --from-config with valid seed config."""

    def test_from_config_creates_manifest(
        self,
        temp_cwd: Path,
        valid_seed: Path,
    ) -> None:
        """Valid seed config creates complete manifest."""
        result = runner.invoke(
            app,
            ["init", "--from-config", str(valid_seed)],
        )
        
        assert result.exit_code == 0, f"Failed: {result.output}"
        
        # Check manifest was created
        manifest_path = temp_cwd / ".dot-organize.yaml"
        assert manifest_path.exists(), "Manifest not created"
        
        # Validate content
        content = yaml.safe_load(manifest_path.read_text())
        assert "manifest_version" in content
        assert "frames" in content
        assert len(content["frames"]) == 1

    def test_from_config_auto_generates_hook_names(
        self,
        temp_cwd: Path,
        valid_seed: Path,
    ) -> None:
        """Auto-generates hook names from concept@source."""
        result = runner.invoke(
            app,
            ["init", "--from-config", str(valid_seed)],
        )
        
        assert result.exit_code == 0
        
        manifest_path = temp_cwd / ".dot-organize.yaml"
        content = yaml.safe_load(manifest_path.read_text())
        
        hook = content["frames"][0]["hooks"][0]
        # Hook name should be auto-generated: _hk__customer__crm
        assert hook["name"].startswith("_hk__")
        assert "customer" in hook["name"].lower()

    def test_from_config_custom_output(
        self,
        temp_cwd: Path,
        valid_seed: Path,
    ) -> None:
        """--output flag writes to custom path."""
        custom_path = temp_cwd / "custom" / "manifest.yaml"
        
        result = runner.invoke(
            app,
            ["init", "--from-config", str(valid_seed), "--output", str(custom_path)],
        )
        
        assert result.exit_code == 0
        assert custom_path.exists()

    def test_from_config_json_format(
        self,
        temp_cwd: Path,
        valid_seed: Path,
    ) -> None:
        """--format json creates JSON output."""
        result = runner.invoke(
            app,
            ["init", "--from-config", str(valid_seed), "--format", "json"],
        )
        
        assert result.exit_code == 0
        
        manifest_path = temp_cwd / ".dot-organize.json"
        assert manifest_path.exists()
        
        # Verify valid JSON
        content = json.loads(manifest_path.read_text())
        assert "frames" in content


# =============================================================================
# Test: --from-config with Invalid Seed
# =============================================================================


class TestFromConfigInvalid:
    """Test --from-config with invalid seed config."""

    def test_from_config_empty_frames_error(
        self,
        temp_cwd: Path,
        invalid_seed: Path,
    ) -> None:
        """Empty frames produces error."""
        result = runner.invoke(
            app,
            ["init", "--from-config", str(invalid_seed)],
        )
        
        assert result.exit_code == 1
        assert "error" in result.output.lower()

    def test_from_config_missing_source_error(
        self,
        temp_cwd: Path,
        seed_missing_source: Path,
    ) -> None:
        """Missing source produces error."""
        result = runner.invoke(
            app,
            ["init", "--from-config", str(seed_missing_source)],
        )
        
        assert result.exit_code == 1
        assert "error" in result.output.lower() or "source" in result.output.lower()

    def test_from_config_nonexistent_file_error(self, temp_cwd: Path) -> None:
        """Non-existent seed file produces error."""
        result = runner.invoke(
            app,
            ["init", "--from-config", "nonexistent.yaml"],
        )
        
        assert result.exit_code != 0
        # Should mention file not found
        assert "not found" in result.output.lower() or "error" in result.output.lower()

    def test_from_config_invalid_yaml_error(self, temp_cwd: Path) -> None:
        """Invalid YAML syntax produces error."""
        bad_yaml = temp_cwd / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: :\n  - broken")
        
        result = runner.invoke(
            app,
            ["init", "--from-config", str(bad_yaml)],
        )
        
        assert result.exit_code != 0


# =============================================================================
# Test: --concept and --source Flags
# =============================================================================


class TestQuickInitFlags:
    """Test --concept and --source flags for minimal manifest."""

    def test_concept_and_source_creates_minimal_manifest(
        self,
        temp_cwd: Path,
    ) -> None:
        """--concept and --source create minimal manifest."""
        result = runner.invoke(
            app,
            ["init", "--concept", "customer", "--source", "CRM"],
        )
        
        assert result.exit_code == 0, f"Failed: {result.output}"
        
        manifest_path = temp_cwd / ".dot-organize.yaml"
        assert manifest_path.exists()
        
        content = yaml.safe_load(manifest_path.read_text())
        assert len(content["frames"]) == 1
        
        frame = content["frames"][0]
        assert "customer" in frame["name"].lower()

    def test_concept_and_source_auto_derives_frame_name(
        self,
        temp_cwd: Path,
    ) -> None:
        """Auto-derives frame name from concept."""
        result = runner.invoke(
            app,
            ["init", "--concept", "order", "--source", "ERP"],
        )
        
        assert result.exit_code == 0
        
        manifest_path = temp_cwd / ".dot-organize.yaml"
        content = yaml.safe_load(manifest_path.read_text())
        
        # Frame name should include concept
        frame_name = content["frames"][0]["name"]
        assert "order" in frame_name.lower()

    def test_concept_and_source_auto_generates_hook(
        self,
        temp_cwd: Path,
    ) -> None:
        """Auto-generates hook from concept and source."""
        result = runner.invoke(
            app,
            ["init", "--concept", "product", "--source", "PIM"],
        )
        
        assert result.exit_code == 0
        
        manifest_path = temp_cwd / ".dot-organize.yaml"
        content = yaml.safe_load(manifest_path.read_text())
        
        hook = content["frames"][0]["hooks"][0]
        assert hook["concept"] == "product"
        assert hook["source"] == "PIM"
        assert "_hk__" in hook["name"]

    def test_concept_only_requires_source(self, temp_cwd: Path) -> None:
        """--concept alone without --source should error."""
        result = runner.invoke(
            app,
            ["init", "--concept", "customer"],
        )
        
        # Should error - source is required
        assert result.exit_code != 0 or "source" in result.output.lower()

    def test_source_only_requires_concept(self, temp_cwd: Path) -> None:
        """--source alone without --concept should error."""
        result = runner.invoke(
            app,
            ["init", "--source", "CRM"],
        )
        
        # Should error - concept is required  
        assert result.exit_code != 0 or "concept" in result.output.lower()

    def test_quick_init_with_custom_output(self, temp_cwd: Path) -> None:
        """Quick init respects --output flag."""
        custom_path = temp_cwd / "quick.yaml"
        
        result = runner.invoke(
            app,
            ["init", "--concept", "customer", "--source", "CRM", "--output", str(custom_path)],
        )
        
        assert result.exit_code == 0
        assert custom_path.exists()

    def test_quick_init_json_format(self, temp_cwd: Path) -> None:
        """Quick init respects --format json."""
        result = runner.invoke(
            app,
            ["init", "--concept", "customer", "--source", "CRM", "--format", "json"],
        )
        
        assert result.exit_code == 0
        
        manifest_path = temp_cwd / ".dot-organize.json"
        assert manifest_path.exists()


# =============================================================================
# Test: Validation of Generated Manifest
# =============================================================================


class TestGeneratedManifestValidation:
    """Test that generated manifests pass validation."""

    def test_from_config_manifest_passes_validation(
        self,
        temp_cwd: Path,
        valid_seed: Path,
    ) -> None:
        """Manifest from seed config passes validation."""
        # Generate
        result = runner.invoke(
            app,
            ["init", "--from-config", str(valid_seed)],
        )
        assert result.exit_code == 0
        
        # Validate
        result = runner.invoke(
            app,
            ["validate", ".dot-organize.yaml"],
        )
        assert result.exit_code == 0, f"Validation failed: {result.output}"

    def test_quick_init_manifest_passes_validation(
        self,
        temp_cwd: Path,
    ) -> None:
        """Manifest from quick init passes validation."""
        # Generate
        result = runner.invoke(
            app,
            ["init", "--concept", "customer", "--source", "CRM"],
        )
        assert result.exit_code == 0
        
        # Validate
        result = runner.invoke(
            app,
            ["validate", ".dot-organize.yaml"],
        )
        assert result.exit_code == 0, f"Validation failed: {result.output}"
