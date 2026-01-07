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

# Step 2: Create/update virtual environment and install dependencies (FR-015)
info "Creating virtual environment and installing dependencies..."
uv venv --quiet 2>/dev/null || true
uv pip install -e ".[dev,test]" --quiet
success "Package installed in editable mode with dev dependencies"

# Step 3: Install pre-commit hooks (FR-018, FR-019)
info "Installing pre-commit hooks..."
if uv run pre-commit --version >/dev/null 2>&1; then
    uv run pre-commit install --install-hooks --overwrite >/dev/null 2>&1
    success "Pre-commit hooks installed"
else
    echo "WARNING: pre-commit not available. Check installation."
fi

# Step 4: Verify installation
info "Verifying installation..."
if uv run python -c "import dot; print(f'dot version: {dot.__version__}')" 2>/dev/null; then
    success "Installation verified"
else
    echo "WARNING: Could not verify installation"
fi

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "Activate the environment with:"
echo "  source .venv/bin/activate"
echo ""
echo "Then run:"
echo "  make check    - Run quality checks"
echo "  make test     - Run test suite"
echo "  make help     - See all available commands"
echo ""
