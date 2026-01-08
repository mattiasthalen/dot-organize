# Typer CLI Research: Subcommands, Rich Output, and Exit Codes

## Table of Contents
1. [Structuring Typer App with Nested Subcommands](#1-structuring-typer-app-with-nested-subcommands)
2. [Integrating Rich Console with Typer](#2-integrating-rich-console-with-typer)
3. [Implementing --no-color Flag](#3-implementing---no-color-flag)
4. [Setting Exit Codes in Typer Commands](#4-setting-exit-codes-in-typer-commands)
5. [Handling File-Not-Found Errors](#5-handling-file-not-found-errors)
6. [Best Practices Summary](#6-best-practices-summary)

---

## 1. Structuring Typer App with Nested Subcommands

### The `app.add_typer()` Pattern

Typer supports nested subcommands through the `add_typer()` method. Each `typer.Typer()` instance can act as both a standalone CLI and a subcommand group.

```python
import typer

# Main application
app = typer.Typer()

# Sub-application for nested commands
examples_app = typer.Typer()

# Register sub-app with the main app
# This creates: myapp examples <subcommand>
app.add_typer(examples_app, name="examples")

@app.command()
def validate():
    """A top-level command."""
    pass

@examples_app.command("list")
def examples_list():
    """Nested: myapp examples list"""
    pass

@examples_app.command("show")
def examples_show(name: str):
    """Nested: myapp examples show <name>"""
    pass
```

### Key Points

| Feature | Implementation |
|---------|---------------|
| Create sub-app | `sub_app = typer.Typer()` |
| Register it | `app.add_typer(sub_app, name="subcommand")` |
| Add commands | `@sub_app.command()` decorator |
| Depth | Unlimited nesting possible |

### Sub-App Callbacks

You can add a callback to the sub-app for shared options or documentation:

```python
@examples_app.callback()
def examples_callback():
    """
    Help text for the 'examples' command group.

    This docstring appears in: myapp examples --help
    """
    pass
```

---

## 2. Integrating Rich Console with Typer

### Basic Integration

Rich works seamlessly with Typer. Create a `Console` instance and use it throughout your app:

```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
err_console = Console(stderr=True)

@app.command()
def my_command():
    # Rich markup in strings
    console.print("[bold green]Success![/bold green]")

    # Rich objects (Tables, Panels, etc.)
    table = Table(title="Results")
    table.add_column("Name")
    table.add_column("Status")
    table.add_row("Item 1", "[green]OK[/green]")
    console.print(table)

    # Error output to stderr
    err_console.print("[bold red]Error:[/bold red] Something went wrong")
```

### Module-Level Console Pattern

For consistent console access across modules:

```python
# console.py
from rich.console import Console

console = Console()
err_console = Console(stderr=True)

# In other files:
from myapp.console import console, err_console
```

### Rich Features Commonly Used with CLIs

| Feature | Use Case |
|---------|----------|
| `Panel` | Boxed messages (errors, success) |
| `Table` | Tabular data display |
| `Syntax` | Code/JSON highlighting |
| `Progress` | Progress bars for long operations |
| `console.status()` | Spinner for async operations |

---

## 3. Implementing --no-color Flag

### Approach 1: Global Console Configuration (Recommended)

Use Typer's callback with `is_eager=True` to process `--no-color` before other options:

```python
from rich.console import Console
import typer

# Global consoles - will be reconfigured
console = Console()
err_console = Console(stderr=True)

def configure_console(no_color: bool) -> None:
    """Configure Rich consoles based on --no-color flag."""
    global console, err_console

    if no_color:
        # color_system=None disables ALL ANSI codes
        console = Console(color_system=None, force_terminal=False)
        err_console = Console(stderr=True, color_system=None, force_terminal=False)
    else:
        console = Console()
        err_console = Console(stderr=True)

app = typer.Typer()

@app.callback()
def main(
    ctx: typer.Context,
    no_color: Annotated[bool, typer.Option(
        "--no-color",
        help="Disable colored output.",
        is_eager=True,  # Process before other options
    )] = False,
):
    if ctx.resilient_parsing:
        return  # Skip during shell completion
    configure_console(no_color)
```

### Rich Console Color System Options

| `color_system` Value | Behavior |
|---------------------|----------|
| `None` | Disables color entirely (plain text) |
| `"auto"` | Auto-detect terminal capabilities |
| `"standard"` | 16 colors |
| `"256"` | 256 colors |
| `"truecolor"` | 16.7 million colors |

### Approach 2: Environment Variable (NO_COLOR Standard)

Rich respects the `NO_COLOR` environment variable automatically:

```bash
NO_COLOR=1 python myapp.py validate file.json
```

This is the [no-color.org](https://no-color.org/) standard. Rich will strip colors but preserve styles (bold, italic, etc.).

### Approach 3: Force Terminal Detection

```python
# force_terminal=True: Always output ANSI codes (even when piping)
# force_terminal=False: Never output ANSI codes
console = Console(force_terminal=False)
```

---

## 4. Setting Exit Codes in Typer Commands

### Using `typer.Exit(code=N)`

Raise `typer.Exit()` with a custom exit code:

```python
class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    USAGE_ERROR = 2

@app.command()
def validate(file_path: Path):
    if not file_path.exists():
        console.print("[red]File not found[/red]")
        raise typer.Exit(code=ExitCode.USAGE_ERROR)

    if not is_valid(file_path):
        console.print("[red]Validation failed[/red]")
        raise typer.Exit(code=ExitCode.VALIDATION_ERROR)

    console.print("[green]Valid![/green]")
    raise typer.Exit(code=ExitCode.SUCCESS)
```

### Key Behaviors

| Scenario | Approach |
|----------|----------|
| Success | `raise typer.Exit(code=0)` or just return |
| Validation error | `raise typer.Exit(code=1)` |
| Usage error | `raise typer.Exit(code=2)` |
| Abort with message | `raise typer.Abort()` (prints "Aborted!") |
| Bad parameter | `raise typer.BadParameter("message")` |

### Exit Code Conventions

Following Unix/POSIX conventions:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (validation, business logic) |
| 2 | Misuse of command (usage error, missing file) |
| 126 | Command cannot execute |
| 127 | Command not found |
| 128+ | Fatal signal (128 + signal number) |

---

## 5. Handling File-Not-Found Errors

### Custom Handling with Exit Code 2

```python
from pathlib import Path
from typing import Annotated

@app.command()
def validate(
    file_path: Annotated[Path, typer.Argument(
        exists=False,  # Don't use Typer's built-in check
    )],
):
    # Custom check with specific exit code
    if not file_path.exists():
        err_console.print(
            f"[bold red]Error:[/bold red] File not found: {file_path}"
        )
        raise typer.Exit(code=2)  # Usage error

    # Continue with validation...
```

### Using Typer's Built-in Path Validation

Typer can auto-validate paths, but uses its own error handling:

```python
@app.command()
def validate(
    file_path: Annotated[Path, typer.Argument(
        exists=True,  # Typer validates existence
        file_okay=True,
        dir_okay=False,
        readable=True,
    )],
):
    # file_path is guaranteed to exist here
    pass
```

**Downside**: Typer's built-in validation uses exit code 2, but you lose control over the error message format.

### Rich Error Display Pattern

```python
from rich.panel import Panel

def file_not_found_error(path: Path) -> None:
    """Display a styled file-not-found error."""
    err_console.print(
        Panel(
            f"[bold red]Error:[/bold red] File not found\n\n"
            f"Path: [cyan]{path}[/cyan]\n"
            f"CWD: [dim]{Path.cwd()}[/dim]",
            title="❌ File Not Found",
            border_style="red",
        )
    )
    raise typer.Exit(code=2)
```

---

## 6. Best Practices Summary

### Architecture

```
myapp/
├── __init__.py
├── __main__.py      # Entry point: from myapp.cli import app; app()
├── cli.py           # Main Typer app and top-level commands
├── console.py       # Rich console instances
├── commands/
│   ├── __init__.py
│   ├── validate.py  # validate command
│   ├── init.py      # init command
│   └── examples.py  # examples sub-app
└── core/
    ├── __init__.py
    └── validators.py
```

### Console Pattern

```python
# console.py
from rich.console import Console

_no_color = False
console: Console = Console()
err_console: Console = Console(stderr=True)

def set_no_color(value: bool) -> None:
    global console, err_console, _no_color
    _no_color = value
    if value:
        console = Console(color_system=None)
        err_console = Console(stderr=True, color_system=None)
```

### Exit Code Constants

```python
# exitcodes.py
class ExitCode:
    SUCCESS = 0
    VALIDATION_ERROR = 1
    USAGE_ERROR = 2
```

### Error Handling Pattern

```python
def safe_command(func):
    """Decorator for consistent error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            err_console.print(f"[red]File not found:[/red] {e}")
            raise typer.Exit(code=2)
        except ValidationError as e:
            err_console.print(f"[red]Validation error:[/red] {e}")
            raise typer.Exit(code=1)
    return wrapper
```

### Testing Commands

```python
from typer.testing import CliRunner

runner = CliRunner()

def test_validate_success():
    result = runner.invoke(app, ["validate", "valid.json"])
    assert result.exit_code == 0

def test_validate_file_not_found():
    result = runner.invoke(app, ["validate", "missing.json"])
    assert result.exit_code == 2

def test_no_color_flag():
    result = runner.invoke(app, ["--no-color", "validate", "file.json"])
    # Check no ANSI codes in output
    assert "\x1b[" not in result.output
```

---

## References

- [Typer Documentation](https://typer.tiangolo.com/)
- [Typer SubCommands](https://typer.tiangolo.com/tutorial/subcommands/add-typer/)
- [Typer Terminating](https://typer.tiangolo.com/tutorial/terminating/)
- [Rich Console API](https://rich.readthedocs.io/en/stable/console.html)
- [NO_COLOR Standard](https://no-color.org/)
