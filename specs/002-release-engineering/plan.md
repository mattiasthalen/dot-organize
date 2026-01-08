# Implementation Plan: Release Engineering

**Branch**: `002-release-engineering` | **Date**: 2026-01-07 | **Spec**: [spec.md](spec.md)

---

## Summary

Implement git-tag-based semantic versioning using `hatch-vcs`, Makefile-driven bump helpers, and automated developer environment bootstrap with pre-commit integration.

---

## Technical Context

**Language/Version**: Python 3.10+ (existing constraint)
**Primary Dependencies**: hatch-vcs (new), pre-commit (existing)
**Build Backend**: hatchling (existing)
**Testing**: pytest (existing), manual verification
**Target Platform**: Linux/macOS (devcontainer: Debian bookworm)
**Project Type**: CLI/library package
**Performance Goals**: Bump commands complete in < 5 seconds
**Constraints**: Zero new runtime dependencies
**Scale/Scope**: Single maintainer local workflow

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Status | Notes |
|------|--------|-------|
| VII. Minimal, Deterministic, Tested | ✅ | Using established tools (hatch-vcs, make), no custom logic |
| VIII. Version Control | ✅ | Git tags as single source of truth |
| X. External Tools | ✅ | hatch-vcs is build-time only, not runtime |
| Pre-commit checks | ✅ | Using existing ruff, mypy hooks |

**Post-Design Recheck**: All implementations follow constitution constraints.

---

## Phase Dependencies

```
Phase 1 (Versioning) ────► Phase 2 (Bump Helpers) ────► Phase 3 (Bootstrap) ────► Phase 4 (Documentation)
     │                          │                              │
     └── hatch-vcs installed    └── scripts/ created           └── make targets available
         _version.py generated      Makefile exists                bootstrap.sh tested
```

**Critical Path**: Phases MUST be executed in order. Each phase depends on artifacts from the previous.

---

## Phase 1: Dynamic Versioning (FR-001 through FR-003a)

