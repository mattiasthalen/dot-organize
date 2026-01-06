# Implementation Plan: HOOK Manifest Builder (dot CLI)

**Branch**: `001-manifest-builder` | **Date**: 2026-01-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-manifest-builder/spec.md`

---

## Summary

Build a Python package + CLI for HOOK manifest authoring and validation. The manifest is the single source of truth for business concepts, hooks, key sets, and frames. This feature delivers:

1. **Manifest schema** with typed data model (Pydantic/dataclasses)
2. **Validation engine** as pure functions (schema + constitutional rules)
3. **CLI** (`dot init`, `dot validate`, `dot examples`)
4. **YAML I/O** with deterministic output
5. **Example manifests** with golden tests

**Not in scope**: SQL generation, AST parsing, graph traversal, IBIS, code generation, marimo UI.

---

## Execution Sequence

Execute tasks in this order (respecting dependencies):

```text
Phase 1: Foundation (M1)
├── M1-01  pyproject.toml
├── M1-12  Pre-commit hooks (ruff, mypy)
├── M1-07  Diagnostic model (needed by validation)
├── M1-06  Settings model
├── M1-05  Concept model  
├── M1-04  Hook model + HookRole enum
├── M1-03  Frame model (imports Hook)
├── M1-02  Manifest model (imports all above)
├── M1-08  Naming validators (regex patterns)
├── M1-09  Schema validation (combines models + validators)
├── M1-10  minimal.yaml fixture
└── M1-11  Unit tests for models

Phase 2: Validation Rules (M2)
├── M2-07  Key set derivation (pure function)
├── M2-08  Concept registry (pure function)
├── M2-09  Hook registry (pure function)
├── M2-10  expr validation (forbidden patterns - Manifest SQL subset)
├── M2-05  MANIFEST rules (semver)
├── M2-01  FRAME rules (FRAME-001 to 006, including source exclusivity)
├── M2-02  HOOK rules (HOOK-001 to 006)
├── M2-03  KEYSET rules (uses M2-07)
├── M2-04  CONCEPT rules (uses M2-08)
├── M2-06  WARN rules (all warnings)
├── M2-11  Invalid fixtures (one per rule)
└── M2-12  Unit tests for rules

Phase 3: I/O (M3)
├── M3-01  YAML reader
├── M3-05  Parse error handling
├── M3-02  YAML writer (ordered keys)
├── M3-03  JSON reader
├── M3-04  JSON writer
└── M3-06  Round-trip tests

Phase 4: CLI (M4)
├── M4-01  typer app skeleton
├── M4-11  Entry point in pyproject.toml
├── M4-02  validate command
├── M4-03  Human-readable output
├── M4-04  JSON output (--json)
├── M4-09  examples list
├── M4-10  examples show
├── M4-05  init wizard
├── M4-06  Wizard validation
├── M4-07  Wizard preview
├── M4-08  Wizard save
└── M4-12  CLI integration tests

Phase 5: Examples (M5)
├── M5-01  minimal.yaml (relation source)
├── M5-02  file_based.yaml (path source)
├── M5-03  typical.yaml
├── M5-04  complex.yaml
├── M5-05  Golden tests
├── M5-06  Negative fixture tests
└── M5-07  Bundle examples

Phase 6: Release (M6)
├── M6-01  Write README
├── M6-02  Complete pyproject.toml
├── M6-03  GitHub Actions CI
├── M6-04  Type check (mypy)
├── M6-05  Test coverage
├── M6-06  Docstrings
└── M6-07  Test PyPI release
```

**Key files for implementation details**:
- [data-model.md](data-model.md) — Model definitions, function patterns, test patterns
- [data-model.md#implementation-cookbook](data-model.md#implementation-cookbook) — Step-by-step code patterns
- [contracts/manifest-schema.json](contracts/manifest-schema.json) — JSON Schema for validation
- [spec.md](spec.md) — Requirements and acceptance criteria

---

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**:
- `pydantic` (v2) — schema validation, immutable models
- `typer` — CLI framework (thin I/O layer)
- `ruamel.yaml` — YAML parsing with ordering
- `pytest` — testing

**Storage**: File-based (YAML manifests)  
**Testing**: pytest with hypothesis for property-based tests  
**Target Platform**: Linux, macOS, Windows (CLI)  
**Project Type**: Single Python package with CLI entry point  
**Performance Goals**: Validate 1000-line manifest in <1 second  
**Constraints**: No external services, no database, pure functions for core logic  
**Scale/Scope**: Manifests with ≤100-150 business concepts (Dunbar guidance)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Organising Discipline | ⬜ | |
| II. Hooks as Identity | ⬜ | |
| III. Business Concepts | ⬜ | |
| IV. Key Sets Required | ⬜ | |
| V. Frames as Wrappers | ⬜ | |
| VI. Join Safety | ⬜ | |
| VII. Implied Relationships | ⬜ | |
| VIII. Manifest as SSOT | ⬜ | |
| X. Simplicity | ⬜ | |

**Prohibited Patterns Check**:
- ⬜ No business logic in hooks
- ⬜ No derived values — `expr` is source expression only (Manifest SQL subset)
- ⬜ No sentinel substitution — null propagation rule
- ⬜ No hooks without key sets — auto-derived key sets

---

## Project Structure

### Documentation (this feature)

```text
specs/001-manifest-builder/
├── spec.md              # Feature specification
├── plan.md              # This file
├── data-model.md        # ✅ Data model with field specs
├── quickstart.md        # ✅ Developer setup guide
├── contracts/           # ✅ API contracts
│   └── manifest-schema.json  # JSON Schema v2020-12
└── checklists/
    └── requirements.md  # Acceptance checklist
