# Tasks: HOOK Manifest Builder

**Input**: Design documents from `/specs/001-manifest-builder/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/manifest-schema.json ✅

**Approach**: TDD (Test-Driven Development) - Tests written FIRST, must FAIL before implementation

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Based on plan.md structure:
- Source: `src/dot/`
- Tests: `tests/`
- Examples: `examples/`
- Fixtures: `tests/fixtures/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization with uv package manager

- [X] T001 Initialize project with `uv init --package dot-organize` in repository root
- [X] T002 Configure pyproject.toml with dependencies: pydantic, typer, ruamel.yaml, questionary
- [X] T003 [P] Add dev dependencies: ruff, mypy, pre-commit
- [X] T004 [P] Add test dependencies: pytest, hypothesis, pytest-cov
- [X] T005 Configure pre-commit hooks for ruff and mypy in .pre-commit-config.yaml
- [X] T006 [P] Create src/dot/__init__.py with package exports and __version__
- [X] T007 [P] Create src/dot/py.typed (PEP 561 marker)
- [X] T008 [P] Create src/dot/models/__init__.py
- [X] T009 [P] Create src/dot/core/__init__.py
- [X] T010 [P] Create src/dot/io/__init__.py
- [X] T011 [P] Create src/dot/cli/__init__.py
- [X] T012 [P] Create tests/conftest.py with shared pytest fixtures
- [X] T013 Create tests/fixtures/valid/ directory structure
- [X] T014 Create tests/fixtures/invalid/ directory structure

**Note**: `tests/fixtures/` are minimal test fixtures for unit/integration tests. `examples/` are complete, documented examples for end users. They serve different purposes and may differ in content.

**Checkpoint**: Project structure ready, `uv sync` succeeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and validation infrastructure - MUST complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational Phase (TDD - Write FIRST, must FAIL) ⚠️

- [X] T015 [P] Create tests/unit/test_models.py with tests for all models (Settings, Diagnostic, Concept, Hook, Frame, Manifest)
- [X] T016 [P] Create tests/unit/test_normalization.py with tests for naming validators (lower_snake_case, UPPER_SNAKE_CASE, hook_name, frame_name, semver)
- [X] T017 [P] Create tests/unit/test_registry.py with tests for key set derivation (including key aliases with qualifiers), concept registry, hook registry
- [X] T018 [P] Create tests/unit/test_expression.py with tests for expr validation (allowed tokens, forbidden patterns)
- [X] T019 [P] Create tests/unit/test_rules.py with tests for all ERROR rules (FRAME-001 to 006 including composite grain validation, HOOK-001 to 007 including hook name uniqueness within frame, CONCEPT-001/002/003, MANIFEST-001/002)
- [X] T020 [P] Create tests/unit/test_rules_warn.py with tests for all WARN rules (CONCEPT-W01, HOOK-W01, FRAME-W01/W02/W03, MANIFEST-W01/W02)

### Implementation for Foundational Phase

#### Models (src/dot/models/)

- [X] T021 [P] Implement Severity enum and Diagnostic model in src/dot/models/diagnostic.py
- [X] T022 [P] Implement Settings model with defaults in src/dot/models/settings.py
- [X] T023 [P] Implement Concept model in src/dot/models/concept.py
- [X] T024 Implement HookRole enum, Hook model, Source model, Frame model in src/dot/models/frame.py
- [X] T025 Implement Metadata model and Manifest root model in src/dot/models/manifest.py (imports frame, concept, settings)

#### Core Validation (src/dot/core/)