**Goal**: Version derived from git tags via `hatch-vcs`.
**Research Reference**: [research.md §1 - Dynamic Versioning from Git Tags](research.md#1-dynamic-versioning-from-git-tags)

#### Task Sequence

| # | Task | File | Action |
|---|------|------|--------|
| 1.1 | Add hatch-vcs dependency | `pyproject.toml` | Modify build-system |
| 1.2 | Configure version source | `pyproject.toml` | Add [tool.hatch.version] |
| 1.3 | Remove static version | `pyproject.toml` | Delete version line |
| 1.4 | Update version import | `src/dot/__init__.py` | Replace |
| 1.5 | Ignore generated file | `.gitignore` | Append |
| 1.6 | Verify version resolution | Terminal | Test |

#### 1.1 Add hatch-vcs to build requirements

**File**: `pyproject.toml`

**Current** (lines 42-44):
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Replace with**:
```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"
```

#### 1.2 Configure version source

**File**: `pyproject.toml` (add after build-system section)

```toml
[tool.hatch.version]
source = "vcs"
raw-options = { version_scheme = "guess-next-dev" }

[tool.hatch.build.hooks.vcs]
version-file = "src/dot/_version.py"
```

#### 1.3 Remove static version

**File**: `pyproject.toml` (line 3)

**Delete this line**:
```toml
version = "0.1.0"
```

**Changes summary**:
- Add `hatch-vcs` to build requirements
- Remove static `version = "0.1.0"` (now derived from git)
- Configure version source as `vcs` (git)
- Generate `_version.py` at build time for runtime access

#### 1.4 Update version import

**File**: `src/dot/__init__.py`

**Current**:
```python
"""dot - Data Organize Tool for validating and creating manifests using the HOOK methodology."""

__version__ = "0.1.0"

# Models will be exported after implementation
...
```

**Replace entire file with**:
```python
"""dot - Data Organize Tool for validating and creating manifests using the HOOK methodology."""

try:
    from dot._version import __version__
except ImportError:
    # Fallback for editable installs before first build
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
]
```

#### 1.5 Add _version.py to .gitignore

**File**: `.gitignore` (append to end of file)

```
# Generated version file
src/dot/_version.py
```

#### 1.6 Verification

**Run these commands in order**:

```bash
# Step 1: Reinstall package to trigger hatch-vcs
uv pip install -e . --force-reinstall

# Step 2: Check that _version.py was generated
ls -la src/dot/_version.py
# Expected: File exists

# Step 3: Check version without tag
dot --version
# Expected: 0.0.0.devN+gXXXXXXX (dev version with commit hash)

# Step 4: Create a test tag and verify
git tag v0.1.0-test
uv pip install -e . --force-reinstall
dot --version
# Expected: 0.1.0.test (or similar - tag is recognized)

# Step 5: Clean up test tag
git tag -d v0.1.0-test
```

| Criterion | Command | Expected |
|-----------|---------|----------|
| SC-001: Tagged → exact version | `git tag v0.1.0 && uv pip install -e . && dot --version` | `0.1.0` |
| SC-002: Non-tagged → dev version | `dot --version` (no tag on HEAD) | `0.1.0.devN+gXXX` |
| FR-001: Tag format | Tags matching `vX.Y.Z` recognized | ✓ |
| FR-014: Non-SemVer ignored | Create `git tag test`, version unchanged | ✓ |

**Rollback if failed**:
```bash
# Revert pyproject.toml changes
git checkout pyproject.toml src/dot/__init__.py .gitignore
rm -f src/dot/_version.py
```

---

### Phase 2: Bump Helpers (FR-004 through FR-014)

**Goal**: Maintainers can bump versions with single commands.
**Research Reference**: [research.md §2 - Bump Helper Implementation](research.md#2-bump-helper-implementation)
**Depends on**: Phase 1 complete (version resolution must work for verification)

**Note**: Originally planned as bash scripts, but migrated to Python for cross-platform compatibility (NFR-001). See Phase 9 tasks (T052-T060) for final implementation.

#### Task Sequence

| # | Task | File | Action |
|---|------|------|--------|
| 2.1 | Create scripts directory | `scripts/` | Create dir |
| 2.2 | Create bump script | `scripts/bump.py` | Create |
| 2.3 | *(N/A - Python scripts don't need chmod)* | — | — |
| 2.4 | Create Makefile | `Makefile` | Create |
| 2.5 | Verify bump commands | Terminal | Test |

#### 2.1 Create scripts directory

```bash
mkdir -p scripts
```

#### 2.2 Create bump script

**File**: `scripts/bump.sh` (create new file)

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bump version and create annotated git tag
# Usage: ./scripts/bump.sh [patch|minor|major|version X.Y.Z]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

error() { echo -e "${RED}ERROR:${NC} $1" >&2; exit 1; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Check for dirty working tree (FR-011)
check_clean() {
    if [[ -n "$(git status --porcelain)" ]]; then
        if [[ "${FORCE:-}" == "true" ]]; then
            warn "Working tree is dirty (proceeding due to --force)"
        else
            error "Working tree is not clean. Commit or stash changes first, or use --force."
        fi
    fi
}

# Get latest SemVer tag (FR-008, FR-014)
get_latest_version() {
    local latest
    latest=$(git tag -l 'v[0-9]*.[0-9]*.[0-9]*' --sort=-v:refname | head -n1)
    if [[ -z "$latest" ]]; then
        echo "v0.0.0"  # FR-009: default version
    else
        echo "$latest"
    fi
}

# Parse version components
parse_version() {
    local version="$1"
    version="${version#v}"  # Strip leading 'v'
    IFS='.' read -r MAJOR MINOR PATCH <<< "$version"
}

# Bump version (FR-004, FR-005, FR-006)
bump_version() {
    local bump_type="$1"
    local current="$2"
    parse_version "$current"

    case "$bump_type" in
        patch)
            PATCH=$((PATCH + 1))
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        *)
            error "Invalid bump type: $bump_type (use patch, minor, or major)"
            ;;
    esac

    echo "v${MAJOR}.${MINOR}.${PATCH}"
}

# Validate SemVer format (FR-007)
validate_semver() {
    local version="$1"
    if [[ ! "$version" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        error "Invalid SemVer format: $version (expected vX.Y.Z or X.Y.Z)"
    fi
    # Ensure 'v' prefix
    [[ "$version" =~ ^v ]] || version="v$version"
    echo "$version"
}

# Check if tag exists (FR-012)
check_tag_exists() {
    local tag="$1"
    if git rev-parse "$tag" >/dev/null 2>&1; then
        error "Tag $tag already exists. Cannot overwrite."
    fi
}

# Create annotated tag (FR-010)
create_tag() {
    local tag="$1"
    git tag -a "$tag" -m "Release $tag"
    success "Created annotated tag: $tag"
    echo ""
    echo "To push the tag, run:"
    echo "  git push origin $tag"
}

# Main
main() {
    cd "$REPO_ROOT"

    # Parse arguments
    local action="${1:-}"
    local explicit_version="${2:-}"

    # Handle --force flag
    for arg in "$@"; do
        [[ "$arg" == "--force" ]] && FORCE=true
    done

    if [[ -z "$action" ]]; then
        echo "Usage: $0 [patch|minor|major|version X.Y.Z] [--force]"
        echo ""
        echo "Commands:"
        echo "  patch           Bump patch version (1.2.3 → 1.2.4)"
        echo "  minor           Bump minor version (1.2.3 → 1.3.0)"
        echo "  major           Bump major version (1.2.3 → 2.0.0)"
        echo "  version X.Y.Z   Create tag for specific version"
        echo ""
        echo "Options:"
        echo "  --force         Allow bump with dirty working tree"
        exit 1
    fi

    check_clean

    local current_version
    current_version=$(get_latest_version)
    local new_version

    case "$action" in
        patch|minor|major)
            new_version=$(bump_version "$action" "$current_version")
            echo "Current version: $current_version"
            echo "Bumping $action → $new_version"
            ;;
        version)
            if [[ -z "$explicit_version" ]]; then
                error "Usage: $0 version X.Y.Z"
            fi
            new_version=$(validate_semver "$explicit_version")
            echo "Creating explicit version: $new_version"
            ;;
        *)
            error "Unknown action: $action"
            ;;
    esac

    check_tag_exists "$new_version"
    create_tag "$new_version"
}

main "$@"
```

#### 2.3 Make script executable

```bash
chmod +x scripts/bump.sh
```

#### 2.4 Create Makefile

**File**: `Makefile`

```makefile
.PHONY: help install dev check test bump-patch bump-minor bump-major bump-version bootstrap clean

# Default target
help:
	@echo "dot-organize development tasks"
	@echo ""
	@echo "Setup:"
	@echo "  make bootstrap     Set up development environment (run first)"
	@echo "  make install       Install package in editable mode"
	@echo "  make dev           Install with dev dependencies"
	@echo ""
	@echo "Quality:"
	@echo "  make check         Run all quality checks (linting, formatting, types)"
	@echo "  make test          Run test suite"
	@echo ""
	@echo "Release:"
	@echo "  make bump-patch    Bump patch version and create tag (1.2.3 → 1.2.4)"
	@echo "  make bump-minor    Bump minor version and create tag (1.2.3 → 1.3.0)"
	@echo "  make bump-major    Bump major version and create tag (1.2.3 → 2.0.0)"
	@echo "  make bump-version VERSION=X.Y.Z  Create tag for specific version"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove build artifacts and caches"

# Setup targets
bootstrap:
	@./scripts/bootstrap.sh

install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev,test]"

