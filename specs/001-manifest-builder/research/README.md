# Implementation Research

This folder contains research documents and working examples for implementing the Manifest Builder (dot CLI).

## Research Documents

| Topic | Document | Example Code | Status |
|-------|----------|--------------|--------|
| **Package Management** | [uv-package-manager-research.md](uv-package-manager-research.md) | — | ✅ Complete |
| **CLI Framework** | [typer-cli-research.md](typer-cli-research.md) | [typer-cli-skeleton.py](typer-cli-skeleton.py) | ✅ Complete |
| **Interactive Wizard** | [interactive-wizard-research.md](interactive-wizard-research.md) | [interactive-wizard-example.py](interactive-wizard-example.py) | ✅ Complete |
| **Pydantic v2 Models** | [pydantic-v2-frozen-models-research.md](pydantic-v2-frozen-models-research.md) | — | ✅ Complete |
| **YAML I/O** | [ruamel-yaml-research.md](ruamel-yaml-research.md) | — | ✅ Complete |
| **Property Testing** | [hypothesis-testing-research.md](hypothesis-testing-research.md) | — | ✅ Complete |
| **Schema Validation** | [json-schema-validation-research.md](json-schema-validation-research.md) | [json-schema-validation-test.py](json-schema-validation-test.py), [json-schema-integration-test.py](json-schema-integration-test.py) | ✅ Complete |
| **Expression Validation** | [sqlglot-expression-validation-research.md](sqlglot-expression-validation-research.md) | — | ✅ Complete |

## Quick Reference by Milestone

### M1: Foundation (Models + Schema Validation)
- [uv-package-manager-research.md](uv-package-manager-research.md) — Project setup with `uv init --package`
- [pydantic-v2-frozen-models-research.md](pydantic-v2-frozen-models-research.md) — Immutable models, validators, enums
- [json-schema-validation-research.md](json-schema-validation-research.md) — Schema validation patterns
- [hypothesis-testing-research.md](hypothesis-testing-research.md) — Property-based testing for models

### M2: Constitutional Validation
- [pydantic-v2-frozen-models-research.md](pydantic-v2-frozen-models-research.md) — Model validators for cross-field validation
- [hypothesis-testing-research.md](hypothesis-testing-research.md) — Testing validation rules

### M3: YAML I/O
- [ruamel-yaml-research.md](ruamel-yaml-research.md) — Reading/writing YAML with ordered keys
- [hypothesis-testing-research.md](hypothesis-testing-research.md) — Round-trip testing

### M4: CLI Commands
- [typer-cli-research.md](typer-cli-research.md) — CLI structure, commands, subcommands
- [interactive-wizard-research.md](interactive-wizard-research.md) — questionary-based wizard

### M6: Release
- [uv-package-manager-research.md](uv-package-manager-research.md) — GitHub Actions CI, PyPI publishing

## Running Example Scripts

```bash
# Ensure dependencies are installed
pip install pydantic ruamel.yaml jsonschema hypothesis questionary typer rich

# Test CLI skeleton
python typer-cli-skeleton.py --help
python typer-cli-skeleton.py validate examples/test.yaml
python typer-cli-skeleton.py examples list

# Test JSON Schema validation
python json-schema-validation-test.py
python json-schema-integration-test.py

# Interactive wizard (requires TTY)
python interactive-wizard-example.py
```

## Key Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `pydantic` | Immutable data models | v2.x |
| `typer` | CLI framework | latest |
| `questionary` | Interactive prompts | latest |
| `ruamel.yaml` | YAML parsing with ordering | ≥0.18.0 |
| `jsonschema` | JSON Schema validation | latest |
| `hypothesis` | Property-based testing | latest |
| `rich` | Terminal formatting | latest |
| `ruff` | Linting/formatting | latest |
| `mypy` | Type checking | latest |
