# Tasks: Release Engineering

**Input**: Design documents from `/specs/002-release-engineering/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

**Tests**: This feature involves shell scripts and configuration files. Verification is via manual test commands documented in plan.md, not automated unit tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure preparation for release engineering

- [ ] T001 Create scripts directory at `scripts/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can be verified

**⚠️ CRITICAL**: User story verification depends on hatch-vcs being configured

- [ ] T002 Add hatch-vcs to build requirements in `pyproject.toml` (lines 42-44)
- [ ] T003 Add version source configuration to `pyproject.toml` ([tool.hatch.version] and [tool.hatch.build.hooks.vcs] sections)
- [ ] T004 Remove static version line from `pyproject.toml` (line 3: version = "0.1.0")
- [ ] T005 Update version import in `src/dot/__init__.py` to import from `_version.py` with fallback
- [ ] T006 Add `src/dot/_version.py` to `.gitignore`
- [ ] T007 Reinstall package to generate `_version.py`: `uv pip install -e . --force-reinstall`

**Checkpoint**: Foundation ready - `dot --version` returns dev version, user story implementation can begin

---

## Phase 3: User Story 3 - Version Resolution from Tags (Priority: P1) 🎯 MVP-Foundation

**Goal**: Maintainers can trust that version derived from git tags is exact and consistent

**Independent Test**: Create tag, reinstall, verify `dot --version` matches tag exactly

**Why first**: This is the foundational capability - bump helpers and bootstrap verification depend on version resolution working.

### Verification for User Story 3

- [ ] T008 [US3] Verify tagged commit resolves to exact version: create `v0.1.0-test` tag, reinstall, check `dot --version` shows `0.1.0.test`
- [ ] T009 [US3] Verify non-tagged commit produces dev version: delete test tag, reinstall, check version shows `0.0.0.devN+gXXX` format
- [ ] T010 [US3] Clean up test tag: `git tag -d v0.1.0-test`

**Checkpoint**: SC-001 (tagged → exact version) and SC-002 (non-tagged → dev version) verified

---

## Phase 4: User Story 1 - Version Bump and Tag Creation (Priority: P1) 🎯 MVP-Core

**Goal**: Maintainers can run single command to bump version and create annotated tag

**Independent Test**: Run `make bump-patch`, verify tag created with correct version and message

### Implementation for User Story 1

- [ ] T011 [US1] Create bump script at `scripts/bump.sh` with version parsing, bump logic, and tag creation
- [ ] T012 [US1] Make bump script executable: `chmod +x scripts/bump.sh`
- [ ] T013 [US1] Create Makefile with bump targets (`bump-patch`, `bump-minor`, `bump-major`, `bump-version`) at `Makefile`

### Verification for User Story 1

- [ ] T014 [US1] Verify bump-patch: run `make bump-patch`, confirm tag v0.0.1 created with no prior tags
- [ ] T015 [US1] Verify bump-minor: run `make bump-minor`, confirm tag v0.1.0 created
- [ ] T016 [US1] Verify bump-major: run `make bump-major`, confirm tag v1.0.0 created
- [ ] T017 [US1] Verify annotated tag message: `git show v1.0.0` shows "Release v1.0.0"
- [ ] T018 [US1] Verify dirty tree rejection: create temp file, run `make bump-patch`, confirm error message
- [ ] T019 [US1] Verify existing tag rejection: run `make bump-version VERSION=1.0.0`, confirm error message
- [ ] T020 [US1] Verify explicit version: clean tree, run `make bump-version VERSION=2.0.0`, confirm v2.0.0 created
- [ ] T021 [US1] Verify detached HEAD: `git checkout --detach`, run `make bump-patch`, confirm tag created at detached commit (edge case from spec.md)
- [ ] T022 [US1] Clean up test tags: `git tag -d v0.0.1 v0.1.0 v1.0.0 v2.0.0` and `git checkout 002-release-engineering`

**Checkpoint**: FR-004 through FR-014 verified, SC-003 (< 5 seconds) confirmed

---

## Phase 5: User Story 4 - Manual Check Execution (Priority: P2)

**Goal**: Contributors can run quality checks manually via single command

**Independent Test**: Run `make check`, verify all pre-commit hooks execute

### Implementation for User Story 4

- [ ] T023 [US4] Add `check` target to `Makefile` that runs `pre-commit run --all-files`
- [ ] T024 [US4] Add `test` target to `Makefile` that runs `pytest`
- [ ] T025 [US4] Add `help` target to `Makefile` with command documentation