- [X] T026 [P] Implement naming validators in src/dot/core/normalization.py (is_lower_snake_case, is_upper_snake_case, is_valid_hook_name, is_valid_frame_name, is_valid_semver)
- [X] T027 Implement key set derivation in src/dot/core/registry.py (derive_key_sets, _build_key_set)
- [X] T028 Implement concept registry in src/dot/core/registry.py (derive_concepts)
- [X] T029 Implement hook registry in src/dot/core/registry.py (derive_hook_registry)
- [X] T030 Implement expr validation in src/dot/core/expression.py (allowed tokens, forbidden patterns regex)
- [X] T031 Implement MANIFEST rules in src/dot/core/rules.py (MANIFEST-001, MANIFEST-002)
- [X] T032 Implement FRAME rules in src/dot/core/rules.py (FRAME-001 to FRAME-006)
- [X] T033 Implement HOOK rules in src/dot/core/rules.py (HOOK-001 to HOOK-006, uses expr validation)
- [X] T034 Implement HOOK-007 rule in src/dot/core/rules.py (hook name uniqueness within frame)
- [X] T035 Implement CONCEPT rules in src/dot/core/rules.py (CONCEPT-001, CONCEPT-002, CONCEPT-003)
- [X] T036 Implement WARN rules in src/dot/core/rules.py (all 7 warning rules: CONCEPT-W01, HOOK-W01, FRAME-W01/W02/W03, MANIFEST-W01/W02)
- [X] T037 Implement composite validate_manifest function in src/dot/core/validation.py

#### Fixtures

- [X] T038 [P] Create tests/fixtures/valid/minimal.yaml (single concept, single hook, relation source)
- [X] T039 [P] Create tests/fixtures/valid/file_based.yaml (path source instead of relation)
- [X] T039a [P] Create tests/fixtures/valid/composite_grain.yaml (frame with multiple primary hooks for composite grain, e.g., order_lines with _hk__order + _hk__product)
- [X] T039b [P] Create tests/fixtures/valid/key_alias.yaml (same concept with different qualifiers, e.g., _hk__order__number and _hk__order__id producing ORDER~NUMBER@ERP and ORDER~ID@ERP)
- [X] T040 [P] Create tests/fixtures/invalid/missing_hooks.yaml (triggers FRAME-001)
- [X] T041 [P] Create tests/fixtures/invalid/invalid_frame_name.yaml (triggers FRAME-002)
- [X] T042 [P] Create tests/fixtures/invalid/missing_primary_hook.yaml (triggers FRAME-003)
- [X] T043 [P] Create tests/fixtures/invalid/missing_source.yaml (triggers FRAME-004)
- [X] T044 [P] Create tests/fixtures/invalid/both_relation_and_path.yaml (triggers FRAME-005)
- [X] T045 [P] Create tests/fixtures/invalid/empty_relation.yaml (triggers FRAME-006)
- [X] T046 [P] Create tests/fixtures/invalid/missing_hook_fields.yaml (triggers HOOK-001)
- [X] T047 [P] Create tests/fixtures/invalid/invalid_hook_name.yaml (triggers HOOK-002)
- [X] T048 [P] Create tests/fixtures/invalid/invalid_hook_role.yaml (triggers HOOK-003)
- [X] T049 [P] Create tests/fixtures/invalid/invalid_concept_name.yaml (triggers HOOK-004)
- [X] T050 [P] Create tests/fixtures/invalid/invalid_source_case.yaml (triggers HOOK-005)
- [X] T051 [P] Create tests/fixtures/invalid/empty_expr.yaml (triggers HOOK-006)
- [X] T052 [P] Create tests/fixtures/invalid/forbidden_expr_select.yaml (triggers HOOK-006 forbidden pattern)
- [X] T053 [P] Create tests/fixtures/invalid/duplicate_hook_name.yaml (triggers HOOK-007)
- [X] T054 [P] Create tests/fixtures/invalid/unused_concept.yaml (triggers CONCEPT-001)
- [X] T055 [P] Create tests/fixtures/invalid/short_concept_description.yaml (triggers CONCEPT-002)
- [X] T055a [P] Create tests/fixtures/invalid/duplicate_concept_name.yaml (triggers CONCEPT-003)
- [X] T056 [P] Create tests/fixtures/invalid/invalid_manifest_version.yaml (triggers MANIFEST-001)
- [X] T057 [P] Create tests/fixtures/invalid/invalid_schema_version.yaml (triggers MANIFEST-002)
- [X] T057a [P] Create tests/fixtures/warn/unknown_fields.yaml (triggers MANIFEST-W02)

