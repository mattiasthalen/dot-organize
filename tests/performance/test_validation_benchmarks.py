"""Performance benchmarks for manifest validation.

T108: Verify NFR-001/002/003 performance requirements:
- NFR-001: Validation <1s for 1000 lines
- NFR-002: Validation <5s for 10000 lines
- NFR-003: Memory usage <100MB

These tests use pytest-benchmark or time module for measurements.
Mark as slow tests to skip in normal CI runs.
"""

import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from dot.core.validation import validate_manifest
from dot.io.yaml import dump_manifest_yaml, load_manifest_yaml
from dot.models.frame import Frame, Hook, HookRole, Source
from dot.models.manifest import Manifest, Metadata
from dot.models.settings import Settings


def generate_large_manifest(num_frames: int, hooks_per_frame: int = 5) -> Manifest:
    """Generate a large manifest for performance testing.

    Args:
        num_frames: Number of frames to generate.
        hooks_per_frame: Number of hooks per frame.

    Returns:
        Manifest with the specified size.
    """
    now = datetime.now(timezone.utc)
    frames = []

    for i in range(num_frames):
        hooks = []
        for j in range(hooks_per_frame):
            hook = Hook(
                name=f"_hk__concept{i}_{j}",
                role=HookRole.PRIMARY if j == 0 else HookRole.FOREIGN,
                concept=f"concept{i}_{j}",
                source=f"SRC{i % 10}",
                expr=f"field_{j}",
            )
            hooks.append(hook)

        frame = Frame(
            name=f"schema{i // 100}.table{i}",
            source=Source(relation=f"raw.source_{i}"),
            hooks=hooks,
        )
        frames.append(frame)

    return Manifest(
        manifest_version="1.0.0",
        schema_version="1.0.0",
        metadata=Metadata(name="Large Test Manifest", created_at=now, updated_at=now),
        settings=Settings(),
        frames=frames,
        concepts=[],
    )


def estimate_yaml_lines(num_frames: int, hooks_per_frame: int) -> int:
    """Estimate YAML line count for a manifest.

    Each frame is roughly:
    - 1 line for "- name:"
    - 2 lines for source
    - 1 line for "hooks:"
    - 5 lines per hook (name, role, concept, source, expr)

    Plus ~5 lines for header.
    """
    lines_per_frame = 4 + (5 * hooks_per_frame)
    return 5 + (num_frames * lines_per_frame)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    # Use resource module on Unix-like systems
    if sys.platform != "win32":
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
    return 0.0


@pytest.mark.slow
class TestNFR001ValidationUnder1Second:
    """NFR-001: Validation MUST complete in <1 second for manifests up to 1000 lines."""

    def test_1000_lines_under_1_second(self) -> None:
        """Validate a ~1000 line manifest in under 1 second."""
        # Calculate frames needed for ~1000 lines
        # Each frame with 5 hooks ≈ 29 lines → ~35 frames for 1000 lines
        num_frames = 35
        hooks_per_frame = 5
        expected_lines = estimate_yaml_lines(num_frames, hooks_per_frame)

        assert expected_lines >= 1000, f"Expected ~1000 lines, got {expected_lines}"

        manifest = generate_large_manifest(num_frames, hooks_per_frame)

        start = time.perf_counter()
        diagnostics = validate_manifest(manifest, include_warnings=True)
        elapsed = time.perf_counter() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Validation took {elapsed:.2f}s, expected <1s"

        # Should produce valid result (no errors expected)
        errors = [d for d in diagnostics if d.severity.value == "ERROR"]
        assert len(errors) == 0, f"Unexpected errors: {errors}"


@pytest.mark.slow
class TestNFR002ValidationUnder5Seconds:
    """NFR-002: Validation MUST complete in <5 seconds for manifests up to 10,000 lines."""

    def test_10000_lines_under_5_seconds(self) -> None:
        """Validate a ~10000 line manifest in under 5 seconds."""
        # Each frame with 5 hooks ≈ 29 lines → ~345 frames for 10000 lines
        num_frames = 345
        hooks_per_frame = 5
        expected_lines = estimate_yaml_lines(num_frames, hooks_per_frame)

        assert expected_lines >= 10000, f"Expected ~10000 lines, got {expected_lines}"

        manifest = generate_large_manifest(num_frames, hooks_per_frame)

        start = time.perf_counter()
        diagnostics = validate_manifest(manifest, include_warnings=True)
        elapsed = time.perf_counter() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0, f"Validation took {elapsed:.2f}s, expected <5s"

        # Should produce valid result (no errors expected)
        errors = [d for d in diagnostics if d.severity.value == "ERROR"]
        assert len(errors) == 0, f"Unexpected errors: {errors}"


@pytest.mark.slow
class TestNFR003MemoryUnder100MB:
    """NFR-003: Memory usage MUST stay under 100MB for manifests up to 1MB file size."""

    def test_large_manifest_memory_under_100mb(self) -> None:
        """Memory usage stays under 100MB for large manifest."""
        # Generate a large manifest and write to file to measure
        num_frames = 100
        hooks_per_frame = 5

        manifest = generate_large_manifest(num_frames, hooks_per_frame)

        # Write to temp file to simulate real loading
        with NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            temp_path = Path(f.name)

        # Serialize manifest to YAML file
        dump_manifest_yaml(manifest, temp_path)

        try:
            # Get baseline memory
            baseline_mb = get_memory_usage_mb()

            # Load and validate
            loaded_manifest, raw_data = load_manifest_yaml(temp_path, return_raw=True)
            diagnostics = validate_manifest(loaded_manifest, raw_data=raw_data)

            # Get peak memory
            peak_mb = get_memory_usage_mb()
            memory_increase = peak_mb - baseline_mb

            # Memory increase should be reasonable (well under 100MB)
            # Note: This is a rough check since Python GC makes exact measurement hard
            assert memory_increase < 100, (
                f"Memory increased by {memory_increase:.1f}MB, expected <100MB"
            )

        finally:
            # Cleanup
            temp_path.unlink()


# Simple benchmark tests that run quickly for CI
class TestQuickValidationBenchmarks:
    """Quick benchmarks that run in normal CI."""

    def test_small_manifest_under_100ms(self) -> None:
        """Small manifest validates very quickly."""
        num_frames = 5
        manifest = generate_large_manifest(num_frames, hooks_per_frame=3)

        start = time.perf_counter()
        diagnostics = validate_manifest(manifest, include_warnings=True)
        elapsed = time.perf_counter() - start

        # Should be very fast
        assert elapsed < 0.1, f"Validation took {elapsed:.3f}s, expected <0.1s"

    def test_medium_manifest_under_500ms(self) -> None:
        """Medium manifest (100 frames) validates quickly."""
        num_frames = 100
        manifest = generate_large_manifest(num_frames, hooks_per_frame=5)

        start = time.perf_counter()
        diagnostics = validate_manifest(manifest, include_warnings=True)
        elapsed = time.perf_counter() - start

        # Should complete quickly
        assert elapsed < 0.5, f"Validation took {elapsed:.3f}s, expected <0.5s"