# Quality targets (FR-020)
check:
	pre-commit run --all-files

test:
	pytest

# Release targets (FR-004, FR-005, FR-006, FR-007)
bump-patch:
	@./scripts/bump.sh patch

bump-minor:
	@./scripts/bump.sh minor

bump-major:
	@./scripts/bump.sh major

bump-version:
	@./scripts/bump.sh version $(VERSION)

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
```

#### 2.5 Verification

**Run these commands in order**:

```bash
# Step 1: Verify bump.sh is executable
ls -la scripts/bump.sh
# Expected: -rwxr-xr-x

# Step 2: Test bump-patch (no tags exist yet)
make bump-patch
# Expected: Current version: v0.0.0, creating v0.0.1

# Step 3: Verify tag was created
git tag -l 'v*'
# Expected: v0.0.1

# Step 4: Verify annotated tag
git show v0.0.1
# Expected: Shows "Release v0.0.1" message

# Step 5: Test bump-minor
make bump-minor
# Expected: v0.0.1 → v0.1.0

# Step 6: Test bump-major
make bump-major
# Expected: v0.1.0 → v1.0.0

# Step 7: Test dirty tree rejection
echo "test" > temp.txt
make bump-patch
# Expected: ERROR - working tree not clean

# Step 8: Test existing tag rejection
rm temp.txt
make bump-version VERSION=1.0.0
# Expected: ERROR - tag v1.0.0 already exists