**Checkpoint**: All foundation tests pass - models, validators, rules implemented

---

## Phase 3: User Story 1 - Validate Existing Manifest (Priority: P1) 🎯 MVP

**Goal**: Users can run `dot validate manifest.yaml` to check manifest compliance

**Independent Test**: Run `dot validate path/to/manifest.yaml` against valid and invalid manifests, verify correct exit codes and error messages

### Tests for User Story 1 (TDD - Write FIRST, must FAIL) ⚠️

- [X] T058 [P] [US1] Create tests/unit/test_yaml_io.py with tests for YAML reader (parse valid, parse errors with line/column)
- [X] T059 [P] [US1] Create tests/unit/test_json_io.py with tests for JSON reader/writer
- [X] T060 [P] [US1] Create tests/integration/test_io_roundtrip.py with round-trip tests (load → save → load)
- [X] T061 [P] [US1] Create tests/integration/test_cli_validate.py with CLI integration tests:
  - Valid manifest → exit 0, "Manifest is valid"
  - Invalid manifest → exit 1, ERROR with rule ID and path
  - Manifest with warnings → exit 0, WARN messages printed
  - --json flag → JSON output format
  - File not found → exit 2, clear error message
  - Parse error → exit 1, line/column in message
  - Default output contains no ANSI escape codes (NFR-010 screen reader compatibility)
  - Default output contains no ANSI escape codes (NFR-010 screen reader compatibility)

### Implementation for User Story 1

#### I/O Layer (src/dot/io/)

- [X] T062 [US1] Implement YAML reader in src/dot/io/yaml.py (parse with ruamel.yaml, return Manifest or ParseError)
- [X] T063 [US1] Implement parse error handling in src/dot/io/yaml.py (line/column extraction)
- [X] T064 [US1] Implement YAML writer in src/dot/io/yaml.py (serialize with ordered keys per data-model.md)
- [X] T065 [P] [US1] Implement JSON reader in src/dot/io/json.py
- [X] T066 [P] [US1] Implement JSON writer in src/dot/io/json.py

#### CLI (src/dot/cli/)

- [X] T067 [US1] Create typer app skeleton in src/dot/cli/main.py with --version, --help
- [X] T068 [US1] Add entry point `dot` in pyproject.toml [project.scripts]
- [X] T069 [US1] Implement validate command in src/dot/cli/validate.py (path argument, calls YAML reader + validation)
- [X] T070 [US1] Implement human-readable diagnostic output formatting in src/dot/cli/validate.py
- [X] T071 [US1] Implement --json flag for machine-readable output in src/dot/cli/validate.py
- [X] T072 [US1] Implement exit codes: 0 (valid), 1 (errors), 2 (usage/file errors) in src/dot/cli/validate.py
- [X] T072a [P] [US1] Implement --no-color flag to disable ANSI escape codes (NFR-011)

**Checkpoint**: `dot validate manifest.yaml` works correctly with all exit codes - User Story 1 complete and independently testable

---

## Phase 4: User Story 2 - Create Manifest via Interactive Wizard (Priority: P2)

**Goal**: Users can run `dot init` to create manifests through guided prompts

**Independent Test**: Run `dot init`, provide inputs, verify output file passes `dot validate`

### Tests for User Story 2 (TDD - Write FIRST, must FAIL) ⚠️

- [X] T073 [P] [US2] Create tests/integration/test_cli_init.py with wizard integration tests:
  - Complete wizard flow → valid manifest created
  - Invalid input → rejection with re-prompt
  - Summary preview before write
  - Overwrite prompt for existing file
  - --format json → JSON output
  - Ctrl+C with ≥1 frame → .dot-draft.yaml saved (verify file content)
  - Non-TTY stdin → error with helpful message

### Implementation for User Story 2

