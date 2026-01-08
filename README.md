# dot-organize

[![CI](https://github.com/mattiasthalen/dot-organize/workflows/CI/badge.svg)](https://github.com/mattiasthalen/dot-organize/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**dot** (Data Organize Tool) is a CLI for creating and validating manifests using the HOOK methodology. Define how business concepts flow between source systems with type-safe, declarative manifests.

## Features

- **Validate manifests** with actionable error messages and fix suggestions
- **Interactive wizard** to create manifests step-by-step
- **Non-interactive mode** for CI/CD pipelines
- **Built-in examples** to learn manifest structure
- **Type-safe** Pydantic v2 models with frozen immutability
- **Fast validation** with <1s for typical manifests

## Installation

```bash
pip install dot-organize
```

Or with [uv](https://github.com/astral-sh/uv) (recommended):

```bash
uv pip install dot-organize
```

## Quick Start

### Validate a Manifest

```bash
# Validate manifest.yaml and show errors/warnings
dot validate manifest.yaml

# Output JSON report
dot validate manifest.yaml --format json
```

### Create a Manifest Interactively

```bash
# Start the interactive wizard
dot init

# Save to specific file
dot init --output my-manifest.yaml

# Generate JSON instead of YAML
dot init --format json
```

### Create Manifest Non-Interactively (CI/CD)

```bash
# From seed configuration
dot init --from-config seed.yaml --output manifest.yaml

# From command-line flags
dot init --concept customer --source CRM --output minimal.yaml
```

### View Example Manifests

```bash
# List available examples
dot examples list

# Show an example
dot examples show minimal
dot examples show complex

# Save example to file
dot examples show typical --output ./my-manifest.yaml
```

## Manifest Structure

A manifest defines **frames** (data tables) with **hooks** (business key derivations):

```yaml
manifest_version: "1.0.0"
schema_version: "1.0.0"

frames:
  - name: staging.customer
    source:
      relation: "crm.public.customers"
    hooks:
      - name: _hk__customer
        role: primary
        concept: customer
        source: CRM
        expr: "customer_id"
```

### Frame Naming

Frame names follow `<schema>.<table>` pattern in `lower_snake_case`:
- ✅ `staging.customer`, `psa.order_header`, `frame.product`
- ❌ `customer`, `STAGING.Customer`

### Hook Naming

Hook names follow `_hk__<concept>[__<qualifier>]` pattern:
- ✅ `_hk__customer`, `_hk__employee__manager`
- ❌ `customer_hook`, `_hk_customer`

### Source Types

| Type | Example | Use Case |
|------|---------|----------|
| `relation` | `"db.schema.table"` | SQL databases |
| `path` | `"s3://bucket/path/*.parquet"` | Data lake files |

### Hook Roles

| Role | Purpose |
|------|---------|
| `primary` | Defines the frame's grain |
| `foreign` | References another concept |

## CLI Reference

### `dot validate <manifest>`

Validate a manifest file against the schema.

| Flag | Description |
|------|-------------|
| `--format` | Output format: `text` (default) or `json` |

Exit codes:
- `0`: Valid manifest
- `1`: Invalid manifest
- `2`: File not found

### `dot init`

Create a new manifest interactively or from configuration.

| Flag | Description |
|------|-------------|
| `--output`, `-o` | Output file path |
| `--format`, `-f` | Output format: `yaml` (default) or `json` |
| `--from-config` | Seed config file (non-interactive) |
| `--concept` | Concept name (non-interactive) |
| `--source` | Source system (non-interactive) |

### `dot examples`

View built-in example manifests.

| Subcommand | Description |
|------------|-------------|
| `list` | Show available examples |
| `show <name>` | Display an example |
| `show <name> --output <file>` | Save example to file |

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/mattiasthalen/dot-organize.git
cd dot-organize

# Install with uv
uv sync --all-groups

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
uv run mypy --strict src/
```

### Project Structure

```
src/dot/
├── cli/          # CLI commands (typer)
├── core/         # Core validation engine
├── io/           # YAML/JSON I/O
└── models/       # Pydantic models

tests/
├── unit/         # Unit tests
├── integration/  # CLI integration tests
└── fixtures/     # Test manifests
```

## Development

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development setup instructions, including:

- Devcontainer and manual setup options
- Running quality checks and tests
- Version bumping and release process
- Commit message conventions

## License

MIT
