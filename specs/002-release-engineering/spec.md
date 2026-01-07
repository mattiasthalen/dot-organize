# Feature Specification: Release Engineering

**Feature Branch**: `002-release-engineering`
**Created**: 2026-01-07
**Status**: Draft
**Input**: User description: "Release engineering — git-tag SemVer + developer environment bootstrap + pre-commit enablement"

---

## Clarifications

### Session 2026-01-07

- Q: What is the exact dev-version format for non-tagged commits? → A: PEP 440 local version format: `MAJOR.MINOR.PATCH.devN+gCOMMIT` (e.g., `1.2.3.dev4+gabcdef`)
- Q: How/where is the resolved version surfaced? → A: Both CLI command (`dot --version`) and package metadata (`dot.__version__`)
- Q: Should CI/CD release automation be included in this feature? → A: Deferred to follow-on feature (this feature = local workflow only)
- Q: What format should annotated tag messages use? → A: Simple release prefix: `Release vX.Y.Z`
- Q: What is the default starting version when no SemVer tags exist? → A: `v0.0.0` (first bump creates `v0.0.1`)

---

## Overview

This feature establishes a reliable, low-friction maintainer workflow for releasing and contributing to the project. It introduces semantic versioning derived from git tags as the single source of truth, provides local helper commands for version bumping, and ensures a self-bootstrapping developer environment with automatic pre-commit hook enablement.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Version Bump and Tag Creation (Priority: P1)

As a maintainer, I can run a single command to bump patch/minor/major and create the next annotated SemVer tag locally, so I can prepare releases efficiently without manual version tracking.

**Why this priority**: Version management is the core of release engineering. Without reliable tagging, releases cannot happen. This is the foundational capability that all other release workflows depend on.

**Independent Test**: Can be fully tested by running bump commands on a repository with existing tags and verifying correct next version calculation and tag creation.

**Acceptance Scenarios**:

1. **Given** the repository has a latest tag `v1.2.3`, **When** I run the "bump patch" command, **Then** an annotated tag `v1.2.4` is created locally with an appropriate message.
2. **Given** the repository has a latest tag `v1.2.3`, **When** I run the "bump minor" command, **Then** an annotated tag `v1.3.0` is created locally.
3. **Given** the repository has a latest tag `v1.2.3`, **When** I run the "bump major" command, **Then** an annotated tag `v2.0.0` is created locally.
4. **Given** the repository has no SemVer tags, **When** I run a bump patch command, **Then** the system uses default `v0.0.0` and creates tag `v0.0.1`.
5. **Given** a tag for the computed next version already exists, **When** I run a bump command, **Then** the command fails with a clear error message and does not modify any tags.
6. **Given** the working tree has uncommitted changes, **When** I run a bump command without an override flag, **Then** the command fails with a clear message indicating the dirty state.
7. **Given** I want to create a specific version tag, **When** I run the "tag explicit version" command with a valid SemVer, **Then** that exact annotated tag is created locally.

---

### User Story 2 - Developer Environment Auto-Bootstrap (Priority: P1)

As a contributor, when I open the repository in the intended dev environment (e.g., devcontainer), the environment bootstraps automatically and pre-commit is enabled without manual installation steps, so I can start contributing immediately.

**Why this priority**: Equally critical as version management—without a working dev environment, contributors cannot effectively work on the project. This directly impacts contributor onboarding and code quality.

**Independent Test**: Can be fully tested by creating a fresh devcontainer instance and verifying that all dev dependencies are installed and pre-commit hooks are active without any manual commands.

**Acceptance Scenarios**:

1. **Given** a fresh devcontainer is created from the repository, **When** the container finishes initialization, **Then** the development environment is fully configured and ready to use.
2. **Given** the bootstrap has already run, **When** the bootstrap runs again (e.g., container rebuild), **Then** it completes successfully without errors (idempotent).
3. **Given** the devcontainer is initialized, **When** I check the git hooks, **Then** pre-commit hooks are installed and active.
4. **Given** pre-commit hooks are installed, **When** I attempt to commit code, **Then** the configured quality checks run automatically before the commit is created.

