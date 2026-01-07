# Quickstart: Release Engineering

**Feature**: 002-release-engineering  
**Purpose**: Quick reference for implementing this feature

---

## Implementation Order

```
Phase 1: Dynamic Versioning     → FR-001 to FR-003a
Phase 2: Bump Helpers           → FR-004 to FR-014
Phase 3: Developer Bootstrap    → FR-015 to FR-021
Phase 4: Documentation          → FR-022 to FR-025
```

---

## Phase 1: Dynamic Versioning

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `pyproject.toml` | Modify | Add hatch-vcs config |
| `src/dot/__init__.py` | Modify | Import from `_version.py` |
| `.gitignore` | Modify | Ignore generated `_version.py` |

### Key Config (pyproject.toml)

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]

[tool.hatch.version]
source = "vcs"

[tool.hatch.build.hooks.vcs]
version-file = "src/dot/_version.py"
```

### Verification

```bash
# Create test tag
git tag v0.1.0

# Rebuild and check version
uv pip install -e . --force-reinstall
dot --version  # Should show: 0.1.0

# Delete test tag
git tag -d v0.1.0
```

---

## Phase 2: Bump Helpers

### Files to Create

| File | Action | Purpose |
|------|--------|---------|
| `scripts/bump.sh` | Create | Version bump logic |
| `Makefile` | Create | Task runner |

### Key Commands

```bash
make bump-patch              # 1.2.3 → 1.2.4
make bump-minor              # 1.2.3 → 1.3.0
make bump-major              # 1.2.3 → 2.0.0
make bump-version VERSION=X  # Explicit version
```

### Verification

```bash
# With no tags, should create v0.0.1
make bump-patch
git tag -l  # Shows: v0.0.1

# Check annotated message
git show v0.0.1  # Shows: "Release v0.0.1"

# Cleanup test tag
git tag -d v0.0.1
```

---

## Phase 3: Bootstrap

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `scripts/bootstrap.sh` | Create | Dev environment setup |
| `.devcontainer/devcontainer.json` | Modify | Add bootstrap to postCreateCommand |

### Verification

```bash
# Manual bootstrap
./scripts/bootstrap.sh

# Verify pre-commit installed
ls -la .git/hooks/pre-commit

# Verify idempotent (run again)
./scripts/bootstrap.sh

# Verify checks work
make check
```

---

## Phase 4: Documentation

### Files to Create

| File | Action | Purpose |
|------|--------|---------|
| `docs/CONTRIBUTING.md` | Create | Developer workflow docs |

### Content Requirements

- [ ] Tag format explained
- [ ] Bump workflow explained
- [ ] Devcontainer setup explained
- [ ] Manual setup explained
- [ ] Pre-commit usage explained
- [ ] `make check` documented

---

## Success Checklist

- [ ] `dot --version` shows version from git tag
- [ ] Non-tagged commits show dev version (X.Y.Z.devN+gXXX)
- [ ] `make bump-patch/minor/major` creates correct tags
- [ ] Bump fails on dirty working tree
- [ ] Bump fails on existing tag
- [ ] Fresh devcontainer has pre-commit hooks
- [ ] `make check` runs all quality checks
- [ ] CONTRIBUTING.md is complete
