# Research: Using `uv` for Python Package Management

**Date**: January 6, 2026  
**Project**: dot-organize (package: `dot`)  
**Purpose**: Evaluate and document `uv` for project setup and dependency management

---

## 1. Executive Summary

`uv` is an extremely fast Python package and project manager written in Rust by Astral (creators of Ruff). It's designed to replace `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, and `virtualenv` with a single tool that's 10-100x faster than pip.

### Key Advantages Over pip/venv/poetry

| Feature | pip/venv | Poetry | uv |
|---------|----------|--------|-----|
| Speed | Baseline | ~1-2x pip | 10-100x faster |
| Lockfile | ❌ | `poetry.lock` | `uv.lock` (cross-platform) |
| Python management | ❌ (needs pyenv) | ❌ | ✅ Built-in |
| Unified tool | ❌ (multiple tools) | Partial | ✅ Single binary |
| Standard pyproject.toml | ✅ | Custom sections | ✅ PEP-compliant |
| Editable installs | ✅ | ✅ | ✅ |
| Dependency groups | ❌ | ✅ | ✅ (PEP 735) |

### Why uv for dot-organize?

1. **Speed**: Faster CI/CD and local development
2. **Simplicity**: Single tool for everything
3. **Standards-compliant**: Uses standard `pyproject.toml` (PEP 621, PEP 735)
4. **Cross-platform lockfile**: Reproducible builds across Linux/macOS/Windows
5. **Built-in Python management**: No need for pyenv

---

## 2. Project Setup with uv

### Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip (not recommended for primary install)
pip install uv

# Or via Homebrew
brew install uv
```

### Initialize a New Packaged CLI Project

For `dot-organize`, we want a **packaged application** with CLI entry points:

```bash
# Create project directory and initialize as packaged application
uv init --package dot-organize

# Or initialize in existing directory
cd dot-organize
uv init --package
```

This creates the following structure:

```
dot-organize/
├── .python-version      # Python version pin
├── .gitignore
├── README.md
├── pyproject.toml
└── src/
    └── dot_organize/
        └── __init__.py
```

### Alternative: Initialize with Specific Options

```bash
# Initialize with Python 3.10 minimum and custom author
uv init --package dot-organize \
    --python ">=3.10" \
    --author-from git \
    --description "HOOK manifest validation CLI tool"
```

---

## 3. Virtual Environment Management

### How uv Handles Virtual Environments

uv **automatically creates and manages** virtual environments. You rarely need to interact with them directly.

```bash
# Virtual environment is created automatically in .venv/
# on first uv run, uv sync, or uv lock

# To manually create (rarely needed):
uv venv

# To create with specific Python version:
uv venv --python 3.10

# To create with a name:
uv venv my-env
```

### Virtual Environment Location

| Type | Location |
|------|----------|
| Project venv | `.venv/` in project root |
| Named venv | Specified path |
| Tool venvs | `~/.local/share/uv/tools/` |

### Activating the Virtual Environment

Usually **not required** when using `uv run`. But if needed:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Deactivate
deactivate
```

### Specifying Python Version Requirements

Create or edit `.python-version`:

```bash
# Pin to Python 3.10+
uv python pin 3.10

# Or specify in pyproject.toml
[project]
requires-python = ">=3.10"
```

### Installing Specific Python Versions

```bash
# Install Python 3.10
uv python install 3.10

# Install multiple versions
uv python install 3.10 3.11 3.12

# List available versions
uv python list
```

---

## 4. Dependency Management

### Adding Runtime Dependencies

```bash
# Add single dependency
uv add pydantic

# Add with version constraint
uv add "pydantic>=2.0"

# Add multiple dependencies at once
uv add typer ruamel.yaml

# Add with extras
uv add "typer[all]"
```

### Adding Development Dependencies

uv uses **dependency groups** (PEP 735) for dev dependencies:

```bash
# Add to default 'dev' group
uv add --dev pytest hypothesis

# Add to custom group (e.g., 'lint')
uv add --group lint ruff mypy

# Add to custom group (e.g., 'test')
uv add --group test pytest hypothesis pytest-cov

# Add to custom group (e.g., 'docs')
uv add --group docs mkdocs mkdocs-material
```

### Removing Dependencies

```bash
# Remove runtime dependency
uv remove pydantic

# Remove dev dependency
uv remove --dev pytest

# Remove from specific group
uv remove --group lint ruff
```

### Lock Dependencies

```bash
# Generate/update uv.lock
uv lock

# Update specific package
uv lock --upgrade-package pydantic

# Update all packages to latest compatible versions
uv lock --upgrade
```

### Lock File Format

