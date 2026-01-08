#!/usr/bin/env python3
"""
Interactive Wizard Example - Complete Working Demo

Demonstrates:
1. Multi-step prompts with validation
2. SIGINT (Ctrl+C) handling with draft save
3. TTY detection for non-interactive mode error
4. YAML preview with Rich syntax highlighting
5. Overwrite confirmation

Run:
    python interactive-wizard-example.py

Test Ctrl+C:
    Start the wizard, add at least one frame, then press Ctrl+C
    Check for .dot-draft.yaml being created
"""

from __future__ import annotations

import signal
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

# =============================================================================
# Console Setup
# =============================================================================

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
    """Holds the current wizard state for draft saving."""

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
            },
        }

    def has_meaningful_data(self) -> bool:
        """Check if there's enough data worth saving as draft."""
        return len(self.frames) > 0


# =============================================================================
# Global State (for signal handler access)
# =============================================================================

_wizard_state: WizardState | None = None
DRAFT_FILE = Path(".dot-draft.yaml")
OUTPUT_FILE = Path(".dot-organize.yaml")


# =============================================================================
# TTY Detection
# =============================================================================


def require_tty() -> None:
    """Exit with error if not running in interactive terminal."""
    if not sys.stdin.isatty():
        err_console.print(
            Panel(
                "[bold red]Error:[/bold red] This command requires an interactive terminal.\n\n"
                "The wizard cannot run when stdin is piped or redirected.\n"
                "Please run this command directly in a terminal.\n\n"
                "[dim]Hint: Use --non-interactive flag for scripted usage.[/dim]",
                title="Non-Interactive Mode Detected",
                border_style="red",
            )
        )
        sys.exit(2)


# =============================================================================
# Draft Save/Load
# =============================================================================


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


def load_draft() -> WizardState | None:
    """Load previous draft if it exists."""
    if not DRAFT_FILE.exists():
        return None

    try:
        data = yaml.safe_load(DRAFT_FILE.read_text())
        state = WizardState()

        for frame_data in data.get("frames", []):
            state.frames.append(
                Frame(
                    name=frame_data.get("name", ""),
                    description=frame_data.get("description", ""),
                    extensions=frame_data.get("extensions", []),
                    target_path=frame_data.get("target_path", ""),
                )
            )

        state.current_step = data.get("wizard_meta", {}).get("current_step", "start")
        return state
    except Exception as e:
        err_console.print(f"[yellow]Warning:[/yellow] Could not load draft: {e}")
        return None


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
                f"Resume with: [bold]python {sys.argv[0]} --resume[/bold]",
                title="Draft Saved",
                border_style="yellow",
            )
        )
    else:
        console.print("[dim]Wizard cancelled (no data to save).[/dim]")

    sys.exit(130)  # 128 + SIGINT(2) - standard Unix convention


def setup_signal_handlers() -> None:
    """Install signal handlers for graceful interruption."""
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)


# =============================================================================
# Validation Functions
# =============================================================================


def validate_frame_name(name: str) -> tuple[bool, str]:
    """Validate frame name. Returns (is_valid, error_message)."""
    if not name:
        return False, "Frame name cannot be empty"

    if not name.replace("-", "").replace("_", "").isalnum():
        return False, "Frame name must be alphanumeric (dashes and underscores allowed)"

    if len(name) > 50:
        return False, "Frame name must be 50 characters or less"

    return True, ""


def validate_extensions(ext_input: str) -> tuple[bool, list[str], str]:
    """Validate and parse extension input. Returns (is_valid, extensions, error)."""
    if not ext_input.strip():
        return False, [], "At least one extension is required"

    # Parse comma or space-separated extensions
    raw_exts = ext_input.replace(",", " ").split()
    extensions = []

    for ext in raw_exts:
        ext = ext.strip().lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        # Validate extension format
        if len(ext) < 2 or not ext[1:].replace("_", "").isalnum():
            return False, [], f"Invalid extension: {ext}"

        extensions.append(ext)

    return True, extensions, ""


def validate_path(path_str: str) -> tuple[bool, str]:
    """Validate target path format. Returns (is_valid, error_message)."""
    if not path_str:
        return False, "Target path cannot be empty"

    invalid_chars = ["<", ">", "|", "\0"]
    if any(c in path_str for c in invalid_chars):
        return False, "Path contains invalid characters"

    return True, ""


# =============================================================================
# Prompt Helpers
# =============================================================================


def prompt_with_validation(
    message: str,
    validator: Callable[[str], tuple[bool, str]],
    default: str = "",
) -> str:
    """Prompt for input with validation loop."""
    while True:
        value = Prompt.ask(
            message,
            default=default if default else None,
        )

        is_valid, error = validator(value)

        if is_valid:
            return value

        err_console.print(f"[red]✗[/red] {error}")