```

### Source Code (repository root)

```text
src/
└── dot/
    ├── __init__.py           # Package exports
    ├── py.typed              # PEP 561 marker
    │
    ├── models/               # Immutable data structures
    │   ├── __init__.py
    │   ├── manifest.py       # Root manifest model
    │   ├── frame.py          # Frame + Hook models
    │   ├── concept.py        # Business concept model
    │   ├── settings.py       # Settings model
    │   └── diagnostic.py     # Validation diagnostic model
    │
    ├── core/                 # Pure functions (no I/O)
    │   ├── __init__.py
    │   ├── validation.py     # Schema + constitutional validation
    │   ├── rules.py          # Validation rule definitions
    │   ├── normalization.py  # Naming conventions, key set derivation
    │   └── registry.py       # Auto-derived registries (concepts, key sets)
    │
    ├── io/                   # Thin I/O layer
    │   ├── __init__.py
    │   ├── yaml.py           # YAML read/write
    │   └── json.py           # JSON read/write (optional)
    │
    ├── cli/                  # CLI commands (thin wrapper)
    │   ├── __init__.py
    │   ├── main.py           # typer app entry point
    │   ├── validate.py       # dot validate command
    │   ├── init.py           # dot init command (wizard)
    │   └── examples.py       # dot examples command

tests/
├── conftest.py               # Shared fixtures
├── unit/
│   ├── test_models.py
│   ├── test_validation.py
│   ├── test_normalization.py
│   └── test_registry.py
├── integration/
│   ├── test_cli_validate.py
│   ├── test_cli_init.py
│   └── test_cli_examples.py
└── fixtures/
    ├── valid/
    │   ├── minimal.yaml
    │   ├── typical.yaml
    │   └── complex.yaml
    └── invalid/
        ├── missing_hook.yaml
        └── duplicate_keyset.yaml

