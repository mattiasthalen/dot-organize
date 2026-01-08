#!/usr/bin/env python3
"""Bump version and create annotated git tag.

Usage: python scripts/bump.py [patch|minor|major|version X.Y.Z] [--force]

Cross-platform Python implementation (NFR-001).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

# ANSI colors (work on Windows 10+ and Unix)
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def error(msg: str) -> NoReturn:
    """Print error and exit."""
    print(f"{RED}ERROR:{NC} {msg}", file=sys.stderr)
    sys.exit(1)


def success(msg: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓{NC} {msg}")


def warn(msg: str) -> None:
    """Print warning message."""
    print(f"{YELLOW}⚠{NC} {msg}")


def run_git(*args: str) -> str:
    """Run git command and return output."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def run_git_check(*args: str) -> bool:
    """Run git command and return success status."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def check_clean(force: bool) -> None:
    """Check for dirty working tree (FR-011)."""
    status = run_git("status", "--porcelain")
    if status:
        if force:
            warn("Working tree is dirty (proceeding due to --force)")
        else:
            error("Working tree is not clean. Commit or stash changes first, or use --force.")


def get_latest_version() -> str:
    """Get latest SemVer tag (FR-008, FR-014)."""
    # Get all semver tags sorted by version
    output = run_git("tag", "-l", "v[0-9]*.[0-9]*.[0-9]*", "--sort=-v:refname")
    tags = output.split("\n") if output else []
    return tags[0] if tags and tags[0] else "v0.0.0"  # FR-009: default version


def parse_version(version: str) -> tuple[int, int, int]:
    """Parse version string into components."""
    version = version.lstrip("v")
    parts = version.split(".")
    return int(parts[0]), int(parts[1]), int(parts[2])


def bump_version(bump_type: str, current: str) -> str:
    """Bump version (FR-004, FR-005, FR-006)."""
    major, minor, patch = parse_version(current)

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        error(f"Invalid bump type: {bump_type} (use patch, minor, or major)")

    return f"v{major}.{minor}.{patch}"


def validate_semver(version: str) -> str:
    """Validate SemVer format (FR-007)."""
    pattern = r"^v?\d+\.\d+\.\d+$"
    if not re.match(pattern, version):
        error(f"Invalid SemVer format: {version} (expected vX.Y.Z or X.Y.Z)")

    # Ensure 'v' prefix
    if not version.startswith("v"):
        version = f"v{version}"
    return version


def check_tag_exists(tag: str) -> None:
    """Check if tag exists (FR-012)."""
    if run_git_check("rev-parse", tag):
        error(f"Tag {tag} already exists. Cannot overwrite.")


def create_tag(tag: str) -> None:
    """Create annotated tag (FR-010)."""
    subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
        check=True,
    )
    success(f"Created annotated tag: {tag}")
    print()
    print("To push the tag, run:")
    print(f"  git push origin {tag}")


def print_usage() -> None:
    """Print usage information."""
    print("Usage: python scripts/bump.py [patch|minor|major|version X.Y.Z] [--force]")
    print()
    print("Commands:")
    print("  patch           Bump patch version (1.2.3 → 1.2.4)")
    print("  minor           Bump minor version (1.2.3 → 1.3.0)")
    print("  major           Bump major version (1.2.3 → 2.0.0)")
    print("  version X.Y.Z   Create tag for specific version")
    print()
    print("Options:")
    print("  --force         Allow bump with dirty working tree")


def main() -> None:
    """Main entry point."""
    # Change to repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    import os

    os.chdir(repo_root)

    # Parse arguments
    args = sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]

    if not args:
        print_usage()
        sys.exit(1)

    action = args[0]
    explicit_version = args[1] if len(args) > 1 else None

    check_clean(force)

    current_version = get_latest_version()

    if action in ("patch", "minor", "major"):
        new_version = bump_version(action, current_version)
        print(f"Current version: {current_version}")
        print(f"Bumping {action} → {new_version}")
    elif action == "version":
        if not explicit_version:
            error("Usage: python scripts/bump.py version X.Y.Z")
        new_version = validate_semver(explicit_version)
        print(f"Creating explicit version: {new_version}")
    else:
        error(f"Unknown action: {action}")

    check_tag_exists(new_version)
    create_tag(new_version)


if __name__ == "__main__":
    main()
