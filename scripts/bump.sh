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