`uv.lock` is a **human-readable TOML file** that:
- Contains exact resolved versions
- Is cross-platform (works on Linux, macOS, Windows)
- Should be committed to version control
- Is managed by uv (don't edit manually)

Example snippet from `uv.lock`:

```toml
version = 1
requires-python = ">=3.10"

[[package]]
name = "pydantic"
version = "2.5.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "annotated-types" },
    { name = "pydantic-core" },
    { name = "typing-extensions" },
]
```

### Sync Dependencies

```bash
# Install all dependencies from lock file
uv sync

# Install with specific groups
uv sync --group test --group lint

# Install all groups
uv sync --all-groups

# Install without dev dependencies
uv sync --no-dev

# Verify lock file is up to date (for CI)
uv sync --locked
```

---

## 5. pyproject.toml Configuration

uv uses **standard pyproject.toml** following PEP 621 and PEP 735. Here's a complete example for `dot-organize`:

### Sample pyproject.toml for dot-organize

```toml
[project]
name = "dot"
version = "0.1.0"
description = "HOOK manifest validation CLI tool for dot-organize"
readme = "README.md"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" }
]
keywords = ["hook", "manifest", "yaml", "cli", "validation"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
    "Typing :: Typed",
]
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "typer>=0.9.0",
    "ruamel.yaml>=0.18.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/dot-organize"
Repository = "https://github.com/yourusername/dot-organize"
Documentation = "https://github.com/yourusername/dot-organize#readme"

# CLI Entry Points
[project.scripts]
dot = "dot.cli:app"

# Optional dependencies (extras)
[project.optional-dependencies]
rich = ["rich>=13.0.0"]

# Development dependency groups (PEP 735)
[dependency-groups]
dev = [
    { include-group = "test" },
    { include-group = "lint" },
    { include-group = "type" },
]
test = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "hypothesis>=6.0.0",
]
lint = [
    "ruff>=0.4.0",
]
type = [
    "mypy>=1.0.0",
]

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# uv-specific settings
[tool.uv]
# Default dependency groups to include
default-groups = ["dev"]

# Hatchling configuration
[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
]

[tool.hatch.build.targets.wheel]
packages = ["src/dot"]

# Tool configurations
[tool.ruff]
target-version = "py310"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --cov=dot --cov-report=term-missing"

[tool.coverage.run]
source = ["src/dot"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Including Package Data

To include non-Python files (like example YAML files):

```toml
# Using hatchling
[tool.hatch.build.targets.wheel]
packages = ["src/dot"]

[tool.hatch.build.targets.wheel.force-include]
"examples/" = "dot/examples/"
"schemas/" = "dot/schemas/"

# Or using MANIFEST.in for source distributions
# Create MANIFEST.in file:
# include src/dot/schemas/*.json
# recursive-include src/dot/examples *.yaml
```

### CLI Entry Points

```toml
[project.scripts]
dot = "dot.cli:app"          # Main CLI command
dot-validate = "dot.cli:validate"  # Subcommand alias
```

This allows users to run:
```bash
dot validate manifest.yaml
# or
dot-validate manifest.yaml
```

---

## 6. Common Commands Reference

### Project Setup

| Command | Description |
|---------|-------------|
| `uv init` | Initialize project in current directory |
| `uv init --package` | Initialize as installable package |
| `uv init --package myproject` | Create new packaged project |
| `uv python pin 3.10` | Pin Python version |
| `uv python install 3.10` | Install specific Python version |

### Dependency Management

| Command | Description |
|---------|-------------|
| `uv add <pkg>` | Add runtime dependency |
| `uv add --dev <pkg>` | Add to dev group |
| `uv add --group test <pkg>` | Add to custom group |
| `uv remove <pkg>` | Remove dependency |
| `uv lock` | Update lock file |
| `uv lock --upgrade` | Upgrade all packages |
| `uv sync` | Install from lock file |
| `uv sync --locked` | Sync and verify lock (CI) |

### Running Code

| Command | Description |
|---------|-------------|
| `uv run python script.py` | Run Python script |
| `uv run pytest` | Run pytest |
| `uv run dot validate` | Run CLI command |
| `uv run -- cmd --flag` | Run with flags (use `--` separator) |

### Building & Publishing

| Command | Description |
|---------|-------------|
| `uv build` | Build wheel and sdist |
| `uv publish` | Publish to PyPI |
| `uv version` | Show package version |
| `uv version --short` | Show version only |

### Environment & Tools

| Command | Description |
|---------|-------------|
| `uv venv` | Create virtual environment |
| `uv pip list` | List installed packages |
| `uv pip show <pkg>` | Show package info |
| `uvx <tool>` | Run tool in isolated env |
| `uv tool install <tool>` | Install CLI tool globally |

---

## 7. Daily Development Workflow

### Initial Setup (One Time)

```bash
# Clone project
git clone https://github.com/user/dot-organize
cd dot-organize

# Install dependencies (creates .venv automatically)
uv sync

# Verify installation
uv run dot --version
```

### Daily Workflow

```bash
# Run the CLI during development
uv run dot validate path/to/manifest.yaml

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/test_manifest.py -k "test_schema"

# Run with hypothesis examples
uv run pytest tests/ --hypothesis-show-statistics

# Run type checker
uv run mypy src/

# Run linter
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Add a new dependency
uv add some-package

# Update dependencies
uv lock --upgrade
uv sync
```

### Using Editable Mode

By default, uv installs the project in editable mode. Changes to source files are immediately reflected without reinstalling:

```bash
# The project is already editable after `uv sync`
# Edit src/dot/cli.py, then run:
uv run dot --help  # Changes are reflected immediately
```

---

## 8. GitHub Actions Integration

### Basic CI Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v5

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.9.21"
          enable-cache: true
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --locked --all-groups

      - name: Run linter
        run: uv run ruff check src/ tests/

      - name: Run type checker
        run: uv run mypy src/

      - name: Run tests
        run: uv run pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Check formatting
        run: uv run ruff format --check src/ tests/

      - name: Check imports
        run: uv run ruff check --select I src/ tests/
```

### Release Workflow with Trusted Publishing

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v5

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        run: uv publish
```

### Caching Strategy

The `astral-sh/setup-uv` action has built-in caching:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
    # Cache key is automatically based on uv.lock
```

For manual caching:

```yaml
- name: Restore uv cache
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
    restore-keys: |
      uv-${{ runner.os }}
```

---

## 9. Best Practices & Gotchas

### Best Practices

1. **Always commit `uv.lock`**: Ensures reproducible builds
2. **Use `--locked` in CI**: Fails if lock file is outdated
3. **Use dependency groups**: Separate test, lint, docs dependencies
4. **Pin uv version in CI**: Avoid surprise breaking changes
5. **Use `uv run`**: Don't activate venv manually
6. **Use `uv sync` not `uv pip install`**: Maintains project state

### Gotchas

1. **No `pip install -e .`**: Use `uv sync` instead (editable by default)

2. **Lock file must be regenerated after manual pyproject.toml edits**:
   ```bash
   # After editing pyproject.toml manually
   uv lock
   uv sync
   ```

3. **Different from Poetry**: uv uses standard PEP fields, not `[tool.poetry]`

4. **Existing venv**: If you have an old venv, remove it:
   ```bash
   rm -rf .venv
   uv sync
   ```

5. **Scripts need `uv run`**: Commands like `pytest` won't work without `uv run` unless venv is activated

6. **Build backend required for packages**: Use `hatchling`, `flit-core`, `setuptools`, or `uv_build`

### Migration from requirements.txt

```bash
# Import existing requirements
uv add -r requirements.txt
uv add -r requirements-dev.txt --dev

# Verify and clean up
uv lock
uv sync
```

### Migration from Poetry

1. Export dependencies:
   ```bash
   poetry export -f requirements.txt > requirements.txt
   poetry export --dev -f requirements.txt > requirements-dev.txt
   ```

2. Create new uv project and import:
   ```bash
   uv init --package
   uv add -r requirements.txt
   uv add -r requirements-dev.txt --dev
   ```

3. Update pyproject.toml with Poetry-specific config (entry points, etc.)

---

## 10. Project Structure for dot-organize

Recommended structure using uv:

```
dot-organize/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── .venv/                    # Created by uv (gitignored)
├── src/
│   └── dot/
│       ├── __init__.py
│       ├── py.typed          # PEP 561 marker
│       ├── cli.py            # Typer CLI
│       ├── models/
│       │   ├── __init__.py
│       │   └── manifest.py   # Pydantic models
│       ├── validators/
│       │   ├── __init__.py
│       │   └── hook.py
│       └── schemas/
│           └── manifest-schema.json
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_manifest.py
│   └── strategies.py         # Hypothesis strategies
├── examples/
│   └── sample-manifest.yaml
├── .gitignore
├── .python-version           # e.g., "3.10"
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock                   # Commit this!
```

### .gitignore additions for uv

```gitignore
# Virtual environment
.venv/

# uv cache (optional, usually outside project)
.uv/

# Build artifacts
dist/
*.egg-info/

# Don't ignore uv.lock - it should be committed!
# uv.lock
```

---

## 11. Quick Start Commands for dot-organize

```bash
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create project (or use existing)
cd dot-organize
uv init --package

# 3. Set Python version
uv python pin 3.10

# 4. Add dependencies
uv add pydantic typer "ruamel.yaml"
uv add --group test pytest hypothesis pytest-cov
uv add --group lint ruff
uv add --group type mypy

# 5. Install everything
uv sync

# 6. Verify
uv run dot --help
uv run pytest

# 7. Start developing!
```

---

## References

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [PEP 621 - Project metadata](https://peps.python.org/pep-0621/)
- [PEP 735 - Dependency Groups](https://peps.python.org/pep-0735/)
- [GitHub Actions Integration](https://docs.astral.sh/uv/guides/integration/github/)
- [astral-sh/setup-uv Action](https://github.com/astral-sh/setup-uv)
