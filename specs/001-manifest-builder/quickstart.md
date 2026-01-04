# Quickstart: HOOK Manifest Builder Development

**Feature**: 001-manifest-builder  
**Created**: 2026-01-04

---

## Prerequisites

- Python 3.10+
- Git
- VS Code with Python extension (recommended)

---

## Initial Setup

### 1. Clone and Enter Repository

```bash
git clone https://github.com/mattiasthalen/hook.git
cd hook
git checkout 001-manifest-builder
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies (Development Mode)

```bash
pip install -e ".[dev]"
```

Or if starting fresh (before pyproject.toml exists):

```bash
pip install pydantic typer ruamel.yaml pytest pytest-cov hypothesis mypy ruff
```

---

## Project Structure

After Milestone 1, the structure should be:

```text
hook/
├── pyproject.toml
├── src/
│   └── hook/
│       ├── __init__.py
│       ├── py.typed
│       ├── models/
│       │   ├── __init__.py
│       │   ├── manifest.py
│       │   ├── frame.py
│       │   ├── concept.py
│       │   ├── settings.py
│       │   └── diagnostic.py
│       └── core/
│           ├── __init__.py
│           ├── validation.py
│           ├── rules.py
│           └── normalization.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   └── test_models.py
│   └── fixtures/
│       └── valid/
│           └── minimal.yaml
└── examples/
    └── minimal.yaml
```

---

## pyproject.toml Template

Create this as task M1-01:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "hook"
version = "0.1.0"
description = "HOOK methodology manifest builder and validator"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "Mattias Thalén" }
]
keywords = ["hook", "data-warehouse", "manifest", "validation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "pydantic>=2.0.0",
    "typer>=0.9.0",
    "ruamel.yaml>=0.18.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "hypothesis>=6.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
ui = [
    "marimo>=0.1.0",
]

[project.scripts]
hook = "hook.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/hook"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --cov=hook --cov-report=term-missing"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

---

## First Test Cycle

### 1. Create Minimal Model

Create `src/hook/models/manifest.py`:

```python
"""Root manifest model."""
from datetime import datetime
from pydantic import BaseModel, Field


class Metadata(BaseModel, frozen=True):
    """Manifest metadata."""
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class Settings(BaseModel, frozen=True):
    """Manifest settings."""
    hook_prefix: str = "_hk__"
    weak_hook_prefix: str = "_wk__"
    delimiter: str = "|"
```

### 2. Write First Test

Create `tests/unit/test_models.py`:

```python
"""Unit tests for manifest models."""
from datetime import datetime, timezone
from hook.models.manifest import Metadata, Settings


def test_metadata_required_fields():
    """Metadata requires name and timestamps."""
    now = datetime.now(timezone.utc)
    meta = Metadata(name="Test", created_at=now, updated_at=now)
    assert meta.name == "Test"
    assert meta.created_at == now


def test_settings_defaults():
    """Settings have sensible defaults."""
    settings = Settings()
    assert settings.hook_prefix == "_hk__"
    assert settings.weak_hook_prefix == "_wk__"
    assert settings.delimiter == "|"


def test_settings_immutable():
    """Settings are frozen (immutable)."""
    settings = Settings()
    try:
        settings.hook_prefix = "changed"
        assert False, "Should have raised"
    except Exception:
        pass  # Expected
```

### 3. Run Tests

```bash
pytest tests/unit/test_models.py -v
```

Expected output:
```
tests/unit/test_models.py::test_metadata_required_fields PASSED
tests/unit/test_models.py::test_settings_defaults PASSED
tests/unit/test_models.py::test_settings_immutable PASSED
```

---

## Type Checking

```bash
mypy src/hook --strict
```

---

## Linting

```bash
ruff check src tests
ruff format src tests
```

---

## Running the CLI (after M4)

```bash
# Validate a manifest
hook validate examples/minimal.yaml

# Start interactive wizard
hook init

# List bundled examples
hook examples list

# Show an example
hook examples show minimal
```

---

## Key References

| Document | Purpose |
|----------|---------|
| [spec.md](spec.md) | Feature specification (requirements, acceptance criteria) |
| [plan.md](plan.md) | Implementation plan (milestones, tasks) |
| [data-model.md](data-model.md) | Data model details (fields, types, validation) |
| [contracts/manifest-schema.json](contracts/manifest-schema.json) | JSON Schema for manifest validation |
| [constitution.md](../../.specify/memory/constitution.md) | Project constitution (principles, rules) |

---

## Milestone Checklist

Use this to track progress:

- [ ] **M1**: Models + Schema Validation
  - [ ] pyproject.toml created
  - [ ] All models implemented
  - [ ] Schema validation works
  - [ ] First test passes

- [ ] **M2**: Constitutional Validation
  - [ ] All ERROR rules implemented
  - [ ] All WARN rules implemented
  - [ ] expr_sql validation works
  - [ ] Invalid fixtures reject correctly

- [ ] **M3**: YAML I/O
  - [ ] YAML read works
  - [ ] YAML write is deterministic
  - [ ] Round-trip test passes

- [ ] **M4**: CLI Commands
  - [ ] `hook validate` works
  - [ ] `hook init` wizard works
  - [ ] `hook examples` works
  - [ ] Exit codes correct

- [ ] **M5**: Examples + Golden Tests
  - [ ] 3 examples created
  - [ ] All examples pass validation
  - [ ] Invalid fixtures produce correct diagnostics

- [ ] **M6**: marimo UI (optional)
  - [ ] UI renders
  - [ ] Validation reactive
  - [ ] Save works

- [ ] **M7**: Polish + Release
  - [ ] README complete
  - [ ] CI passes
  - [ ] Package installable