---

### User Story 3 - Version Resolution from Tags (Priority: P1)

As a maintainer, I can push a tag and trust that the version used by build/release artifacts matches the tag exactly, so releases are consistent and traceable.

**Why this priority**: Essential for release integrity—the version embedded in artifacts must match the git tag to ensure traceability and reproducibility.

**Independent Test**: Can be tested by checking out a tagged commit and verifying the resolved version matches the tag, then checking out a non-tagged commit and verifying a distinct dev version is produced.

**Acceptance Scenarios**:

1. **Given** the current commit has a release tag `v1.2.3`, **When** the version is resolved, **Then** the project version is exactly `1.2.3`.
2. **Given** the current commit does not have a release tag, **When** the version is resolved, **Then** a dev-version is produced that is distinguishable from release versions and traceable to the commit.
3. **Given** multiple tags exist on different commits, **When** resolving version at each commit, **Then** each resolution is deterministic and reproducible.

---

### User Story 4 - Manual Check Execution (Priority: P2)

As a contributor, I can run the same checks locally that pre-commit runs, in a consistent way, so I can verify my changes before committing or debug failing checks.

**Why this priority**: Important for developer experience but not blocking—contributors can still commit and have checks run. This enables proactive quality verification.

**Independent Test**: Can be tested by running the documented "check all files" command and verifying it executes the same checks as pre-commit hooks.

**Acceptance Scenarios**:

1. **Given** pre-commit is installed, **When** I run the documented command to check all files, **Then** all configured quality checks execute against the entire codebase.
2. **Given** a check fails, **When** I review the output, **Then** I can identify which check failed and what needs to be fixed.

---

### User Story 5 - Non-Container Development Setup (Priority: P3)

As a contributor working outside the devcontainer, I can follow documented steps to set up my local development environment, so I can contribute without using containers.

**Why this priority**: The devcontainer is the primary onboarding path, but supporting local development expands contributor accessibility. Lower priority because the devcontainer provides the best experience.

**Independent Test**: Can be tested by following the documented manual setup steps on a clean machine and verifying the environment works identically to the devcontainer.

**Acceptance Scenarios**:

1. **Given** I am on a supported OS without the devcontainer, **When** I follow the documented bootstrap steps, **Then** my environment is set up with all necessary dependencies.
2. **Given** I have completed manual setup, **When** I run the pre-commit hook installation command, **Then** hooks are installed and active.

---

### Edge Cases

- What happens when the git history has non-SemVer tags mixed with SemVer tags?
  - The system MUST ignore non-conforming tags and only consider valid SemVer tags when determining the latest version.
- What happens when someone tries to bump from a detached HEAD state?
  - The bump command should work from any git state as long as the working tree is clean; the tag is created at the current commit.
- What happens if pre-commit is already installed with different hooks?
  - Bootstrap should update/reinstall hooks to match the project configuration (idempotent behavior).
- What happens when running bootstrap in a CI environment?
  - Bootstrap should detect non-interactive environments and skip interactive prompts or devcontainer-specific setup.

---

## Requirements *(mandatory)*

### Functional Requirements

#### A) Semantic Versioning from Git Tags

