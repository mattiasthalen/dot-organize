# Tasks: HOOK Manifest Builder

**Input**: Design documents from `/specs/001-manifest-builder/`  
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/manifest-schema.json ✅, quickstart.md ✅

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1=Validate, US2=Wizard, US3=Non-Interactive, US4=Examples)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Package layout, dependencies, entry point skeleton

- [ ] T001 Create pyproject.toml with pydantic, typer, ruamel.yaml deps in pyproject.toml
- [ ] T002 [P] Create package structure: src/hook/__init__.py, src/hook/py.typed
- [ ] T003 [P] Create src/hook/models/__init__.py directory structure
- [ ] T004 [P] Create src/hook/core/__init__.py directory structure
- [ ] T005 [P] Create src/hook/io/__init__.py directory structure
- [ ] T006 [P] Create src/hook/cli/__init__.py directory structure
- [ ] T007 [P] Create tests/conftest.py with shared fixtures
- [ ] T008 [P] Create tests/fixtures/valid/ and tests/fixtures/invalid/ directories
- [ ] T009 [P] Configure ruff.toml for linting/formatting

**Done when**: `pip install -e .` succeeds, package imports work

---

## Phase 2: Foundation — Data Models (Blocking)

**Purpose**: Pydantic models with frozen=True, required for ALL user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Implement Severity enum and Diagnostic model in src/hook/models/diagnostic.py
- [ ] T011 [P] Implement Settings model with defaults (hook_prefix, weak_hook_prefix, delimiter) in src/hook/models/settings.py
- [ ] T012 [P] Implement Concept model (name, description, examples, is_weak) in src/hook/models/concept.py
- [ ] T013 Implement HookRole enum and Hook model (name, role, concept, qualifier, source, tenant, expr_sql, treatment) in src/hook/models/frame.py
- [ ] T014 Implement Frame model (name, source, description, hooks) in src/hook/models/frame.py
- [ ] T015 [P] Implement Metadata model (name, description, created_at, updated_at) in src/hook/models/manifest.py
- [ ] T016 [P] Implement Targets model (hook_sql, uss_sql, qlik as empty dicts) in src/hook/models/manifest.py
- [ ] T017 Implement Manifest root model combining all models in src/hook/models/manifest.py
- [ ] T018 [P] Implement naming validators (lower_snake_case, UPPER_SNAKE_CASE, hook pattern regex) in src/hook/core/normalization.py
- [ ] T019 [P] Create minimal.yaml fixture with single frame, single hook, single concept in tests/fixtures/valid/minimal.yaml
- [ ] T020 Unit tests for all models (serialization, defaults, validation) in tests/unit/test_models.py

**Done when**: All models serialize to/from dict, frozen=True enforced, naming patterns validate

---

## Phase 3: User Story 1 — Validate Existing Manifest (P1) 🎯 MVP

**Goal**: `hook validate manifest.yaml` validates against schema + constitutional rules, outputs diagnostics

**Independent Test**: Run `hook validate tests/fixtures/valid/minimal.yaml` → exit 0; run against invalid → exit 1 with rule ID

### Core Validation Engine

- [ ] T021 [US1] Implement key set derivation function (CONCEPT[~QUALIFIER]@SOURCE[~TENANT]) in src/hook/core/registry.py
- [ ] T022 [P] [US1] Implement concept registry (unique concepts from hooks) in src/hook/core/registry.py
- [ ] T023 [P] [US1] Implement hook registry (hooks indexed by name) in src/hook/core/registry.py
- [ ] T024 [US1] Implement expr_sql allowlist validation (reject SELECT/JOIN/subqueries/non-deterministic) in src/hook/core/expression.py
- [ ] T025 [US1] Implement MANIFEST rules (MANIFEST-001, MANIFEST-002: semver validation) in src/hook/core/rules.py
- [ ] T026 [US1] Implement FRAME rules (FRAME-001 to FRAME-004) in src/hook/core/rules.py
- [ ] T027 [US1] Implement HOOK rules (HOOK-001 to HOOK-007) using expr_sql validator in src/hook/core/rules.py
- [ ] T028 [US1] Implement KEYSET rules (KEYSET-001: uniqueness) using key set registry in src/hook/core/rules.py
- [ ] T029 [US1] Implement CONCEPT rules (CONCEPT-001, CONCEPT-002) using concept registry in src/hook/core/rules.py
- [ ] T030 [US1] Implement all WARN rules (CONCEPT-W01, HOOK-W01, FRAME-W01 to W03, TARGET-W01, MANIFEST-W01) in src/hook/core/rules.py
- [ ] T031 [US1] Implement validate_manifest() orchestration function combining all rules in src/hook/core/validation.py