examples/
├── minimal.yaml          # Relational source example
├── file_based.yaml       # File/path source example
├── typical.yaml
└── complex.yaml
```

**Structure Decision**: Single Python package (`dot`) with clear separation:
- `models/` — immutable Pydantic models (frozen=True)
- `core/` — pure functions, no I/O, independently testable
- `io/` — YAML/JSON serialization (thin)
- `cli/` — typer commands (thin wrapper over core)

---

## Milestones

### Milestone 1: Foundation (Models + Schema Validation)

**Objective**: Define the manifest data model and basic schema validation.

**Deliverables**:
- [ ] `src/dot/models/` — all Pydantic models
- [ ] `src/dot/core/validation.py` — schema validation (required fields, types)
- [ ] `src/dot/core/normalization.py` — naming conventions
- [ ] `tests/unit/test_models.py` — model unit tests
- [ ] `tests/fixtures/valid/minimal.yaml` — first example fixture

**Done when**:
- Models serialize to/from YAML
- Schema validation catches missing required fields
- Naming conventions enforced (lower_snake_case, UPPER_SNAKE_CASE)

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M1-01 | Create pyproject.toml | Package metadata, dependencies, entry points | — | [quickstart.md](quickstart.md#pyprojecttoml-template) |
| M1-12 | Add pre-commit hooks | ruff check, ruff format, mypy --strict (per NFR-042) | M1-01 | [spec.md NFR-040-042](spec.md#implementation-standards) |
| M1-07 | Implement Diagnostic model | Severity enum, rule_id, message, path, fix | M1-01 | [data-model.md §8](data-model.md#8-diagnostic) |
| M1-06 | Implement Settings model | hook_prefix, weak_hook_prefix, delimiter with defaults | M1-01 | [data-model.md §3](data-model.md#3-settings) |
| M1-05 | Implement Concept model | Optional concept with name, description, examples, is_weak | M1-01 | [data-model.md §6](data-model.md#6-concept-optional) |
| M1-04 | Implement Hook model | Hook with name, role, concept, qualifier, source, tenant, expression | M1-01 | [data-model.md §5](data-model.md#5-hook) |
| M1-03 | Implement Frame model | Frame with name, source, description, hooks list | M1-04 | [data-model.md §4](data-model.md#4-frame) |
| M1-02 | Implement Manifest model | Root model with metadata, settings, frames, concepts | M1-03, M1-05, M1-06 | [data-model.md §1](data-model.md#1-manifest-root) |
| M1-08 | Implement naming validators | lower_snake_case, UPPER_SNAKE_CASE, hook naming pattern | M1-01 | [data-model.md §10](data-model.md#10-naming-convention-patterns) |
| M1-09 | Implement schema validation | Required field checks, type validation | M1-02, M1-07, M1-08 | [manifest-schema.json](contracts/manifest-schema.json) |
| M1-10 | Create minimal.yaml fixture | Single concept, single hook, single frame | M1-02 | [spec.md §5](spec.md#5-manifest-schema-v1) |
| M1-11 | Unit tests for models | Serialization, validation, defaults | M1-02, M1-09 | [data-model.md §Implementation Cookbook](data-model.md#test-patterns) |

---

### Milestone 2: Constitutional Validation

**Objective**: Implement all constitutional rules from the spec.

**Deliverables**:
- [ ] `src/dot/core/rules.py` — all validation rules (ERROR + WARN)
- [ ] `src/dot/core/registry.py` — auto-derive key sets, concepts, hooks
- [ ] `tests/unit/test_validation.py` — rule tests
- [ ] `tests/fixtures/invalid/` — invalid fixture collection

**Done when**:
- All 17 ERROR rules from spec are implemented
- All 6 WARN rules from spec are implemented
- Auto-derived key sets follow `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M2-07 | Implement key set derivation | `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]` | M1-02 | [data-model.md §9](data-model.md#9-auto-derived-registries) |
| M2-08 | Implement concept registry | Unique concepts from all hooks | M1-02 | [data-model.md §9](data-model.md#9-auto-derived-registries) |
| M2-09 | Implement hook registry | All hooks indexed by name | M1-02 | [data-model.md §9](data-model.md#9-auto-derived-registries) |
| M2-05 | Implement MANIFEST rules | MANIFEST-001, MANIFEST-002 (semver) | M1-07, M1-08 | [spec.md §7.1](spec.md#71-error-severity) |
| M2-01 | Implement FRAME rules | FRAME-001 to FRAME-004 | M1-07, M1-08 | [spec.md §7.1](spec.md#71-error-severity) |
| M2-02 | Implement HOOK rules | HOOK-001 to HOOK-006 | M1-07, M1-08 | [spec.md §7.1](spec.md#71-error-severity) |
| M2-03 | Implement KEYSET rules | KEYSET-001 (uniqueness) | M2-07 | [spec.md §7.1](spec.md#71-error-severity) |
| M2-04 | Implement CONCEPT rules | CONCEPT-001, CONCEPT-002 | M1-07, M2-08 | [spec.md §7.1](spec.md#71-error-severity) |
| M2-06 | Implement WARN rules | CONCEPT-W01, HOOK-W01, FRAME-W01 to W03, MANIFEST-W01 | M2-01 to M2-05 | [spec.md §7.2](spec.md#72-warn-severity) |
| M2-11 | Create invalid fixtures | One per rule for negative testing | M2-01 to M2-06 | [data-model.md §Implementation Cookbook](data-model.md#fixture-templates) |
| M2-12 | Unit tests for all rules | Each rule has positive + negative test | M2-11 | [data-model.md §Implementation Cookbook](data-model.md#test-patterns) |

---

### Milestone 3: YAML I/O

**Objective**: Reliable YAML parsing and deterministic output.

**Deliverables**:
- [ ] `src/dot/io/yaml.py` — read/write with ruamel.yaml
- [ ] `src/dot/io/json.py` — JSON alternative (optional format)
- [ ] Deterministic key ordering in output
- [ ] `tests/integration/test_io.py` — round-trip tests

**Done when**:
- YAML parse errors include line/column
- Output YAML has consistent ordering (metadata, settings, frames, concepts, targets)
- Round-trip: load → save → load produces identical models

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M3-01 | Implement YAML reader | Parse with ruamel.yaml, return Manifest or errors | M1-02, M1-07 | [data-model.md §14](data-model.md#14-yaml-key-ordering) |
| M3-05 | Handle parse errors | Line/column in error messages | M3-01 | [data-model.md §8](data-model.md#8-diagnostic) |
| M3-02 | Implement YAML writer | Serialize Manifest to YAML with ordered keys | M1-02 | [data-model.md §14](data-model.md#14-yaml-key-ordering) |
| M3-03 | Implement JSON reader | Parse JSON manifest | M1-02 | [manifest-schema.json](contracts/manifest-schema.json) |
| M3-04 | Implement JSON writer | Serialize to JSON | M1-02 | [manifest-schema.json](contracts/manifest-schema.json) |
| M3-06 | Round-trip tests | Verify idempotent serialization | M3-01, M3-02 | [data-model.md §Implementation Cookbook](data-model.md#test-patterns) |

---

### Milestone 4: CLI Commands

**Objective**: Implement all CLI commands from the spec.

**Deliverables**:
- [ ] `src/dot/cli/main.py` — typer app with subcommands
- [ ] `dot validate <path>` — validate command with --json flag
- [ ] `dot init` — interactive wizard
- [ ] `dot examples list` / `dot examples show <name>` — examples command
- [ ] Entry point in pyproject.toml
- [ ] `tests/integration/test_cli_*.py` — CLI integration tests

**Done when**:
- `dot validate manifest.yaml` exits 0 on valid, 1 on error, 2 on usage error
- `dot validate --json` outputs JSON diagnostics
- `dot init` creates valid manifest via prompts
- `dot examples list` shows available examples
- All CLI commands tested via subprocess

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M4-01 | Create typer app | Main entry point with --version, --help | M1-01 | [spec.md §6.1](spec.md#61-cli-commands) |
| M4-02 | Implement validate command | Path argument, --json flag, exit codes | M4-01, M2-12, M3-01 | [spec.md §6.1](spec.md#61-cli-commands) |
| M4-03 | Implement human-readable output | Diagnostic formatting per spec | M4-02 | [spec.md §6.3](spec.md#63-diagnostic-format-cli) |
| M4-04 | Implement JSON output | --json flag for machine-readable diagnostics | M4-02 | [spec.md §6.3](spec.md#63-diagnostic-format-cli) |
| M4-05 | Implement init wizard | Frame-first workflow with prompts | M4-01, M1-02 | [spec.md §6.2](spec.md#62-wizard-flow-hook-init) |
| M4-06 | Implement wizard validation | Validate each input, prevent invalid states | M4-05, M2-12 | [spec.md §6.2](spec.md#62-wizard-flow-hook-init) |
| M4-07 | Implement wizard preview | Show YAML preview before writing | M4-05, M3-02 | [spec.md §6.2](spec.md#62-wizard-flow-hook-init) |
| M4-08 | Implement wizard save | Write to path, prompt on overwrite | M4-07 | [spec.md §6.2](spec.md#62-wizard-flow-hook-init) |
| M4-09 | Implement examples list | List bundled examples | M4-01 | [spec.md §6.1](spec.md#61-cli-commands) |
| M4-10 | Implement examples show | Display example content, --output flag | M4-09 | [spec.md §6.1](spec.md#61-cli-commands) |
| M4-11 | Add entry point | `dot` command in pyproject.toml | M4-01 | [quickstart.md](quickstart.md#pyprojecttoml-template) |
| M4-12 | CLI integration tests | Test all commands via subprocess | M4-02 to M4-10 | [data-model.md §Implementation Cookbook](data-model.md#test-patterns) |
| M4-13 | Implement draft save on cancel | Save `.dot-draft.yaml` on Ctrl+C if ≥1 frame entered | M4-05 | [spec.md FR-084](spec.md#functional-requirements) |

---

### Milestone 5: Examples and Golden Tests

**Objective**: Ship bundled examples that pass validation.

**Deliverables**:
- [ ] `examples/minimal.yaml` — single concept, single frame
- [ ] `examples/typical.yaml` — header/line pattern (order + order_line)
- [ ] `examples/complex.yaml` — multi-source, qualifiers, weak hooks
- [ ] Golden tests: all examples pass `dot validate`
- [ ] Negative fixtures: expected diagnostics verified

**Done when**:
- All 3 examples pass validation with exit code 0
- Invalid fixtures produce expected ERROR/WARN with correct rule IDs
- All examples pass `dot validate`

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M5-01 | Create minimal.yaml | Single concept, single hook, single frame (relation source) | M2-12 | [spec.md §5](spec.md#5-manifest-schema-v1) |
| M5-02 | Create file_based.yaml | Single concept, file/path source (QVD example) | M2-12 | [spec.md §5](spec.md#5-manifest-schema-v1) |
| M5-03 | Create typical.yaml | Order header + line items (1:M pattern) | M2-12 | [data-model.md §4-5](data-model.md#4-frame) |
| M5-04 | Create complex.yaml | Multi-source, qualifiers, tenant, weak hooks | M2-12 | [data-model.md §5](data-model.md#5-hook) |
| M5-05 | Golden tests | pytest: each example → validate → exit 0 | M5-01, M5-02, M5-03, M5-04, M4-02 | [quickstart.md](quickstart.md#milestone-checklist) |
| M5-06 | Negative fixture tests | Each invalid fixture → expected diagnostics | M2-11, M4-02 | [data-model.md §Implementation Cookbook](data-model.md#fixture-templates) |
| M5-07 | Bundle examples | Include in package data | M5-01, M5-02, M5-03, M5-04 | [quickstart.md](quickstart.md#pyprojecttoml-template) |

---

### Milestone 6: Polish and Release

**Objective**: Documentation, packaging, CI.

**Deliverables**:
- [ ] README.md with quickstart
- [ ] pyproject.toml complete with metadata
- [ ] CI workflow (GitHub Actions)
- [ ] Type checking (mypy/pyright)
- [ ] Linting (ruff)
- [ ] 100% test coverage for core module

**Done when**:
- `pip install dot-organize` works from PyPI (or test PyPI)
- CI passes on push
- README shows install + basic usage
- All public functions typed and documented

**Tasks** (ordered by dependency):

| ID | Task | Description | Depends On | Ref |
|----|------|-------------|------------|-----|
| M6-01 | Write README | Installation, quickstart, CLI reference | M5-07 | [quickstart.md](quickstart.md) |
| M6-02 | Complete pyproject.toml | Classifiers, URLs, license | M1-01 | [quickstart.md](quickstart.md#pyprojecttoml-template) |
| M6-03 | Add GitHub Actions CI | pytest, mypy --strict, ruff check/format on push | M5-05 | [spec.md NFR-040-042](spec.md#implementation-standards) |
| M6-04 | Type check all modules | mypy --strict (per NFR-041) | M4-12, M5-06 | [spec.md NFR-041](spec.md#implementation-standards) |
| M6-05 | Ensure test coverage | 100% for core/, ≥80% for cli/ | M5-06 | [data-model.md §Implementation Cookbook](data-model.md#test-patterns) |
| M6-06 | Write docstrings | All public functions documented | M4-12 | constitution §Code Quality |
| M6-07 | Test PyPI release | Verify installable package | M6-01 to M6-06 | [quickstart.md](quickstart.md#initial-setup) |

---

## Dependency Graph

```text
M1 (Models) ─────► M2 (Validation) ─────► M3 (YAML I/O)
                         │                      │
                         │                      ▼
                         └───────────────► M4 (CLI)
                                               │
                                               ▼
                                          M5 (Examples)
                                               │
                                               ▼
                                          M6 (Release)
```

**Critical path**: M1 → M2 → M3 → M4 → M5 → M6

---

## Out of Scope (Explicitly Deferred)

| Item | Reason |
|------|--------|
| HOOK SQL generation | Future feature |
| USS SQL generation | Future feature |
| Qlik script generation | Future feature |
| Graph traversal (networkx) | Future feature |
| AST manipulation (IBIS) | Future feature |
| Database introspection | Future feature |
| Manifest diff/merge | Future feature |
| Treatment syntax | Deferred from v1 |
| Comment preservation in YAML | Out of scope for v1 |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| expr validation too strict | Start with allowlist, expand based on user feedback |
| YAML output ordering inconsistent | Use ruamel.yaml with explicit key ordering |
| Wizard UX complexity | Start with minimal flow, iterate based on feedback |

---

## Success Criteria Mapping

| Spec Criteria | Implementation |
|---------------|----------------|
| SC-001: Validate <1s for 1000 lines | Pure functions, no I/O in validation loop |
| SC-002: Wizard <5min for 5 concepts | Frame-first flow with auto-derived values |
| SC-003: 100% prohibited patterns detected | All constitutional rules implemented |
| SC-004: 4 examples pass validation | Golden tests in M5 |
| SC-005: Diagnostics have rule ID + path + fix | Diagnostic model enforces structure |
| SC-006: Correct exit codes | CLI tests verify exit codes |
| SC-007: Wizard output always valid | Validation before save |

---

**Next step**: `/speckit.tasks` to generate implementation tasks from this plan.