def prompt_extensions() -> list[str]:
    """Prompt for extensions with validation."""
    while True:
        ext_input = Prompt.ask(
            "File extensions [dim](comma/space separated, e.g., jpg png gif)[/dim]"
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


def display_frame_summary(frame: Frame) -> None:
    """Display a summary of the entered frame."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("Name", f"[cyan]{frame.name}[/cyan]")
    table.add_row("Description", frame.description or "[dim]—[/dim]")
    table.add_row("Extensions", ", ".join(frame.extensions))
    table.add_row("Target", frame.target_path)

    console.print(Panel(table, title="✓ Frame Added", border_style="green"))


def wizard_add_frame(state: WizardState, frame_number: int) -> Frame:
    """Interactive prompts for adding a single frame."""
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


def generate_manifest(state: WizardState) -> dict[str, Any]:
    """Generate the final manifest dictionary."""
    return {
        "version": "1.0",
        "frames": [
            {
                "name": f.name,
                "description": f.description,
                "extensions": f.extensions,
                "target": f.target_path,
            }
            for f in state.frames
        ],
    }


def wizard_preview(state: WizardState) -> bool:
    """Show YAML preview and ask for confirmation."""
    console.print("\n[bold blue]━━━ Preview ━━━[/bold blue]\n")

    manifest = generate_manifest(state)

    # Generate YAML
    yaml_content = yaml.dump(
        manifest,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    # Display with syntax highlighting
    syntax = Syntax(yaml_content, "yaml", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=str(OUTPUT_FILE), border_style="blue"))

    return Confirm.ask("\n[bold]Save this manifest?[/bold]", default=True)


def check_overwrite(output_path: Path) -> bool:
    """Check if file exists and prompt for overwrite confirmation."""
    if not output_path.exists():
        return True

    console.print(f"\n[yellow]⚠[/yellow]  File [cyan]{output_path}[/cyan] already exists.")
    return Confirm.ask("Overwrite?", default=False)


def show_resume_summary(state: WizardState) -> None:
    """Show summary of resumed draft."""
    console.print(
        Panel(
            f"[green]✓[/green] Resuming from draft with {len(state.frames)} frame(s):\n\n"
            + "\n".join(f"  • [cyan]{f.name}[/cyan]" for f in state.frames),
            title="Draft Loaded",
            border_style="green",
        )
    )


# =============================================================================
# Main Wizard Flow
# =============================================================================


def run_wizard(resume: bool = False) -> bool:
    """
    Run the complete wizard flow.
    Returns True if manifest was saved, False otherwise.
    """
    global _wizard_state

    # TTY check
    require_tty()

    # Setup signal handlers
    setup_signal_handlers()

    # Initialize or resume state
    if resume:
        loaded = load_draft()
        if loaded:
            _wizard_state = loaded
            show_resume_summary(_wizard_state)
        else:
            console.print("[yellow]No draft found, starting fresh.[/yellow]")
            _wizard_state = WizardState()
    else:
        _wizard_state = WizardState()

    try:
        # Intro (only if starting fresh)
        if len(_wizard_state.frames) == 0:
            wizard_intro()

        # Frame collection loop
        frame_number = len(_wizard_state.frames) + 1
        while True:
            frame = wizard_add_frame(_wizard_state, frame_number)
            _wizard_state.frames.append(frame)

            console.print()
            if not Confirm.ask("Add another frame?", default=True):
                break

            frame_number += 1

        # Preview
        if not wizard_preview(_wizard_state):
            console.print("[dim]Manifest not saved.[/dim]")
            return False

        # Check overwrite
        if not check_overwrite(OUTPUT_FILE):
            console.print("[dim]Cancelled.[/dim]")
            return False

        # Save manifest
        manifest = generate_manifest(_wizard_state)
        yaml_content = yaml.dump(
            manifest,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        OUTPUT_FILE.write_text(yaml_content)

        _wizard_state.is_complete = True

        console.print(
            Panel(
                f"[bold green]✓[/bold green] Manifest saved to [cyan]{OUTPUT_FILE}[/cyan]",
                title="Success",
                border_style="green",
            )
        )

        # Clean up draft
        if DRAFT_FILE.exists():
            DRAFT_FILE.unlink()
            console.print(f"[dim]Cleaned up draft file: {DRAFT_FILE}[/dim]")

        return True

    except KeyboardInterrupt:
        # Fallback - shouldn't normally reach here
        sigint_handler(signal.SIGINT, None)
        return False


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Entry point with argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive manifest builder wizard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python interactive-wizard-example.py           # Start fresh
  python interactive-wizard-example.py --resume  # Resume from draft

Keyboard:
  Enter    Accept default value
  Ctrl+C   Save draft and exit
        """,
    )
    parser.add_argument(
        "--resume",
        "-r",
        action="store_true",
        help="Resume from previously saved draft",
    )

    args = parser.parse_args()

    success = run_wizard(resume=args.resume)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