### YAML I/O

- [ ] T032 [US1] Implement YAML reader with ruamel.yaml, return Manifest or list[Diagnostic] in src/hook/io/yaml.py
- [ ] T033 [US1] Implement parse error handling with line/column in diagnostics in src/hook/io/yaml.py
- [ ] T034 [P] [US1] Implement YAML writer with deterministic key ordering in src/hook/io/yaml.py
- [ ] T035 [P] [US1] Implement JSON reader in src/hook/io/json.py
- [ ] T036 [P] [US1] Implement JSON writer in src/hook/io/json.py

### CLI: validate command

- [ ] T037 [US1] Create typer app skeleton with --version, --help in src/hook/cli/main.py
- [ ] T038 [US1] Add entry point `hook = "hook.cli.main:app"` in pyproject.toml [project.scripts]
- [ ] T039 [US1] Implement `hook validate <path>` command with exit codes (0=valid, 1=error, 2=usage) in src/hook/cli/validate.py
- [ ] T040 [US1] Implement human-readable diagnostic output (severity, rule_id, path, message, fix) in src/hook/cli/validate.py
- [ ] T040a [US1] Implement --no-color flag to disable ANSI escape codes (NFR-011) in src/hook/cli/validate.py
- [ ] T041 [US1] Implement --json flag for machine-readable JSON diagnostics in src/hook/cli/validate.py

### Tests & Fixtures

- [ ] T042 [P] [US1] Create invalid fixture: missing_fields.yaml (HOOK-001 violation: hook missing required fields) in tests/fixtures/invalid/
- [ ] T043 [P] [US1] Create invalid fixture: duplicate_keyset.yaml (KEYSET-001 violation: duplicate derived key sets) in tests/fixtures/invalid/
- [ ] T044 [P] [US1] Create invalid fixture: bad_expression.yaml (HOOK-006/007 violation) in tests/fixtures/invalid/
- [ ] T045 [P] [US1] Create invalid fixture: missing_primary.yaml (FRAME-003 violation) in tests/fixtures/invalid/
- [ ] T046 [P] [US1] Create invalid fixture: bad_naming.yaml (HOOK-002/004/005 violations) in tests/fixtures/invalid/
- [ ] T047 [US1] Unit tests for all 16 ERROR rules (positive + negative) in tests/unit/test_rules.py
- [ ] T048 [US1] Unit tests for all 7 WARN rules in tests/unit/test_rules.py
- [ ] T049 [US1] Unit tests for expr_sql validation (allowed + forbidden patterns) in tests/unit/test_expression.py
- [ ] T050 [US1] Integration tests for `hook validate` CLI (valid → exit 0, invalid → exit 1, --json) in tests/integration/test_cli_validate.py
- [ ] T051 [US1] Round-trip tests: load → save → load produces identical models in tests/integration/test_io.py

**Checkpoint**: 🚀 **SHIP POINT** — `hook validate` is fully functional, CI can integrate

---

## Phase 4: User Story 4 — View Example Manifests (P4, moved up)

**Goal**: `hook examples list` and `hook examples show <name>` display bundled examples

**Why moved up**: Examples are simple, provide user value, and support learning

**Independent Test**: Run `hook examples list` → shows 3 examples; `hook examples show minimal` → prints valid YAML