### Verification for User Story 4

- [ ] T026 [US4] Verify make check: run `make check`, confirm all hooks execute
- [ ] T027 [US4] Verify make help: run `make help`, confirm all commands documented

**Checkpoint**: FR-020 (manual checks) and SC-007 (single command) verified

---

## Phase 6: User Story 2 - Developer Environment Auto-Bootstrap (Priority: P1)

**Goal**: Fresh devcontainer auto-configures with pre-commit hooks enabled

**Independent Test**: Rebuild devcontainer, verify hooks active without manual commands

**Note**: Depends on Makefile existing (Phase 4/5) for bootstrap verification commands

### Implementation for User Story 2

- [ ] T028 [US2] Create bootstrap script at `scripts/bootstrap.sh` with uv install and pre-commit setup (uses `--overwrite` flag for idempotent reinstall)
- [ ] T029 [US2] Make bootstrap script executable: `chmod +x scripts/bootstrap.sh`
- [ ] T030 [US2] Add `bootstrap` target to `Makefile` that runs `./scripts/bootstrap.sh`
- [ ] T031 [US2] Add `install` and `dev` targets to `Makefile` for manual installation
- [ ] T032 [US2] Update `.devcontainer/devcontainer.json` postCreateCommand to call bootstrap script

### Verification for User Story 2

- [ ] T033 [US2] Verify bootstrap script: run `./scripts/bootstrap.sh`, confirm all steps show success
- [ ] T034 [US2] Verify idempotency: run `./scripts/bootstrap.sh` twice, confirm no errors second run
- [ ] T035 [US2] Verify pre-commit hooks reinstall with overwrite: manually modify `.git/hooks/pre-commit`, run bootstrap, confirm hooks restored to project config (edge case from spec.md)
- [ ] T036 [US2] Verify pre-commit hooks installed: check `.git/hooks/pre-commit` exists and matches project
- [ ] T037 [US2] Verify package importable: run `python -c "import dot; print(dot.__version__)"`

**Checkpoint**: FR-015 through FR-018 verified, SC-004 (zero manual commands) and SC-005 (idempotent) confirmed, edge case (existing hooks overwrite) verified

---

## Phase 7: User Story 5 - Non-Container Development Setup (Priority: P3)

**Goal**: Contributors outside devcontainer can follow docs to set up environment

**Independent Test**: Follow documented steps on clean machine, verify identical to devcontainer

### Implementation for User Story 5

- [ ] T038 [US5] Create `docs/CONTRIBUTING.md` with devcontainer and manual setup instructions
- [ ] T039 [US5] Document tag format and version resolution behavior in CONTRIBUTING.md (FR-022)
- [ ] T040 [US5] Document bump workflow in CONTRIBUTING.md (FR-023)
- [ ] T041 [US5] Document bootstrap process in CONTRIBUTING.md (FR-024)
- [ ] T042 [US5] Document pre-commit hooks and manual execution in CONTRIBUTING.md (FR-025)
- [ ] T043 [US5] Add note about CI environment: bootstrap skips interactive prompts; CI systems should use `uv pip install -e .` directly

### Verification for User Story 5

- [ ] T044 [US5] Verify devcontainer section exists: grep "Using Devcontainer" docs/CONTRIBUTING.md
- [ ] T045 [US5] Verify manual setup section exists: grep "Manual Setup" docs/CONTRIBUTING.md
- [ ] T046 [US5] Verify tag format documented: grep "Tag Format" docs/CONTRIBUTING.md
- [ ] T047 [US5] Verify bump commands documented: grep "Bumping Versions" docs/CONTRIBUTING.md

**Checkpoint**: FR-022 through FR-025 verified, SC-006 (self-service docs) confirmed

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and integration verification

