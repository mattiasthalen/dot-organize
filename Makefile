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
	@python scripts/bootstrap.py

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
	@python scripts/bump.py patch

bump-minor:
	@python scripts/bump.py minor

bump-major:
	@python scripts/bump.py major

bump-version:
	@python scripts/bump.py version $(VERSION)

# Cleanup
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
