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
uv venv
uv pip install -e ".[dev,test]"
pre-commit install
```

### CI Environment Notes

For CI/CD systems and non-interactive environments:
- The bootstrap script is designed for interactive development environments
- CI systems should use `uv pip install -e .` directly without the bootstrap wrapper
- Pre-commit hooks are optional in CI (use `make check` instead)

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
