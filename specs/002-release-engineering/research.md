# Research: Release Engineering

**Feature**: 002-release-engineering  
**Date**: 2026-01-07  
**Purpose**: Resolve open questions and evaluate tooling options

---

## Research Tasks

### 1. Dynamic Versioning from Git Tags

**Question**: How to derive PEP 440-compliant version from git tags at build/install time?

**Options Evaluated**:

| Tool | Mechanism | PEP 440 Format Support | Integration |
|------|-----------|------------------------|-------------|
| `hatch-vcs` | Hatchling plugin, uses git tags | ✅ Native `X.Y.Z.devN+gCOMMIT` | pyproject.toml only |
| `setuptools-scm` | setuptools plugin | ✅ Native | Requires setuptools backend |
| `versioningit` | Backend-agnostic | ✅ Configurable | Complex configuration |
| Custom script | Manual git parsing | ⚠️ Must implement | Full control, maintenance burden |

**Decision**: **`hatch-vcs`**

**Rationale**:
- Project already uses `hatchling` as build backend (see pyproject.toml)
- Zero-config for standard `vMAJOR.MINOR.PATCH` tag format
- Automatically produces PEP 440 dev versions (`1.2.3.dev4+gabcdef`)
- Single source of truth: git tags → package metadata → `dot.__version__`
- Well-maintained by the Hatch project (same team as Ruff)

**Alternatives Rejected**:
- `setuptools-scm`: Would require changing build backend from hatchling
- `versioningit`: Overly complex for our straightforward tag format
- Custom script: Maintenance burden, reinventing the wheel

---

### 2. Bump Helper Implementation

**Question**: How to implement version bump commands (patch/minor/major)?

**Options Evaluated**:

| Approach | Complexity | UX | Maintenance |
|----------|------------|-----|-------------|
| Makefile targets | Low | `make bump-patch` | Easy |
| Shell script | Low | `./scripts/bump.sh patch` | Portable |
| Python CLI subcommand | Medium | `dot release bump patch` | Integrated |
| External tool (bump2version, tbump) | External dep | Tool-specific | Another dependency |

**Decision**: **Makefile targets** with thin shell script backend

**Rationale**:
- `make` is universally available on dev machines and in CI
- Makefile provides discoverability (`make help`)
- Shell script backend keeps logic simple and testable
- No new Python dependencies required
- Consistent with "simple, deterministic solutions" constraint

**Implementation**:
```makefile
bump-patch:    scripts/bump.sh patch
bump-minor:    scripts/bump.sh minor
bump-major:    scripts/bump.sh major
bump-version:  scripts/bump.sh version $(VERSION)
```

---

### 3. Bootstrap Mechanism

**Question**: Where does bootstrap live and how is it triggered?

**Options Evaluated**:

| Approach | Trigger | Idempotency | Portability |
|----------|---------|-------------|-------------|
| `postCreateCommand` inline | Devcontainer only | Hard to achieve | Poor |
| Shell script in `scripts/` | Manual or postCreateCommand | Easy | Good |
| Makefile target | Manual or postCreateCommand | Easy | Good |

**Decision**: **Shell script** (`scripts/bootstrap.sh`) called from **Makefile** (`make bootstrap`) and **devcontainer.json** `postCreateCommand`

**Rationale**:
- Single script handles all bootstrap logic
- Makefile provides entry point for manual invocation
- devcontainer.json calls the script directly for auto-bootstrap
- Script handles idempotency checks internally
- Works identically inside and outside containers

**Bootstrap Steps**:
1. Check Python/uv availability
2. Install project in editable mode with dev dependencies
3. Install pre-commit hooks
4. Display success message

---

### 4. Pre-commit Hook Selection

**Question**: Which quality checks to enforce?

**Current State**: `.pre-commit-config.yaml` already exists with:
- `trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-toml`, `check-added-large-files`
- `ruff` (linter + formatter)
- `mypy` (type checker)

**Decision**: **Keep existing hooks** — they already satisfy the quality check requirements

**Rationale**:
- Hooks are already defined and working
- Ruff covers linting + formatting (replaces black/isort/flake8)
- MyPy provides strict type checking
- Pre-commit-hooks cover basic file hygiene
- No additional hooks needed for this feature

---

### 5. Manual Check Execution

**Question**: How to run all checks on demand?

**Decision**: **`make check`** target that runs `pre-commit run --all-files`

**Rationale**:
- Uses the same hooks as pre-commit (consistency guarantee)
- Single command, discoverable via `make help`
- No additional tooling required

---

### 6. Version Surfacing

**Question**: How is version exposed to users?

**Current State**: 
- `dot --version` already implemented in CLI (uses `dot.__version__`)
- `__version__` is hardcoded in `src/dot/__init__.py`

**Decision**: 
- Replace hardcoded `__version__` with dynamic import from package metadata
- `hatch-vcs` writes version to package metadata at build time
- `importlib.metadata.version("dot-organize")` reads it at runtime

**Implementation**:
```python
# src/dot/__init__.py
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("dot-organize")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"  # Fallback for editable installs without build
```

---

## Summary of Decisions

| Open Question | Resolution |
|---------------|------------|
| Q3: Bootstrap mechanism | `scripts/bootstrap.sh` + `make bootstrap` + devcontainer integration |
| Q4: Quality checks | Keep existing `.pre-commit-config.yaml` hooks (ruff, mypy, pre-commit-hooks) |
| Tooling: Version derivation | `hatch-vcs` plugin (hatchling-native, PEP 440 compliant) |
| Tooling: Bump helpers | Makefile targets + `scripts/bump.sh` |
| Tooling: Manual checks | `make check` → `pre-commit run --all-files` |
| Tooling: Version surfacing | `importlib.metadata.version()` from hatch-vcs-written metadata |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| hatch-vcs doesn't match exact format | Low | Medium | Configurable via `[tool.hatch.version]` |
| Editable install version fallback | Medium | Low | Graceful fallback to "0.0.0+unknown" |
| Makefile not available on Windows | Low | Low | Git Bash includes make; document workaround |
| Bootstrap fails silently | Medium | High | Script exits on error, logs each step |