- **FR-001**: System MUST accept tags in the format `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`) as valid release tags.
- **FR-002**: System MUST resolve the project version to exactly `MAJOR.MINOR.PATCH` when the current commit is at a release tag.
- **FR-003**: System MUST resolve a deterministic dev-version in PEP 440 local version format (`MAJOR.MINOR.PATCH.devN+gCOMMIT`) when the current commit is not at a release tag; the dev-version MUST be distinguishable from release versions and traceable to the specific commit.
- **FR-003a**: System MUST surface the resolved version via CLI command (`dot --version`) and package metadata (`dot.__version__`).
- **FR-004**: System MUST provide a "bump patch" helper command that increments the patch version.
- **FR-005**: System MUST provide a "bump minor" helper command that increments the minor version and resets patch to 0.
- **FR-006**: System MUST provide a "bump major" helper command that increments the major version and resets minor and patch to 0.
- **FR-007**: System MUST provide a "tag explicit version" helper command that creates a tag for a user-specified valid SemVer.
- **FR-008**: Bump helpers MUST find the latest SemVer tag from git history to determine the current version.
- **FR-009**: Bump helpers MUST use default version `v0.0.0` when no SemVer tags exist (first patch bump creates `v0.0.1`).
- **FR-010**: Bump helpers MUST create annotated tags (not lightweight tags) with message format `Release vX.Y.Z`.
- **FR-011**: Bump helpers MUST refuse to execute if the working tree is not clean, unless explicitly overridden with a flag.
- **FR-012**: Bump helpers MUST refuse to overwrite or recreate existing tags.
- **FR-013**: Bump helpers MUST provide clear, user-facing success and failure messages.
- **FR-014**: System MUST ignore non-SemVer tags when determining the latest version.

#### B) Developer Environment Bootstrap

- **FR-015**: System MUST provide an automated bootstrap mechanism that sets up the development environment.
- **FR-016**: Bootstrap MUST run automatically when the devcontainer is created or rebuilt.
- **FR-017**: Bootstrap MUST be idempotent—safe to run multiple times without side effects.
- **FR-018**: Bootstrap MUST install and enable pre-commit hooks automatically.
- **FR-019**: System MUST provide a documented command to manually (re)install pre-commit hooks.
- **FR-020**: System MUST provide a documented command to run all quality checks on the entire codebase on demand.
- **FR-021**: Bootstrap MUST work for local development outside containers when run manually.

#### C) Documentation

- **FR-022**: Documentation MUST explain the tag format and version resolution behavior (tagged vs. non-tagged).
- **FR-023**: Documentation MUST explain how to bump versions and push tags.
- **FR-024**: Documentation MUST explain how dev bootstrap works for both devcontainer and non-container environments.
- **FR-025**: Documentation MUST explain how pre-commit is enabled and how to run checks manually.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A release tag deterministically produces the exact corresponding project version 100% of the time.
- **SC-002**: Non-tagged commits deterministically produce a consistent dev-version that differs from release versions.
- **SC-003**: Bump commands correctly compute and create the next version tag in under 5 seconds.
- **SC-004**: Opening a fresh devcontainer results in a fully functional dev environment with pre-commit hooks active within the container initialization time, requiring zero manual commands.
- **SC-005**: The bootstrap process can run multiple times consecutively without errors or state changes after the first run.
- **SC-006**: Contributors can find and follow setup/release documentation without external assistance (documentation completeness).
- **SC-007**: All pre-commit quality checks can be run manually via a single documented command.

---

## Assumptions

- The repository already has a devcontainer configuration that can be extended.
- The project uses Python and has a `pyproject.toml` for package configuration.
- Maintainers have git installed and understand basic git operations (commit, push, tag).
- The repository is hosted on a platform that supports annotated tags (e.g., GitHub).

---

## Out of Scope

- Selection of specific implementation tools/libraries for version computation or packaging.
- Definition of specific linters, formatters, or type-checkers for pre-commit hooks.
- CI/CD release automation (GitHub release creation, package publishing)—**confirmed deferred** to follow-on feature.
- Changes to domain functionality.

---

## Open Questions (to resolve in planning)

1. ~~What is the exact dev-version format for non-tagged commits?~~ → **Resolved**: PEP 440 local version `MAJOR.MINOR.PATCH.devN+gCOMMIT`
2. ~~How/where is the resolved version surfaced?~~ → **Resolved**: Both CLI (`dot --version`) and package metadata (`dot.__version__`)
3. What is the exact bootstrap mechanism and where does it live? (scripts, make targets, etc.)
4. Which quality checks are enforced via pre-commit hooks?
5. ~~Should CI/CD release automation be included in this feature or deferred to a follow-on feature?~~ → **Resolved**: Deferred to follow-on feature
