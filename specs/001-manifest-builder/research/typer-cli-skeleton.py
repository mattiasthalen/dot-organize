#!/usr/bin/env python3
"""
Typer CLI Skeleton with Nested Subcommands and Rich Output

This skeleton demonstrates:
1. Main commands: `validate`, `init`
2. Nested subcommands: `examples list`, `examples show <name>`
3. Rich colored output with `--no-color` flag for accessibility
4. Exit codes: 0 (success), 1 (validation error), 2 (usage error)

Usage:
    python typer-cli-skeleton.py --help
    python typer-cli-skeleton.py validate manifest.json
    python typer-cli-skeleton.py init
    python typer-cli-skeleton.py examples list
    python typer-cli-skeleton.py examples show my-example
    python typer-cli-skeleton.py --no-color validate manifest.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# =============================================================================
# Exit Codes (following Unix conventions)
# =============================================================================

class ExitCode:
    """Standard exit codes for the CLI."""
    SUCCESS = 0           # Command completed successfully
    VALIDATION_ERROR = 1  # Validation failed (e.g., invalid manifest)
    USAGE_ERROR = 2       # Usage error (e.g., file not found, bad arguments)


# =============================================================================
# Console Configuration (Rich integration with --no-color support)
# =============================================================================

# Global console instances - will be configured by the callback
# Using None initially; they get configured based on --no-color flag
console: Console = Console()
err_console: Console = Console(stderr=True)


def configure_console(no_color: bool) -> None:
    """
    Configure Rich consoles based on --no-color flag.
    
    Rich respects the NO_COLOR environment variable automatically,
    but we also support an explicit --no-color CLI flag.
    
    When no_color=True:
    - color_system=None disables all ANSI color codes
    - This ensures output works in environments without color support
    """
    global console, err_console
    
    if no_color:
        # Disable all colors - outputs plain text
        console = Console(color_system=None, force_terminal=False)
        err_console = Console(stderr=True, color_system=None, force_terminal=False)
    else:
        # Auto-detect color support (default behavior)
        console = Console()
        err_console = Console(stderr=True)


# =============================================================================
# Main Application
# =============================================================================

app = typer.Typer(
    name="myapp",
    help="A CLI tool with nested subcommands and Rich output.",
    add_completion=False,  # Set to True if you want shell completion
    no_args_is_help=True,  # Show help when no command is provided
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable colored output for accessibility.",
            is_eager=True,  # Process this before other options
        ),
    ] = False,
) -> None:
    """
    MyApp - A demonstration CLI with Rich output.
    
    Use --no-color to disable ANSI color codes for accessibility
    or when piping output to files/other commands.
    """
    # Skip configuration during shell completion
    if ctx.resilient_parsing:
        return
    
    # Configure consoles based on --no-color flag
    configure_console(no_color)


# =============================================================================
# Main Commands: validate, init
# =============================================================================

@app.command()
def validate(
    file_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the file to validate.",
            exists=False,  # We handle existence check ourselves for custom exit code
        ),
    ],
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            "-s",
            help="Enable strict validation mode.",
        ),
    ] = False,
) -> None:
    """
    Validate a manifest or configuration file.
    
    Exit codes:
    - 0: Validation successful
    - 1: Validation failed (file is invalid)
    - 2: Usage error (file not found)
    """
    # Check if file exists - exit code 2 for usage error
    if not file_path.exists():
        err_console.print(
            Panel(
                f"[bold red]Error:[/bold red] File not found: [cyan]{file_path}[/cyan]",
                title="File Not Found",
                border_style="red",
            )
        )
        raise typer.Exit(code=ExitCode.USAGE_ERROR)
    
    # Simulate validation logic
    console.print(f"[dim]Validating:[/dim] [cyan]{file_path}[/cyan]")
    
    if strict:
        console.print("[dim]Mode:[/dim] [yellow]strict[/yellow]")
    
    # Example: Check file extension as simple validation
    if file_path.suffix not in (".json", ".yaml", ".yml", ".toml"):
        err_console.print(
            Panel(
                f"[bold red]Validation Error:[/bold red] Unsupported file type: [cyan]{file_path.suffix}[/cyan]\n"
                "Supported types: .json, .yaml, .yml, .toml",
                title="Validation Failed",
                border_style="red",
            )
        )
        raise typer.Exit(code=ExitCode.VALIDATION_ERROR)
    
    # Validation successful
    console.print(
        Panel(
            f"[bold green]✓[/bold green] File [cyan]{file_path}[/cyan] is valid!",
            title="Validation Passed",
            border_style="green",
        )
    )
    raise typer.Exit(code=ExitCode.SUCCESS)


@app.command()
def init(
    directory: Annotated[
        Optional[Path],
        typer.Argument(
            help="Directory to initialize. Defaults to current directory.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing configuration.",
        ),
    ] = False,
) -> None:
    """
    Initialize a new project configuration.
    
    Creates a default manifest.json in the specified directory.
    """
    target_dir = directory or Path.cwd()
    
    if not target_dir.exists():
        err_console.print(
            f"[bold red]Error:[/bold red] Directory not found: [cyan]{target_dir}[/cyan]"
        )
        raise typer.Exit(code=ExitCode.USAGE_ERROR)
    
    config_file = target_dir / "manifest.json"
    
    if config_file.exists() and not force:
        err_console.print(
            f"[bold yellow]Warning:[/bold yellow] Configuration already exists: [cyan]{config_file}[/cyan]\n"
            "Use [bold]--force[/bold] to overwrite."
        )
        raise typer.Exit(code=ExitCode.VALIDATION_ERROR)
    
    # Create config (simulated)
    console.print(f"[dim]Creating configuration in:[/dim] [cyan]{target_dir}[/cyan]")
    console.print("[bold green]✓[/bold green] Project initialized successfully!")


# =============================================================================
# Sub-Application: examples (nested subcommands)
# =============================================================================

# Create a separate Typer app for the "examples" command group
examples_app = typer.Typer(
    name="examples",
    help="Manage and explore example configurations.",
    no_args_is_help=True,
)

# Add the sub-app to the main app
# This creates the nested structure: myapp examples <subcommand>
app.add_typer(examples_app, name="examples")


# Sample data for examples
EXAMPLES_DATA = {
    "basic": {
        "description": "A minimal configuration example",
        "complexity": "low",
        "content": '{\n  "name": "basic-project",\n  "version": "1.0.0"\n}',
    },
    "advanced": {
        "description": "Full-featured configuration with all options",
        "complexity": "high",
        "content": '{\n  "name": "advanced-project",\n  "version": "2.0.0",\n  "features": ["auth", "api", "db"]\n}',
    },
    "minimal": {
        "description": "Absolute minimum required fields",
        "complexity": "low",
        "content": '{\n  "name": "minimal"\n}',
    },
}


@examples_app.command("list")
def examples_list(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed information for each example.",
        ),
    ] = False,
) -> None:
    """
    List all available example configurations.
    
    Use --verbose to see descriptions and complexity levels.
    """
    if not EXAMPLES_DATA:
        console.print("[yellow]No examples available.[/yellow]")
        raise typer.Exit(code=ExitCode.SUCCESS)
    
    if verbose:
        # Rich table for detailed view
        table = Table(
            title="Available Examples",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Complexity", justify="center")
        
        for name, data in EXAMPLES_DATA.items():
            complexity_style = "green" if data["complexity"] == "low" else "yellow"
            table.add_row(
                name,
                data["description"],
                f"[{complexity_style}]{data['complexity']}[/{complexity_style}]",
            )
        
        console.print(table)
    else:
        # Simple list view
        console.print("[bold]Available examples:[/bold]")
        for name in EXAMPLES_DATA:
            console.print(f"  • [cyan]{name}[/cyan]")
        console.print("\n[dim]Use --verbose for more details.[/dim]")


@examples_app.command("show")
def examples_show(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the example to show.",
        ),
    ],
    raw: Annotated[
        bool,
        typer.Option(
            "--raw",
            "-r",
            help="Output raw content without formatting (useful for piping).",
        ),
    ] = False,
) -> None:
    """
    Show the content of a specific example.
    
    Use --raw to get the content without decoration (for piping to files).
    """
    if name not in EXAMPLES_DATA:
        available = ", ".join(EXAMPLES_DATA.keys())
        err_console.print(
            Panel(
                f"[bold red]Error:[/bold red] Example [cyan]{name}[/cyan] not found.\n\n"
                f"Available examples: [yellow]{available}[/yellow]",
                title="Example Not Found",
                border_style="red",
            )
        )
        raise typer.Exit(code=ExitCode.USAGE_ERROR)
    
    example = EXAMPLES_DATA[name]
    
    if raw:
        # Raw output - no formatting, just the content
        # Use print() directly to avoid Rich formatting
        print(example["content"])
    else:
        # Formatted output with Rich
        console.print(
            Panel(
                f"[bold]{example['description']}[/bold]\n"
                f"Complexity: [yellow]{example['complexity']}[/yellow]",
                title=f"Example: {name}",
                border_style="blue",
            )
        )
        console.print("\n[bold]Content:[/bold]")
        # Use Rich's syntax highlighting for JSON
        from rich.syntax import Syntax
        syntax = Syntax(example["content"], "json", theme="monokai", line_numbers=True)
        console.print(syntax)


# =============================================================================
# Alternative: Adding callback to sub-app (optional)
# =============================================================================

@examples_app.callback()
def examples_callback() -> None:
    """
    Example configurations and templates.
    
    Browse and explore pre-built configuration examples.
    """
    # This docstring becomes the help text for the "examples" command group
    pass


# =============================================================================
# Entry Point
# =============================================================================

def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
