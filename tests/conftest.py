"""Shared pytest fixtures for dot-organize tests."""

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to valid test fixtures."""
    return fixtures_dir / "valid"


@pytest.fixture
def invalid_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to invalid test fixtures."""
    return fixtures_dir / "invalid"


@pytest.fixture
def minimal_manifest_data() -> dict[str, Any]:
    """Return minimal valid manifest data for testing."""
    return {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test Manifest",
            "description": "A test manifest",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        "settings": {
            "hook_prefix": "_hk__",
            "weak_hook_prefix": "_wk__",
            "delimiter": "|",
        },
        "frames": [
            {
                "name": "frame.customer",
                "source": {"relation": "psa.customer"},
                "hooks": [
                    {
                        "name": "_hk__customer",
                        "role": "primary",
                        "concept": "customer",
                        "source": "CRM",
                        "expr": "customer_id",
                    }
                ],
            }
        ],
        "concepts": [],
    }
