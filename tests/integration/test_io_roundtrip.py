"""T060: Round-trip tests for I/O operations.

TDD - Write tests FIRST, must FAIL before implementation
"""

from pathlib import Path


class TestYamlRoundTrip:
    """Tests for YAML load → save → load round-trip."""

    def test_yaml_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """Load → save → load produces equivalent manifest."""
        from dot.io.yaml import dump_manifest_yaml, load_manifest_yaml

        # Load original
        original_path = (
            Path(__file__).parent.parent / "fixtures" / "valid" / "minimal.yaml"
        )
        original = load_manifest_yaml(original_path)

        # Save to new file
        output_path = tmp_path / "roundtrip.yaml"
        dump_manifest_yaml(original, output_path)

        # Load the saved file
        reloaded = load_manifest_yaml(output_path)

        # Compare essential fields
        assert reloaded.manifest_version == original.manifest_version
        assert reloaded.schema_version == original.schema_version
        assert len(reloaded.frames) == len(original.frames)
        assert len(reloaded.concepts) == len(original.concepts)

    def test_yaml_roundtrip_preserves_key_order(self, tmp_path: Path) -> None:
        """YAML round-trip preserves key order per data-model.md."""
        from dot.io.yaml import dump_manifest_yaml, load_manifest_yaml, parse_yaml

        # Load original
        original_path = (
            Path(__file__).parent.parent / "fixtures" / "valid" / "minimal.yaml"
        )
        original = load_manifest_yaml(original_path)

        # Save to new file
        output_path = tmp_path / "roundtrip.yaml"
        dump_manifest_yaml(original, output_path)

        # Check key order in output
        raw = parse_yaml(output_path)
        keys = list(raw.keys())

        # Expected order per data-model.md
        assert keys[0] == "manifest_version"
        assert keys[1] == "schema_version"

    def test_yaml_roundtrip_with_composite_grain(self, tmp_path: Path) -> None:
        """Round-trip works with composite grain manifest."""
        from dot.io.yaml import dump_manifest_yaml, load_manifest_yaml

        original_path = (
            Path(__file__).parent.parent / "fixtures" / "valid" / "composite_grain.yaml"
        )
        original = load_manifest_yaml(original_path)

        output_path = tmp_path / "roundtrip.yaml"
        dump_manifest_yaml(original, output_path)

        reloaded = load_manifest_yaml(output_path)

        # Verify composite grain preserved
        frame = reloaded.frames[0]
        primary_hooks = [h for h in frame.hooks if h.role.value == "primary"]
        assert len(primary_hooks) == 2


class TestJsonRoundTrip:
    """Tests for JSON load → save → load round-trip."""

    def test_json_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """Load → save → load produces equivalent manifest."""
        from dot.io.json import dump_manifest_json, load_manifest_json
        from dot.models.manifest import Manifest

        # Create original
        original = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        # Save to file
        output_path = tmp_path / "roundtrip.json"
        dump_manifest_json(original, output_path)

        # Load the saved file
        reloaded = load_manifest_json(output_path)

        assert reloaded.manifest_version == original.manifest_version
        assert reloaded.schema_version == original.schema_version


class TestCrossFormatRoundTrip:
    """Tests for YAML ↔ JSON format conversion."""

    def test_yaml_to_json_conversion(self, tmp_path: Path) -> None:
        """Load YAML, save as JSON, load JSON produces equivalent manifest."""
        from dot.io.json import dump_manifest_json, load_manifest_json
        from dot.io.yaml import load_manifest_yaml

        # Load from YAML
        yaml_path = Path(__file__).parent.parent / "fixtures" / "valid" / "minimal.yaml"
        original = load_manifest_yaml(yaml_path)

        # Save as JSON
        json_path = tmp_path / "converted.json"
        dump_manifest_json(original, json_path)

        # Load from JSON
        reloaded = load_manifest_json(json_path)

        assert reloaded.manifest_version == original.manifest_version
        assert len(reloaded.frames) == len(original.frames)

    def test_json_to_yaml_conversion(self, tmp_path: Path) -> None:
        """Load JSON, save as YAML, load YAML produces equivalent manifest."""
        from dot.io.json import dump_manifest_json, load_manifest_json
        from dot.io.yaml import dump_manifest_yaml, load_manifest_yaml
        from dot.models.manifest import Manifest

        # Create original
        original = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            frames=[],
            concepts=[],
        )

        # Save as JSON first
        json_path = tmp_path / "original.json"
        dump_manifest_json(original, json_path)

        # Load from JSON
        from_json = load_manifest_json(json_path)

        # Save as YAML
        yaml_path = tmp_path / "converted.yaml"
        dump_manifest_yaml(from_json, yaml_path)

        # Load from YAML
        reloaded = load_manifest_yaml(yaml_path)

        assert reloaded.manifest_version == original.manifest_version
