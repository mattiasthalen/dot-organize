"""Examples command for dot CLI (T095-T096).

Provides built-in example manifests for users to learn from.

Commands:
- dot examples list: Show available examples
- dot examples show <name>: Display example content
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

# Examples metadata
EXAMPLES: dict[str, dict[str, str]] = {
    "minimal": {
        "file": "minimal.yaml",
        "description": "Simplest valid manifest - single frame from database",
        "features": "Basic structure, relation source, single hook",
    },
    "file_based": {
        "file": "file_based.yaml",
        "description": "Loading data from file paths (CSV, Parquet)",
        "features": "Path source, glob patterns, S3/GCS paths",
    },
    "typical": {
        "file": "typical.yaml",
        "description": "Common header/line pattern with relationships",
        "features": "Multiple frames, entity relationships, SQL sources",
    },
    "complex": {
        "file": "complex.yaml",
        "description": "Enterprise data mesh with advanced features",
        "features": "Qualifiers, tenants, weak hooks, multi-source",
    },
}


def _get_examples_dir() -> Path:
    """Get the examples directory path.

    Examples are bundled with the package, so we look relative to this file
    or in the standard package location.
    """
    # Try package data location first (installed package)
    import dot

    package_dir = Path(dot.__file__).parent
    examples_dir = package_dir / "examples"
    if examples_dir.is_dir():
        return examples_dir

    # Fall back to development location (repo root)
    # Go up from src/dot/cli/examples.py to repo root
    repo_root = Path(__file__).parent.parent.parent.parent
    examples_dir = repo_root / "examples"
    if examples_dir.is_dir():
        return examples_dir

    raise FileNotFoundError(
        "Examples directory not found. "
        "Please ensure the package is installed correctly."
    )


def _read_example(name: str) -> str:
    """Read an example file by name.

    Args:
        name: Example name (e.g., "minimal", "typical")

    Returns:
        Example file content as string

    Raises:
        FileNotFoundError: If example doesn't exist
    """
    if name not in EXAMPLES:
        raise FileNotFoundError(f"Example '{name}' not found")

    examples_dir = _get_examples_dir()
    file_path = examples_dir / EXAMPLES[name]["file"]

    if not file_path.exists():
        raise FileNotFoundError(f"Example file not found: {file_path}")

    return file_path.read_text()


# Create examples app as a subcommand group
examples_app = typer.Typer(
    name="examples",
    help="Show built-in example manifests",
    no_args_is_help=True,
)


@examples_app.command("list")
def list_examples() -> None:
    """List available example manifests."""
    console = Console()

    table = Table(
        title="Available Examples",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Features", style="dim")

    for name, info in EXAMPLES.items():
        table.add_row(name, info["description"], info["features"])

    console.print(table)
    console.print()
    console.print("[dim]Use 'dot examples show <name>' to view an example[/dim]")


@examples_app.command("show")
def show_example(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the example to show (e.g., minimal, typical, complex)"
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Write to file instead of stdout",
        ),
    ] = None,
) -> None:
    """Show an example manifest.

    Use --output to save the example to a file.
    """
    console = Console(stderr=True)

    try:
        content = _read_example(name)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        available = ", ".join(EXAMPLES.keys())
        console.print(f"[dim]Available examples: {available}[/dim]")
        raise typer.Exit(1)

    if output:
        output.write_text(content)
        console.print(f"[green]✓[/green] Example saved to: {output}")
    else:
        # Print raw content to stdout for piping
        print(content, end="")