- [ ] T052 [US4] Create examples/minimal.yaml (single concept, single frame) in examples/
- [ ] T053 [P] [US4] Create examples/typical.yaml (order header + order_line, 1:M pattern) in examples/
- [ ] T054 [P] [US4] Create examples/complex.yaml (multi-source, qualifiers, tenant, weak hooks) in examples/
- [ ] T055 [US4] Implement `hook examples list` command in src/hook/cli/examples.py
- [ ] T056 [US4] Implement `hook examples show <name>` with stdout output in src/hook/cli/examples.py
- [ ] T057 [US4] Implement --output flag to write example to path in src/hook/cli/examples.py
- [ ] T058 [US4] Bundle examples as package data in pyproject.toml [tool.setuptools.package-data]
- [ ] T059 [US4] Golden tests: all 3 examples → `hook validate` → exit 0 in tests/integration/test_examples.py
- [ ] T060 [US4] Negative fixture tests: each invalid fixture → expected rule ID in tests/integration/test_examples.py
- [ ] T061 [US4] Integration tests for `hook examples` CLI in tests/integration/test_cli_examples.py

**Checkpoint**: `hook validate` + `hook examples` both work — users can learn from examples

---

## Phase 5: User Story 2 — Create Manifest via Interactive Wizard (P2)

**Goal**: `hook init` guides user through frame-first manifest creation

**Independent Test**: Run `hook init`, provide inputs, verify output file passes `hook validate`

- [ ] T062 [US2] Implement wizard skeleton with typer prompts in src/hook/cli/init.py
- [ ] T063 [US2] Implement frame-first workflow: frames → hooks → key sets → concepts in src/hook/cli/init.py
- [ ] T064 [US2] Implement real-time input validation (reject invalid names, prompt again) in src/hook/cli/init.py
- [ ] T064a [US2] Implement auto-suggest valid names based on naming conventions (FR-026) in src/hook/cli/init.py
- [ ] T065 [US2] Implement YAML preview before writing in src/hook/cli/init.py
- [ ] T066 [US2] Implement overwrite confirmation (prompt if file exists) in src/hook/cli/init.py
- [ ] T067 [US2] Implement --output flag with format detection (.json → JSON, else YAML) in src/hook/cli/init.py
- [ ] T068 [US2] Implement Ctrl+C handler: save .hook-draft.yaml if ≥1 frame entered (FR-084) in src/hook/cli/init.py
- [ ] T069 [US2] Detect non-TTY stdin and exit with error message in src/hook/cli/init.py
- [ ] T070 [US2] Integration tests for wizard (mock stdin, verify output passes validation) in tests/integration/test_cli_init.py

**Checkpoint**: `hook init` produces valid manifests interactively

---

## Phase 6: User Story 3 — Create Manifest Non-Interactively (P3)

**Goal**: `hook init --from-config seed.yaml` generates manifest from config file

**Independent Test**: Run `hook init --from-config tests/fixtures/seeds/minimal.yaml` → valid manifest

- [ ] T071 [US3] Create seed config schema (minimal input format) in src/hook/models/seed.py
- [ ] T072 [US3] Implement `hook init --from-config <path>` command in src/hook/cli/init.py
- [ ] T073 [US3] Implement --concept and --source flags for single-concept shortcut in src/hook/cli/init.py
- [ ] T074 [US3] Implement auto-derivation: key sets, timestamps, defaults in src/hook/cli/init.py
- [ ] T075 [P] [US3] Create seed fixture: tests/fixtures/seeds/minimal.yaml
- [ ] T076 [P] [US3] Create seed fixture: tests/fixtures/seeds/multi_frame.yaml
- [ ] T077 [US3] Integration tests for --from-config and --concept flags in tests/integration/test_cli_init.py

**Checkpoint**: Manifest generation is fully automatable for CI/CD

---

## Phase 7: Optional marimo UI

**Purpose**: Local reactive wizard UI as optional extra

**Ship independently**: Can be deferred without blocking core CLI release

- [ ] T078 Add marimo as optional dependency: `hook[ui]` extra in pyproject.toml
- [ ] T079 Create wizard notebook skeleton in src/hook/ui/wizard.py
- [ ] T080 [P] Implement settings form (prefix, delimiter) in src/hook/ui/wizard.py
- [ ] T081 Implement frame form (add/edit frames with hooks) in src/hook/ui/wizard.py
- [ ] T082 [P] Implement concept form (optional enrichment) in src/hook/ui/wizard.py
- [ ] T083 Implement reactive validation display (errors/warnings) in src/hook/ui/wizard.py
- [ ] T084 Implement live YAML preview panel in src/hook/ui/wizard.py
- [ ] T085 Implement save button (write manifest to disk) in src/hook/ui/wizard.py
- [ ] T086 Manual testing: verify UI produces valid manifests

