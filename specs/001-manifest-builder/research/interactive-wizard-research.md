# Interactive Wizard Research: Typer/Rich with Ctrl+C Handling

## Table of Contents
1. [Library Comparison & Recommendation](#1-library-comparison--recommendation)
2. [Complete Multi-Step Wizard Example](#2-complete-multi-step-wizard-example)
3. [SIGINT Handler Pattern for Saving Draft](#3-sigint-handler-pattern-for-saving-draft)
4. [TTY Detection Pattern](#4-tty-detection-pattern)
5. [YAML Preview with Rich](#5-yaml-preview-with-rich)
6. [Best Practices Summary](#6-best-practices-summary)

---

## 1. Library Comparison & Recommendation

### Available Libraries for Interactive Prompts

| Library | Pros | Cons | Best For |
|---------|------|------|----------|
| **Rich Prompt** | Built-in with Rich, beautiful styling, simple API, integrates with console theming | Limited prompt types (text, int, float, confirm), no arrow-key selection | Simple text/confirm prompts |
| **typer.prompt()** | Zero dependencies (uses Click), consistent with Typer ecosystem | Basic, no advanced features, limited styling | Simple interactive commands |
| **questionary** | Beautiful UI, arrow-key navigation, 2k+ stars, actively maintained, Rasa-backed | Extra dependency, no Rich integration | Feature-rich standalone apps |
| **InquirerPy** | Most feature-rich, fuzzy search, filepath completion, excellent validation, skip/interrupt handling | Extra dependency, slightly heavier | Complex wizards with advanced needs |

### Recommendation: **Rich Prompt + questionary** (Hybrid Approach)

For the dot-organize wizard, I recommend:

1. **Primary: `rich.prompt`** for simple confirmations and text input
   - Already a dependency (via Typer)
   - Consistent styling with rest of CLI
   - Simple `Prompt.ask()` and `Confirm.ask()` patterns

2. **Fallback consideration: `questionary`** if you need:
   - Arrow-key selection from lists
   - Autocomplete/fuzzy search
   - Multi-select checkboxes

**Reasoning:**
- Rich is already in the dependency tree (Typer uses it)
- questionary has excellent UX for selection prompts
- Both handle KeyboardInterrupt gracefully
- Minimal additional dependencies

### Hybrid Pattern Example

```python
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.console import Console
import questionary  # Only if selection prompts needed

console = Console()

# Simple text prompt with Rich
name = Prompt.ask("Enter frame name", default="frame-01")

# Integer with validation
count = IntPrompt.ask("Enter count", default=1)

# Confirmation
if Confirm.ask("Proceed with creation?"):
    ...

# Selection (if needed - use questionary)
choice = questionary.select(
    "Select file type:",
    choices=["photo", "video", "document", "other"]
).ask()
```

---

## 2. Complete Multi-Step Wizard Example

### Full Implementation with Validation, Navigation, and Draft Saving

```python
#!/usr/bin/env python3
"""
Multi-step interactive wizard with:
- Step-by-step prompts
- Input validation
- Ctrl+C graceful handling (saves draft)
- YAML preview before save
- Overwrite confirmation
"""

from __future__ import annotations

import signal
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.syntax import Syntax
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class Frame:
    """A single frame in the manifest."""
    name: str
    description: str = ""
    extensions: list[str] = field(default_factory=list)
    target_path: str = ""


@dataclass
class WizardState:
    """Holds the current state of the wizard for draft saving."""
    frames: list[Frame] = field(default_factory=list)
    current_step: str = "start"
    is_complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for YAML serialization."""
        return {
            "frames": [
                {
                    "name": f.name,
                    "description": f.description,
                    "extensions": f.extensions,
                    "target_path": f.target_path,
                }
                for f in self.frames
            ],
            "wizard_meta": {
                "current_step": self.current_step,
                "is_complete": self.is_complete,
            }
        }

    def has_meaningful_data(self) -> bool:
        """Check if there's enough data worth saving as draft."""
        return len(self.frames) > 0


# =============================================================================
# Wizard State (Global for signal handler access)
# =============================================================================

_wizard_state: WizardState | None = None
DRAFT_FILE = Path(".dot-draft.yaml")


def save_draft() -> bool:
    """
    Save current wizard state to draft file.
    Returns True if draft was saved, False otherwise.
    """
    global _wizard_state

    if _wizard_state is None:
        return False

    if not _wizard_state.has_meaningful_data():
        return False

    try:
        draft_content = yaml.dump(
            _wizard_state.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        DRAFT_FILE.write_text(draft_content)
        return True
    except Exception as e:
        err_console.print(f"[yellow]Warning:[/yellow] Could not save draft: {e}")
        return False


# =============================================================================
# SIGINT Handler (Ctrl+C)
# =============================================================================

def sigint_handler(signum: int, frame: Any) -> None:
    """
    Handle Ctrl+C gracefully:
    - Save draft if meaningful data exists
    - Print helpful message
    - Exit cleanly
    """
    console.print()  # Newline after ^C

    if save_draft():
        console.print(
            Panel(
                f"[yellow]Wizard interrupted.[/yellow]\n\n"
                f"Your progress has been saved to [cyan]{DRAFT_FILE}[/cyan]\n"
                f"Resume with: [bold]dot init --resume[/bold]",
                title="Draft Saved",
                border_style="yellow",
            )
        )
    else:
        console.print("[dim]Wizard cancelled.[/dim]")

    sys.exit(130)  # 128 + SIGINT(2) - standard Unix convention


def setup_signal_handlers() -> None:
    """Install signal handlers for graceful interruption."""
    signal.signal(signal.SIGINT, sigint_handler)
    # Optionally handle SIGTERM too
    signal.signal(signal.SIGTERM, sigint_handler)


# =============================================================================
# Validation Functions
# =============================================================================

def validate_frame_name(name: str) -> tuple[bool, str]:
    """
    Validate frame name.
    Returns (is_valid, error_message).
    """
    if not name:
        return False, "Frame name cannot be empty"

    if not name.replace("-", "").replace("_", "").isalnum():
        return False, "Frame name must be alphanumeric (dashes and underscores allowed)"

    if len(name) > 50:
        return False, "Frame name must be 50 characters or less"

    return True, ""


def validate_extensions(ext_input: str) -> tuple[bool, list[str], str]:
    """
    Validate and parse extension input.
    Returns (is_valid, parsed_extensions, error_message).
    """
    if not ext_input.strip():
        return False, [], "At least one extension is required"

    # Parse comma or space-separated extensions
    raw_exts = ext_input.replace(",", " ").split()
    extensions = []

    for ext in raw_exts:
        # Normalize: ensure leading dot
        ext = ext.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        # Validate extension format
        if not ext[1:].isalnum():
            return False, [], f"Invalid extension: {ext}"

        extensions.append(ext)

    return True, extensions, ""


def validate_path(path_str: str) -> tuple[bool, str]:
    """
    Validate target path format.
    Returns (is_valid, error_message).
    """
    if not path_str:
        return False, "Target path cannot be empty"

    # Check for invalid characters
    invalid_chars = ['<', '>', '|', '\0']
    if any(c in path_str for c in invalid_chars):
        return False, f"Path contains invalid characters"

    return True, ""


# =============================================================================
# Prompt Functions with Validation Loop
# =============================================================================

def prompt_with_validation(
    message: str,
    validator: callable,
    default: str = "",
    show_default: bool = True,
) -> str:
    """
    Prompt for input with validation loop.
    Keeps asking until valid input is provided.
    """
    while True:
        value = Prompt.ask(
            message,
            default=default if default else None,
            show_default=show_default,
        )

        is_valid, error = validator(value)

        if is_valid:
            return value

        err_console.print(f"[red]✗[/red] {error}")


def prompt_extensions() -> list[str]:
    """Prompt for extensions with validation."""
    while True:
        ext_input = Prompt.ask(
            "File extensions [dim](comma or space separated, e.g., jpg png gif)[/dim]"
        )

        is_valid, extensions, error = validate_extensions(ext_input)

        if is_valid:
            return extensions

        err_console.print(f"[red]✗[/red] {error}")


# =============================================================================
# Wizard Steps
# =============================================================================

def wizard_intro() -> None:
    """Display wizard introduction."""
    console.print()
    console.print(
        Panel(
            "[bold]Welcome to the dot-organize manifest builder![/bold]\n\n"
            "This wizard will help you create a [cyan].dot-organize.yaml[/cyan] manifest.\n\n"
            "[dim]• Press Enter to accept defaults (shown in brackets)\n"
            "• Press Ctrl+C at any time to save progress and exit[/dim]",
            title="🧙 Manifest Builder Wizard",
            border_style="blue",
        )
    )
    console.print()


def wizard_add_frame(state: WizardState, frame_number: int) -> Frame | None:
    """
    Interactive prompts for adding a single frame.
    Returns the Frame or None if user wants to stop adding.
    """
    state.current_step = f"frame-{frame_number}"

    console.print(f"\n[bold blue]━━━ Frame {frame_number} ━━━[/bold blue]\n")

    # Frame name
    name = prompt_with_validation(
        "[bold]Frame name[/bold]",
        validate_frame_name,
        default=f"frame-{frame_number:02d}",
    )

    # Description (optional)
    description = Prompt.ask(
        "[bold]Description[/bold] [dim](optional)[/dim]",
        default="",
        show_default=False,
    )

    # Extensions
    extensions = prompt_extensions()

    # Target path
    target_path = prompt_with_validation(
        "[bold]Target path[/bold] [dim](e.g., ~/Photos/{{year}}/{{month}})[/dim]",
        validate_path,
        default=f"~/Organized/{name}",
    )

    frame = Frame(
        name=name,
        description=description,
        extensions=extensions,
        target_path=target_path,
    )

    # Show frame summary
    console.print()
    display_frame_summary(frame)

    return frame


def display_frame_summary(frame: Frame) -> None:
    """Display a summary of the entered frame."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Name", f"[cyan]{frame.name}[/cyan]")
    table.add_row("Description", frame.description or "[dim]—[/dim]")
    table.add_row("Extensions", ", ".join(frame.extensions))
    table.add_row("Target", frame.target_path)

    console.print(Panel(table, title="Frame Added", border_style="green"))


def wizard_preview(state: WizardState) -> bool:
    """
    Show YAML preview and ask for confirmation.
    Returns True if user confirms, False to go back.
    """
    console.print("\n[bold blue]━━━ Preview ━━━[/bold blue]\n")

    # Generate manifest dict (without wizard_meta)
    manifest = {
        "version": "1.0",
        "frames": [
            {
                "name": f.name,
                "description": f.description,
                "extensions": f.extensions,
                "target": f.target_path,
            }
            for f in state.frames
        ]
    }

    # Generate YAML
    yaml_content = yaml.dump(
        manifest,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    # Display with syntax highlighting
    syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=".dot-organize.yaml", border_style="blue"))

    return Confirm.ask("\n[bold]Save this manifest?[/bold]", default=True)


def check_overwrite(output_path: Path) -> bool:
    """
    Check if file exists and prompt for overwrite confirmation.
    Returns True if OK to write, False to cancel.
    """
    if not output_path.exists():
        return True

    console.print(
        f"\n[yellow]⚠[/yellow]  File [cyan]{output_path}[/cyan] already exists."
    )
    return Confirm.ask("Overwrite?", default=False)


# =============================================================================
# Main Wizard Flow
# =============================================================================

def run_wizard(output_path: Path = Path(".dot-organize.yaml")) -> bool:
    """
    Run the complete wizard flow.
    Returns True if manifest was saved, False otherwise.
    """
    global _wizard_state

    # Initialize state and signal handlers
    _wizard_state = WizardState()
    setup_signal_handlers()

    try:
        # Intro
        wizard_intro()

        # Frame collection loop
        frame_number = 1
        while True:
            frame = wizard_add_frame(_wizard_state, frame_number)
            _wizard_state.frames.append(frame)

            # Ask if user wants to add more
            console.print()
            if not Confirm.ask("Add another frame?", default=True):
                break

            frame_number += 1

        # Preview
        if not wizard_preview(_wizard_state):
            console.print("[dim]Manifest not saved.[/dim]")
            return False

        # Check overwrite
        if not check_overwrite(output_path):
            console.print("[dim]Cancelled.[/dim]")
            return False

        # Generate final manifest
        manifest = {
            "version": "1.0",
            "frames": [
                {
                    "name": f.name,
                    "description": f.description,
                    "extensions": f.extensions,
                    "target": f.target_path,
                }
                for f in _wizard_state.frames
            ]
        }

        # Save
        yaml_content = yaml.dump(
            manifest,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        output_path.write_text(yaml_content)

        _wizard_state.is_complete = True

        console.print(
            Panel(
                f"[bold green]✓[/bold green] Manifest saved to [cyan]{output_path}[/cyan]",
                title="Success",
                border_style="green",
            )
        )

        # Clean up draft if it exists
        if DRAFT_FILE.exists():
            DRAFT_FILE.unlink()

        return True

    except KeyboardInterrupt:
        # This shouldn't normally be reached due to signal handler,
        # but acts as a fallback
        sigint_handler(signal.SIGINT, None)
        return False


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    success = run_wizard()
    sys.exit(0 if success else 1)
```

---

## 3. SIGINT Handler Pattern for Saving Draft

### Key Components

#### 1. Global State Access

The signal handler needs access to wizard state, so use a module-level variable:

```python
_wizard_state: WizardState | None = None

def sigint_handler(signum: int, frame: Any) -> None:
    """Handle Ctrl+C - save draft and exit."""
    global _wizard_state
    # ... save logic
```

#### 2. Signal Registration

```python
import signal

def setup_signal_handlers() -> None:
    """Install signal handlers."""
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)  # Also handle kill
```

#### 3. Conditional Draft Saving

Only save if there's meaningful data:

```python
def save_draft() -> bool:
    """Save only if at least one frame was entered."""
    if _wizard_state is None:
        return False

    if not _wizard_state.has_meaningful_data():
        return False

    # Save to .dot-draft.yaml
    DRAFT_FILE.write_text(yaml.dump(_wizard_state.to_dict()))
    return True
```

#### 4. Exit Code Convention

Use `130` (128 + SIGINT signal number 2) for Ctrl+C exits:

```python
sys.exit(130)  # Standard Unix convention for SIGINT
```

### Alternative: Context Manager Pattern

For cleaner resource management:

```python
from contextlib import contextmanager

@contextmanager
def wizard_session():
    """Context manager that ensures draft is saved on interruption."""
    state = WizardState()
    original_handler = signal.getsignal(signal.SIGINT)

    def handler(sig, frame):
        if state.has_meaningful_data():
            save_draft(state)
            console.print(f"[yellow]Draft saved to {DRAFT_FILE}[/yellow]")
        sys.exit(130)

    signal.signal(signal.SIGINT, handler)

    try:
        yield state
    finally:
        signal.signal(signal.SIGINT, original_handler)
        # Clean up draft on success
        if state.is_complete and DRAFT_FILE.exists():
            DRAFT_FILE.unlink()


# Usage
def run_wizard():
    with wizard_session() as state:
        # ... wizard logic
        state.is_complete = True
```

### Alternative: atexit for Fallback

```python
import atexit

def _emergency_save():
    """Last-resort save on any exit."""
    if _wizard_state and _wizard_state.has_meaningful_data():
        save_draft()

atexit.register(_emergency_save)
```

---

## 4. TTY Detection Pattern

### Why TTY Detection Matters

Interactive prompts require a terminal. When stdin is piped (e.g., from a script), prompts will fail or behave unexpectedly.

### Detection Methods

#### Method 1: `sys.stdin.isatty()` (Recommended)

```python
import sys

def require_tty() -> None:
    """Exit with error if not running in interactive terminal."""
    if not sys.stdin.isatty():
        err_console.print(
            Panel(
                "[bold red]Error:[/bold red] This command requires an interactive terminal.\n\n"
                "The wizard cannot run when stdin is piped or redirected.\n"
                "Please run this command directly in a terminal.",
                title="Non-Interactive Mode Detected",
                border_style="red",
            )
        )
        raise typer.Exit(code=2)
```

#### Method 2: Rich Console Detection

Rich's Console has built-in TTY detection:

```python
from rich.console import Console

console = Console()

if not console.is_terminal:
    # Not a TTY - disable interactive features
    err_console.print("[red]Error: Interactive terminal required[/red]")
    raise typer.Exit(2)
```

#### Method 3: Full Check (stdin + stdout)

```python
def is_interactive() -> bool:
    """Check if both stdin and stdout are TTYs."""
    return sys.stdin.isatty() and sys.stdout.isatty()

def require_interactive_mode() -> None:
    """Require interactive mode or exit with helpful message."""
    if not sys.stdin.isatty():
        err_console.print(
            "[red]Error:[/red] Cannot read input - stdin is not a terminal.\n"
            "Hint: Don't pipe input to this command."
        )
        raise typer.Exit(2)

    if not sys.stdout.isatty():
        err_console.print(
            "[red]Error:[/red] Cannot display prompts - stdout is not a terminal.\n"
            "Hint: Don't redirect output from this command."
        )
        raise typer.Exit(2)
```

### Integration with Typer Command

```python
@app.command()
def init(
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "-y", help="Skip prompts, use defaults"),
    ] = False,
) -> None:
    """Initialize a new manifest with interactive wizard."""

    if non_interactive:
        # Non-interactive mode - use defaults or config file
        create_default_manifest()
        return

    # Interactive mode - require TTY
    require_tty()

    # Now safe to run wizard
    run_wizard()
```

### Environment Variable Check

Some CI environments set specific variables:

```python
import os

def is_ci_environment() -> bool:
    """Detect if running in CI/CD environment."""
    ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL", "TRAVIS"]
    return any(os.environ.get(var) for var in ci_vars)

def require_interactive() -> None:
    if is_ci_environment():
        err_console.print("[red]Error:[/red] Interactive wizard cannot run in CI.")
        err_console.print("Use [bold]--non-interactive[/bold] flag or provide config file.")
        raise typer.Exit(2)

    if not sys.stdin.isatty():
        # ... TTY error
```

---

## 5. YAML Preview with Rich

### Basic Syntax Highlighting

```python
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
import yaml

console = Console()

def preview_yaml(data: dict, title: str = "Preview") -> None:
    """Display YAML with syntax highlighting."""
    yaml_content = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        indent=2,
    )

    syntax = Syntax(
        yaml_content,
        "yaml",
        theme="monokai",
        line_numbers=True,
        word_wrap=True,
    )

    console.print(Panel(syntax, title=title, border_style="blue"))
```

### Available Themes

| Theme | Style |
|-------|-------|
| `monokai` | Dark, colorful (default) |
| `dracula` | Dark purple tones |
| `github-dark` | GitHub dark mode |
| `one-dark` | Atom One Dark |
| `nord` | Arctic color palette |
| `material` | Material Design |

### Customizing YAML Output

```python
# For cleaner YAML output
yaml_content = yaml.dump(
    data,
    default_flow_style=False,  # Block style, not inline
    sort_keys=False,           # Preserve key order
    allow_unicode=True,        # Allow non-ASCII characters
    indent=2,                  # Indentation
    width=80,                  # Line width for wrapping
)
```

### Side-by-Side Preview (Before/After)

```python
from rich.columns import Columns

def preview_diff(before: dict, after: dict) -> None:
    """Show before/after YAML preview."""
    before_yaml = yaml.dump(before, default_flow_style=False)
    after_yaml = yaml.dump(after, default_flow_style=False)

    before_panel = Panel(
        Syntax(before_yaml, "yaml", theme="monokai"),
        title="[red]Before[/red]",
        border_style="red",
    )

    after_panel = Panel(
        Syntax(after_yaml, "yaml", theme="monokai"),
        title="[green]After[/green]",
        border_style="green",
    )

    console.print(Columns([before_panel, after_panel]))
```

---

## 6. Best Practices Summary

### UX Best Practices for CLI Wizards

| Practice | Implementation |
|----------|---------------|
| **Show defaults** | `Prompt.ask("Name", default="value")` - always show what Enter will do |
| **Validate inline** | Validate immediately, show error, re-prompt |
| **Progressive disclosure** | Ask simple questions first, complex ones later |
| **Allow escape** | Ctrl+C should always work; save progress |
| **Confirm destructive actions** | Always confirm before overwriting |
| **Show progress** | "Step 2 of 5" or visual progress indicators |
| **Preview before commit** | Show exactly what will be written |
| **Helpful error messages** | Explain what went wrong AND how to fix it |

### Validation Pattern

```python
def prompt_with_retry(
    message: str,
    validator: Callable[[str], tuple[bool, str]],
    max_attempts: int = 3,
) -> str | None:
    """Prompt with validation and retry limit."""
    for attempt in range(max_attempts):
        value = Prompt.ask(message)
        is_valid, error = validator(value)

        if is_valid:
            return value

        remaining = max_attempts - attempt - 1
        if remaining > 0:
            console.print(f"[red]✗[/red] {error} ({remaining} attempts remaining)")
        else:
            console.print(f"[red]✗[/red] {error}")

    return None  # Max attempts reached
```

### Graceful Degradation

```python
def get_input_or_default(
    message: str,
    default: str,
    timeout_seconds: int = 30,
) -> str:
    """
    Get input with timeout fallback to default.
    Useful for automated environments.
    """
    if not sys.stdin.isatty():
        console.print(f"[dim]Using default: {default}[/dim]")
        return default

    return Prompt.ask(message, default=default)
```

### Draft Resume Pattern

```python
def load_draft() -> WizardState | None:
    """Load previous draft if it exists."""
    if not DRAFT_FILE.exists():
        return None

    try:
        data = yaml.safe_load(DRAFT_FILE.read_text())
        state = WizardState()

        for frame_data in data.get("frames", []):
            state.frames.append(Frame(**frame_data))

        return state
    except Exception:
        return None


def run_wizard(resume: bool = False) -> bool:
    """Run wizard, optionally resuming from draft."""
    if resume:
        state = load_draft()
        if state:
            console.print(f"[green]✓[/green] Resuming from {DRAFT_FILE}")
        else:
            console.print("[yellow]No draft found, starting fresh[/yellow]")
            state = WizardState()
    else:
        state = WizardState()

    # ... continue wizard
```

---

## Appendix: Quick Reference

### Import Cheatsheet

```python
# Rich prompts
from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Signal handling
import signal
import sys
import atexit

# YAML
import yaml
```

### Signal Numbers Reference

| Signal | Number | Trigger |
|--------|--------|---------|
| SIGINT | 2 | Ctrl+C |
| SIGTERM | 15 | `kill` command |
| SIGQUIT | 3 | Ctrl+\ |
| SIGHUP | 1 | Terminal closed |

### Exit Code Reference

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Usage/command error |
| 130 | Ctrl+C (128 + 2) |
| 143 | SIGTERM (128 + 15) |