- [ ] T048 Add `clean` target to Makefile for build artifact cleanup
- [ ] T049 Update README.md with brief development section pointing to CONTRIBUTING.md
- [ ] T050 Verify complete workflow: bump version, verify resolution, run checks
- [ ] T051 Run quickstart.md validation steps as final integration check

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─► Phase 2 (Foundational) ─► Phase 3 (US3) ─► Phase 4 (US1) ─► Phase 5 (US4) ─► Phase 6 (US2) ─► Phase 7 (US5) ─► Phase 8 (Polish)
      │                    │                       │                │                │                │                │
      └── scripts/         └── hatch-vcs          └── Version      └── Bump         └── Check        └── Bootstrap    └── Docs
          dir                  configured             works            helpers          targets          works            complete
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|------------|-------------------|
| US3 (Version Resolution) | Foundational | None - must be first |
| US1 (Bump Helpers) | US3 | None - needs version to verify |
| US4 (Manual Checks) | Setup | Can parallel with US1 after Makefile created |
| US2 (Bootstrap) | US1, US4 | None - needs Makefile targets |
| US5 (Documentation) | US1, US2 | None - documents completed features |

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T002, T003, T004 can be edited together (same file) but apply sequentially
- T005 and T006 can run in parallel (different files)

**Within Phase 4 (US1 Implementation)**:
- T011 and T013 (bump.sh and Makefile) can be created in parallel

**Within Phase 7 (US5 Implementation)**:
- T039, T040, T041, T042, T043 are sections of same file - apply sequentially

---

## Implementation Strategy

### MVP First (US3 + US1)

1. Complete Phase 1: Setup (scripts/ directory)
2. Complete Phase 2: Foundational (hatch-vcs configuration)
3. Complete Phase 3: US3 (verify version resolution works)
4. Complete Phase 4: US1 (bump helpers)
5. **STOP and VALIDATE**: Can create release tags correctly

### Incremental Delivery

1. Setup + Foundational + US3 → Version resolution works
2. Add US1 → Bump helpers work → **First release possible**
3. Add US4 → Manual checks work
4. Add US2 → Bootstrap works → **Full dev experience**
5. Add US5 → Documentation complete → **Contributor-ready**
6. Polish → Clean and verified

---

## Requirements Traceability

| Requirement | Task(s) | User Story |
|-------------|---------|------------|
| FR-001 (tag format) | T002, T003 | US3 |
| FR-002 (exact version) | T008 | US3 |
| FR-003 (dev version) | T009 | US3 |
| FR-003a (version surfacing) | T005 | US3 |
| FR-004 (bump patch) | T011, T013, T014 | US1 |
| FR-005 (bump minor) | T011, T013, T015 | US1 |
| FR-006 (bump major) | T011, T013, T016 | US1 |
| FR-007 (explicit version) | T011, T013, T020 | US1 |
| Edge: Detached HEAD | T021 | US1 |
| FR-008 (find latest tag) | T011 | US1 |
| FR-009 (default v0.0.0) | T011, T014 | US1 |
| FR-010 (annotated tags) | T011, T017 | US1 |
| FR-011 (clean tree check) | T011, T018 | US1 |
| FR-012 (no overwrite) | T011, T019 | US1 |
| FR-013 (clear messages) | T011 | US1 |
| FR-014 (ignore non-SemVer) | T011 | US1 |
| FR-015 (bootstrap) | T028 | US2 |
| FR-016 (devcontainer) | T032 | US2 |
| FR-017 (idempotent) | T028, T034 | US2 |
| FR-018 (pre-commit) | T028, T035, T036 | US2 |
| Edge: Existing hooks overwrite | T035 | US2 |
| FR-019 (reinstall docs) | T042 | US5 |
| FR-020 (manual checks) | T023, T026 | US4 |
| FR-021 (outside container) | T028, T038 | US2, US5 |
| FR-022 (tag format docs) | T039 | US5 |
| FR-023 (bump docs) | T040 | US5 |
| FR-024 (bootstrap docs) | T041 | US5 |
| FR-025 (pre-commit docs) | T042 | US5 |
| Edge: CI environment | T043 | US5 |

---

## Success Criteria Traceability

| Criterion | Task(s) | Verification |
|-----------|---------|--------------|
| SC-001 (tagged → exact) | T008 | Manual verification |
| SC-002 (non-tagged → dev) | T009 | Manual verification |
| SC-003 (< 5 seconds) | T014-T021 | Time bump commands |
| SC-004 (zero manual) | T032, T037 | Rebuild devcontainer |
| SC-005 (idempotent) | T034 | Run bootstrap twice |
| SC-006 (self-service docs) | T044-T047 | Documentation review |
| SC-007 (single check cmd) | T026 | `make check` works |

---

## Notes

- This feature is infrastructure/tooling - verification is via documented manual tests, not pytest
- Shell scripts follow constitution's functional paradigm (pure functions, no global state mutation)
- All verification steps are documented in plan.md with expected outputs
- Commit after each phase or logical task group
- Clean up test tags after verification to avoid polluting git history
