#!/usr/bin/env python3
"""Bootstrap development environment.

Usage: python scripts/bootstrap.py

Idempotent - safe to run multiple times (FR-017).
Cross-platform Python implementation (NFR-001).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# ANSI colors (work on Windows 10+ and Unix)
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def info(msg: str) -> None:
    """Print info message."""
    print(f"{BLUE}→{NC} {msg}")


def success(msg: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓{NC} {msg}")


def run_command(*args: str, check: bool = True, quiet: bool = False) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            args,
            capture_output=quiet,
            text=True,
            check=check,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def command_exists(cmd: str) -> bool:
    """Check if a command exists on PATH."""
    return shutil.which(cmd) is not None


def main() -> None:
    """Main entry point."""
    # Change to repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    os.chdir(repo_root)

    print("========================================")
    print("  dot-organize Development Setup")
    print("========================================")
    print()

    # Step 1: Check prerequisites
    info("Checking prerequisites...")

    if not command_exists("uv"):
        print("ERROR: uv is required but not installed.")
        print("Install from: https://github.com/astral-sh/uv")
        sys.exit(1)

    if not command_exists("git"):
        print("ERROR: git is required but not installed.")
        sys.exit(1)

    success("Prerequisites satisfied (uv, git)")

    # Step 2: Create/update virtual environment and install dependencies (FR-015)
    info("Creating virtual environment and installing dependencies...")

    # Create venv if it doesn't exist
    run_command("uv", "venv", "--quiet", check=False, quiet=True)

    # Install package with dev dependencies
    if not run_command("uv", "pip", "install", "-e", ".[dev,test]", "--quiet", quiet=True):
        print("WARNING: Failed to install dependencies. Try running manually:")
        print("  uv pip install -e '.[dev,test]'")
    else:
        success("Package installed in editable mode with dev dependencies")

    # Step 3: Install pre-commit hooks (FR-018, FR-019)
    info("Installing pre-commit hooks...")

    # Check if pre-commit is available via uv run
    if run_command("uv", "run", "pre-commit", "--version", check=False, quiet=True):
        if run_command(
            "uv",
            "run",
            "pre-commit",
            "install",
            "--install-hooks",
            "--overwrite",
            check=False,
            quiet=True,
        ):
            success("Pre-commit hooks installed")
        else:
            print("WARNING: Failed to install pre-commit hooks")
    else:
        print("WARNING: pre-commit not available. Check installation.")

    # Step 4: Verify installation
    info("Verifying installation...")

    result = subprocess.run(
        ["uv", "run", "python", "-c", "import dot; print(f'dot version: {dot.__version__}')"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        print(result.stdout.strip())
        success("Installation verified")
    else:
        print("WARNING: Could not verify installation")

    print()
    print("========================================")
    print("  Setup complete!")
    print("========================================")
    print()

    # Platform-specific activation instructions
    if sys.platform == "win32":
        print("Activate the environment with:")
        print("  .venv\\Scripts\\activate")
    else:
        print("Activate the environment with:")
        print("  source .venv/bin/activate")

    print()
    print("Then run:")
    print("  make check    - Run quality checks")
    print("  make test     - Run test suite")
    print("  make help     - See all available commands")
    print()


if __name__ == "__main__":
    main()