- [X] T074 [US2] Implement init command skeleton in src/dot/cli/init.py (--output, --format flags)
- [X] T075 [US2] Implement frame-first wizard workflow in src/dot/cli/init.py using questionary
- [X] T076 [US2] Implement input validation in wizard (reject invalid names with actionable errors)
- [X] T077 [US2] Implement auto-suggest for valid names based on naming conventions
- [X] T078 [US2] Implement auto-generate key set values using CONCEPT[~QUALIFIER]@SOURCE[~TENANT] recipe
- [X] T079 [US2] Implement summary preview display before writing manifest
- [X] T080 [US2] Implement overwrite confirmation prompt for existing files
- [X] T081 [US2] Implement manifest save with YAML/JSON format based on --format flag
- [X] T082 [US2] Implement Ctrl+C handler to save .dot-draft.yaml if ≥1 frame entered
- [X] T083 [US2] Implement TTY detection with helpful error for non-interactive mode

**Checkpoint**: `dot init` wizard creates valid manifests - User Story 2 complete and independently testable

---

## Phase 5: User Story 3 - Create Manifest Non-Interactively (Priority: P3)

**Goal**: CI/CD pipelines can generate manifests from config files or flags

**Independent Test**: Run `dot init --from-config seed.yaml --output manifest.yaml`, verify output

### Tests for User Story 3 (TDD - Write FIRST, must FAIL) ⚠️

- [X] T084 [P] [US3] Create tests/integration/test_cli_init_noninteractive.py with tests:
  - --from-config with valid seed → complete manifest
  - --from-config with invalid seed → exit 1 with errors
  - --concept and --source flags → minimal manifest with auto-derived key set

### Implementation for User Story 3

- [X] T085 [US3] Implement --from-config flag in src/dot/cli/init.py (parse seed YAML)
- [X] T086 [US3] Implement seed config validation with actionable error messages
- [X] T087 [US3] Implement manifest generation from seed config
- [X] T088 [US3] Implement --concept and --source flags for minimal manifest generation
- [X] T089 [US3] Implement auto-derivation of key set from command flags

**Checkpoint**: `dot init --from-config` and flag-based creation works - User Story 3 complete and independently testable

---

## Phase 6: User Story 4 - View Example Manifests (Priority: P4)

**Goal**: Users can view bundled example manifests to learn the structure

**Independent Test**: Run `dot examples list` and `dot examples show minimal`

### Tests for User Story 4 (TDD - Write FIRST, must FAIL) ⚠️

- [ ] T090 [P] [US4] Create tests/integration/test_cli_examples.py with tests:
  - `dot examples list` → lists available examples
  - `dot examples show minimal` → prints example to stdout
  - `dot examples show typical --output ./my-manifest.yaml` → writes to file
  - `dot examples show nonexistent` → exit 1 with error

### Implementation for User Story 4

- [ ] T091 [US4] Create examples/minimal.yaml (relation source, per spec.md Example A)
- [ ] T092 [P] [US4] Create examples/file_based.yaml (path source, per spec.md Example B)
- [ ] T093 [P] [US4] Create examples/typical.yaml (header/line pattern, order + order_line)
- [ ] T094 [P] [US4] Create examples/complex.yaml (multi-source, qualifiers, tenant, weak hooks)
- [ ] T095 [US4] Implement examples list command in src/dot/cli/examples.py
- [ ] T096 [US4] Implement examples show command in src/dot/cli/examples.py (--output flag)
- [ ] T097 [US4] Bundle examples in package data via pyproject.toml [tool.setuptools.package-data]
- [ ] T098 [P] [US4] Create tests/integration/test_golden.py - golden tests verifying all examples pass validation

**Checkpoint**: `dot examples` commands work - User Story 4 complete and independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI, release preparation