# Step 9: Clean up test tags
git tag -d v0.0.1 v0.1.0 v1.0.0
```

| Criterion | Test | Expected |
|-----------|------|----------|
| FR-004: Bump patch | `make bump-patch` | Increments patch |
| FR-005: Bump minor | `make bump-minor` | Increments minor, resets patch |
| FR-006: Bump major | `make bump-major` | Increments major, resets minor/patch |
| FR-007: Explicit version | `make bump-version VERSION=2.0.0` | Creates v2.0.0 |
| FR-009: No tags default | With no tags, bump-patch | Creates v0.0.1 |
| FR-010: Annotated tag | `git show v0.0.1` | Shows "Release v0.0.1" |
| FR-011: Dirty tree | With uncommitted changes | Fails with error |
| FR-012: No overwrite | Bump to existing tag | Fails with error |
| FR-013: Clear messages | Success/failure output | Color-coded, user-friendly |
| SC-003: Speed | Any bump command | Completes < 5 seconds |

**Rollback if failed**:
```bash
# Remove scripts and Makefile
rm -rf scripts/ Makefile
# Clean up any test tags
git tag -l 'v*' | xargs -r git tag -d
```

---

### Phase 3: Developer Bootstrap (FR-015 through FR-021)

**Goal**: Devcontainer auto-bootstraps; manual bootstrap works identically.
**Research Reference**: [research.md §3 - Bootstrap Mechanism](research.md#3-bootstrap-mechanism)
**Depends on**: Phase 2 complete (Makefile targets used by bootstrap verification)

#### Task Sequence

| # | Task | File | Action |
|---|------|------|--------|
| 3.1 | Create bootstrap script | `scripts/bootstrap.sh` | Create |
| 3.2 | Make scripts executable | `scripts/*.sh` | chmod +x |
| 3.3 | Update devcontainer.json | `.devcontainer/devcontainer.json` | Modify |
| 3.4 | Verify bootstrap works | Terminal | Test |

#### 3.1 Create bootstrap script

**File**: `scripts/bootstrap.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bootstrap development environment
# Idempotent - safe to run multiple times (FR-017)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}→${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }

cd "$REPO_ROOT"

echo "========================================"
echo "  dot-organize Development Setup"
echo "========================================"
echo ""

# Step 1: Check prerequisites
info "Checking prerequisites..."
command -v uv >/dev/null 2>&1 || { echo "ERROR: uv is required but not installed."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "ERROR: git is required but not installed."; exit 1; }
success "Prerequisites satisfied (uv, git)"

# Step 2: Install package with dev dependencies (FR-015)
info "Installing package with dev dependencies..."
uv pip install -e ".[dev,test]" --quiet
success "Package installed in editable mode"

# Step 3: Install pre-commit hooks (FR-018, FR-019)
info "Installing pre-commit hooks..."
if command -v pre-commit >/dev/null 2>&1; then
    pre-commit install --install-hooks --overwrite >/dev/null 2>&1
    success "Pre-commit hooks installed"
else
    echo "WARNING: pre-commit not found. Run 'uv pip install pre-commit' then 'pre-commit install'"
fi

# Step 4: Verify installation
info "Verifying installation..."
if python -c "import dot; print(f'dot version: {dot.__version__}')" 2>/dev/null; then
    success "Installation verified"
else
    echo "WARNING: Could not verify installation"
fi

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  make check    - Run quality checks"
echo "  make test     - Run test suite"
echo "  make help     - See all available commands"
echo ""
```

#### 3.2 Make scripts executable

```bash
chmod +x scripts/bootstrap.sh scripts/bump.sh
```

#### 3.3 Update devcontainer.json (FR-016)

**File**: `.devcontainer/devcontainer.json`

```jsonc
{
  "name": "dot-organize",
  "image": "mcr.microsoft.com/devcontainers/python:3.12-bookworm",
  "remoteUser": "vscode",

  "features": {
    "ghcr.io/devcontainers-extra/features/uv:1": {}
  },

  "postCreateCommand": "uv tool install specify-cli --from git+https://github.com/github/spec-kit.git && ./scripts/bootstrap.sh",

  "customizations": {
    "vscode": {
      "extensions": [
        "charliermarsh.ruff",
        "eamodio.gitlens",
        "GitHub.copilot-chat",
        "GitHub.copilot",
        "ms-python.mypy-type-checker",
        "ms-python.python",
        "ms-python.vscode-pylance"
      ]
    }
  }
}
```

#### 3.4 Verification

**Run these commands in order**:

```bash
# Step 1: Run bootstrap script manually
./scripts/bootstrap.sh
# Expected: All steps show green checkmarks

# Step 2: Verify idempotency
./scripts/bootstrap.sh
# Expected: Completes without errors or duplicate work

# Step 3: Verify pre-commit hooks installed
ls -la .git/hooks/pre-commit
# Expected: File exists and is executable

# Step 4: Verify make check works
make check
# Expected: All pre-commit hooks run

# Step 5: Verify package is importable
python -c "import dot; print(dot.__version__)"
# Expected: Version string printed
```

| Criterion | Test | Expected |
|-----------|------|----------|
| FR-015: Automated bootstrap | `./scripts/bootstrap.sh` | Completes successfully |
| FR-016: Devcontainer auto-run | Rebuild devcontainer | Bootstrap runs automatically |
| FR-017: Idempotent | Run bootstrap twice | No errors second time |
| FR-018: Pre-commit installed | `ls .git/hooks/pre-commit` | File exists |
| FR-019: Manual reinstall | See CONTRIBUTING.md | Documented |
| FR-020: Manual checks | `make check` | Runs all hooks |
| FR-021: Works outside container | Run on local machine | Same behavior |
| SC-004: Zero manual commands | Fresh devcontainer | Hooks active without user action |
| SC-005: Idempotent | Multiple runs | No errors or changes |

**Rollback if failed**:
```bash
# Remove bootstrap script
rm -f scripts/bootstrap.sh
# Revert devcontainer.json changes
git checkout .devcontainer/devcontainer.json
```

---

### Phase 4: Documentation (FR-022 through FR-025)

**Goal**: Clear contributor and release documentation.
**Research Reference**: [research.md §6 - Version Surfacing and Documentation](research.md#6-version-surfacing-and-documentation)
**Depends on**: Phase 3 complete (docs reference bootstrap/make commands)

#### Task Sequence

| # | Task | File | Action |
|---|------|------|--------|
| 4.1 | Create CONTRIBUTING.md | `docs/CONTRIBUTING.md` | Create |
| 4.2 | Update README.md | `README.md` | Modify (add dev section) |
| 4.3 | Verify documentation | Manual | Review |

#### 4.1 Create CONTRIBUTING.md

**File**: `docs/CONTRIBUTING.md`

```markdown
# Contributing to dot-organize

## Development Setup

### Using Devcontainer (Recommended)

1. Open the repository in VS Code with the Dev Containers extension
2. Click "Reopen in Container" when prompted
3. Wait for the container to build - setup is automatic!

The devcontainer will:
- Install Python 3.12 and uv
- Install the package with dev dependencies
- Enable pre-commit hooks

### Manual Setup

1. Ensure you have Python 3.10+ and [uv](https://github.com/astral-sh/uv) installed
2. Clone the repository
3. Run the bootstrap script:

```bash
./scripts/bootstrap.sh
```

Or manually:

```bash
uv pip install -e ".[dev,test]"
pre-commit install
```

## Development Workflow

### Running Checks

```bash
make check    # Run all quality checks (ruff, mypy, pre-commit hooks)
make test     # Run test suite
```

Pre-commit hooks run automatically on each commit. To run manually:

```bash
pre-commit run --all-files
```

### Available Commands

```bash
make help     # Show all available commands
```

## Versioning and Releases

### How Versioning Works

This project uses **git tags as the single source of truth** for versioning:

- **Release versions**: Tags like `v1.2.3` → package version `1.2.3`
- **Development versions**: Commits after `v1.2.3` → `1.2.3.dev4+gabcdef`

The version is automatically derived from git tags at build time using [hatch-vcs](https://github.com/ofek/hatch-vcs).

### Tag Format

Tags MUST follow semantic versioning with a `v` prefix:

```
v1.0.0      ✓ Valid
v0.2.1      ✓ Valid
1.0.0       ✗ Invalid (missing v prefix)
v1.0        ✗ Invalid (missing patch)
v1.0.0-rc1  ✗ Invalid (pre-release not supported)
```

### Bumping Versions

Maintainers can create new version tags using:

```bash
make bump-patch    # 1.2.3 → 1.2.4
make bump-minor    # 1.2.3 → 1.3.0
make bump-major    # 1.2.3 → 2.0.0

# Or for a specific version:
make bump-version VERSION=2.0.0
```

**Requirements**:
- Working tree must be clean (committed)
- Tag must not already exist

### Releasing

1. Ensure all changes are committed and pushed
2. Bump the version: `make bump-patch` (or minor/major)
3. Push the tag: `git push origin v1.2.4`

The tag push will be used by CI/CD to publish releases (coming in a future feature).

## Commit Message Format

Use the following prefixes:

| Prefix | Usage |
|--------|-------|
| `spec:` | Specification changes |
| `impl:` | Implementation changes |
| `docs:` | Documentation only |
| `fix:` | Bug fixes |
| `refactor:` | Code restructuring |
| `chore:` | Tooling, CI, dependencies |

Example: `impl: add YAML validation for manifest schema`
```

#### 4.2 Update README.md (add versioning section)

Add a brief section to the existing README pointing to CONTRIBUTING.md for development setup.

#### 4.3 Verification

**Manual review checklist**:

```bash
# Step 1: Verify CONTRIBUTING.md exists
cat docs/CONTRIBUTING.md
# Expected: Full documentation rendered

# Step 2: Verify devcontainer setup documented
grep -A5 "Using Devcontainer" docs/CONTRIBUTING.md
# Expected: Steps for container-based setup

# Step 3: Verify manual setup documented
grep -A10 "Manual Setup" docs/CONTRIBUTING.md
# Expected: Steps for local machine setup

# Step 4: Verify bump workflow documented
grep -A5 "Bumping Versions" docs/CONTRIBUTING.md
# Expected: make bump-* commands documented

# Step 5: Verify tag format documented
grep -A10 "Tag Format" docs/CONTRIBUTING.md
# Expected: v prefix and format explained
```

| Criterion | Test | Expected |
|-----------|------|----------|
| FR-022: Tag format documented | Search for "Tag Format" | Section explains `vX.Y.Z` |
| FR-023: Bump workflow documented | Search for "Bumping" | Shows bump commands |
| FR-024: Bootstrap documented | Search for "Setup" | Both devcontainer and manual |
| FR-025: Pre-commit documented | Search for "pre-commit" | Installation and usage |
| SC-006: Self-service docs | New contributor reads docs | Can follow without help |
| SC-007: Single check command | Search for "make check" | Documented |

**Rollback if failed**:
```bash
# Remove documentation
rm -f docs/CONTRIBUTING.md
# Revert README changes
git checkout README.md
```

---

## Rollout / Migration

### Initial Baseline Version

Since no tags exist, the first release workflow will be:

1. Complete all implementation
2. Run `make bump-patch` to create `v0.0.1`
3. Push tag: `git push origin v0.0.1`

This establishes the baseline. Subsequent releases use normal bump workflow.

### Maintainer Flow

```
1. Complete feature work
2. Commit all changes
3. make bump-patch    # or minor/major
4. git push origin v0.1.0
```

---

## Requirements Traceability

| Requirement | Phase | Implementation |
|-------------|-------|----------------|
| FR-001 | 1 | hatch-vcs tag pattern |
| FR-002 | 1 | hatch-vcs version resolution |
| FR-003 | 1 | hatch-vcs dev version format |
| FR-003a | 1 | `_version.py` + `__init__.py` import |
| FR-004 | 2 | `scripts/bump.sh patch` |
| FR-005 | 2 | `scripts/bump.sh minor` |
| FR-006 | 2 | `scripts/bump.sh major` |
| FR-007 | 2 | `scripts/bump.sh version X.Y.Z` |
| FR-008 | 2 | `git tag -l` parsing in bump.sh |
| FR-009 | 2 | Default to v0.0.0 in bump.sh |
| FR-010 | 2 | `git tag -a -m "Release vX.Y.Z"` |
| FR-011 | 2 | `git status --porcelain` check |
| FR-012 | 2 | `git rev-parse` existence check |
| FR-013 | 2 | Color-coded success/error messages |
| FR-014 | 2 | Tag pattern filter in bump.sh |
| FR-015 | 3 | `scripts/bootstrap.sh` |
| FR-016 | 3 | devcontainer.json postCreateCommand |
| FR-017 | 3 | Idempotent script design |
| FR-018 | 3 | `pre-commit install` in bootstrap |
| FR-019 | 3 | Documented in CONTRIBUTING.md |
| FR-020 | 3 | `make check` target |
| FR-021 | 3 | Script works outside container |
| FR-022-025 | 4 | docs/CONTRIBUTING.md |

---

## Next Feature (Out of Scope)

**CI/CD Release Automation** (deferred per spec clarification):
- GitHub Actions workflow triggered on tag push
- Build and publish to PyPI
- Create GitHub Release with changelog

This will be specified and planned as a separate feature.