**Checkpoint**: `pip install hook[ui]` + `marimo run src/hook/ui/wizard.py` opens wizard

---

## Phase 8: Polish & Release

**Purpose**: Documentation, CI, packaging for PyPI release

- [ ] T087 [P] Write README.md with installation, quickstart, CLI reference
- [ ] T088 [P] Complete pyproject.toml metadata (classifiers, URLs, license)
- [ ] T089 [P] Add GitHub Actions CI workflow (.github/workflows/ci.yml): pytest, mypy, ruff
- [ ] T090 [P] Add pre-commit hooks configuration (.pre-commit-config.yaml)
- [ ] T091 Type check all modules with mypy strict mode
- [ ] T092 Ensure test coverage: 100% for src/hook/core/, ≥80% for src/hook/cli/
- [ ] T092a Add performance benchmark: validate 1000-line manifest in <1s (NFR-001) in tests/benchmark/
- [ ] T093 Write docstrings for all public functions
- [ ] T094 Test PyPI release: verify `pip install hook` works

---

## Dependencies & Execution Order

### Phase Dependencies

```text
Phase 1: Setup ─────────────────────────────────────► (can start immediately)
                         │
                         ▼
Phase 2: Foundation ────────────────────────────────► (BLOCKS all user stories)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
Phase 3: US1        Phase 4: US4    (after US1)
(Validate)          (Examples)
         │               │
         ▼               │
Phase 5: US2 ◄───────────┘
(Wizard)
         │
         ▼
Phase 6: US3
(Non-Interactive)
         │
         ├────────────────────────────┐
         ▼                            ▼
Phase 7: marimo UI              Phase 8: Release
(OPTIONAL)
```

### Critical Path: Setup → Foundation → US1 (Validate) → US4 (Examples) → Release

### Ship Points

1. **After Phase 3 (T051)**: `hook validate` is shippable — CI integration possible
2. **After Phase 4 (T061)**: Add `hook examples` — learning support
3. **After Phase 5 (T070)**: Add `hook init` — interactive creation
4. **After Phase 6 (T077)**: Add --from-config — CI/CD automation
5. **After Phase 7 (T086)**: Add marimo UI (optional)
6. **After Phase 8 (T094)**: PyPI release

---

## Parallel Opportunities

### Within Phase 2 (Foundation)
```bash
# Can run in parallel:
T011: Settings model
T012: Concept model
T015: Metadata model
T016: Targets model
T018: Naming validators
T019: minimal.yaml fixture
```

### Within Phase 3 (Validation)
```bash
# Can run in parallel:
T022: Concept registry
T023: Hook registry
T034: YAML writer
T035: JSON reader
T036: JSON writer
T042-T046: Invalid fixtures
```

### Within Phase 4 (Examples)
```bash
# Can run in parallel:
T052-T054: All three examples
```

---

## Summary

| Phase | Tasks | Est. Days | Ship Point? |
|-------|-------|-----------|-------------|
| 1. Setup | T001-T009 (9) | 0.5 | No |
| 2. Foundation | T010-T020 (11) | 1.5 | No |
| 3. US1 Validate | T021-T051 + T040a (32) | 4 | ✅ Yes |
| 4. US4 Examples | T052-T061 (10) | 1 | ✅ Yes |
| 5. US2 Wizard | T062-T070 + T064a (10) | 1.5 | ✅ Yes |
| 6. US3 Non-Interactive | T071-T077 (7) | 1 | ✅ Yes |
| 7. marimo UI | T078-T086 (9) | 1.5 | Optional |
| 8. Release | T087-T094 + T092a (9) | 1 | ✅ Yes |
| **Total** | **97 tasks** | **~12 days** | |

**MVP (Phases 1-4)**: 61 tasks, ~7 days → shippable `hook validate` + `hook examples`