- [ ] T099 [P] Write README.md with installation, quickstart, CLI reference
- [ ] T100 [P] Complete pyproject.toml metadata (classifiers, URLs, license)
- [ ] T101 Add GitHub Actions CI workflow in .github/workflows/ci.yml (uv sync, pytest, mypy --strict, ruff)
- [ ] T102 Run mypy --strict and fix all type errors
- [ ] T103 Run ruff check and ruff format, fix all issues
- [ ] T104 [P] Ensure test coverage ≥80% for cli/, 100% for core/
- [ ] T105 [P] Add docstrings to all public functions
- [ ] T106 Test PyPI release with `uv build` and verify installable package
- [ ] T107 Run spec.md quickstart validation scenarios end-to-end
- [ ] T108 [P] Create tests/performance/test_validation_benchmarks.py - verify NFR-001/002/003 (validation <1s for 1000 lines, <5s for 10000 lines, <100MB memory)
- [ ] T109 [P] Verify functional paradigm compliance (NFR-050 to NFR-056): no stateful classes in core/, pure functions only, frozen models, composition over inheritance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - MVP delivery target
- **User Story 2 (Phase 4)**: Depends on Foundational, integrates with US1 for validation
- **User Story 3 (Phase 5)**: Depends on Foundational, integrates with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational and US1 (for golden tests)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories ✅
- **User Story 2 (P2)**: Can start after Foundational - Uses validation from US1 for wizard output
- **User Story 3 (P3)**: Can start after Foundational - Shares init command structure with US2
- **User Story 4 (P4)**: Can start after Foundational - Uses validate from US1 for golden tests

### Within Each Phase

- Tests MUST be written FIRST and FAIL before implementation (TDD)
- Models before services/validation
- Core validation before CLI commands
- Commit after each task or logical group

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All test creation tasks marked [P] can run in parallel
- Model implementations T021-T023 can run in parallel (no dependencies)
- Invalid fixture creation (T040-T057) can all run in parallel
- Different user stories can be worked on by different team members after Foundational

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all test files together (TDD - write failing tests first):
T015: tests/unit/test_models.py
T016: tests/unit/test_normalization.py
T017: tests/unit/test_registry.py
T018: tests/unit/test_expression.py
T019: tests/unit/test_rules.py
T020: tests/unit/test_rules_warn.py

# Launch independent model implementations together:
T021: src/dot/models/diagnostic.py
T022: src/dot/models/settings.py
T023: src/dot/models/concept.py

# Launch all invalid fixtures together:
T040-T057: tests/fixtures/invalid/*.yaml
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Validate)
4. **STOP and VALIDATE**: Test `dot validate` independently
5. Deploy/demo MVP if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Validate) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Wizard) → Test independently → Deploy/Demo
4. Add User Story 3 (Non-Interactive) → Test independently → Deploy/Demo
5. Add User Story 4 (Examples) → Test independently → Deploy/Demo
6. Polish phase → Release

### TDD Workflow Per Task

1. Write test that describes expected behavior
2. Run test → verify it FAILS (red)
3. Implement minimal code to pass test
4. Run test → verify it PASSES (green)
5. Refactor if needed
6. Commit

---

## Definition of Done (DoD)

Each task is complete when:

- [ ] Test exists and initially failed before implementation
- [ ] Implementation passes all tests
- [ ] Code passes `ruff check` and `ruff format`
- [ ] Code passes `mypy --strict` (no type errors)
- [ ] Public functions have docstrings
- [ ] Changes committed with descriptive message

Each User Story is complete when:

- [ ] All story tasks completed per DoD
- [ ] Story can be tested independently
- [ ] Story acceptance scenarios from spec.md verified
- [ ] No regressions in other stories

---

## Summary

| Phase | Tasks | Parallel Tasks | Key Deliverable |
|-------|-------|----------------|-----------------|
| Setup | T001-T014 | 10 | Project structure |
| Foundational | T015-T057a | 42 | Models, validators, rules, fixtures |
| US1: Validate | T058-T072a | 6 | `dot validate` command |
| US2: Wizard | T073-T083 | 1 | `dot init` interactive |
| US3: Non-Interactive | T084-T089 | 1 | `dot init --from-config` |
| US4: Examples | T090-T098 | 5 | `dot examples` command |
| Polish | T099-T109 | 6 | README, CI, release, benchmarks, paradigm verification |

**Total Tasks**: 115 (107 base + 8 additions: T039a, T039b, T055a, T057a, T072a, T108, T109)
**MVP Scope**: Phases 1-3 (T001-T072a) = 78 tasks
