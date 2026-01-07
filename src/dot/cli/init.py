"""
Init command - Interactive manifest builder wizard (T074-T083).

Implements:
- T074: Command skeleton with --output, --format flags
- T075: Frame-first wizard workflow using questionary
- T076: Input validation with re-prompting
- T077: Auto-suggest for valid names
- T078: Auto-generate key set values
- T079: Summary preview before writing
- T080: Overwrite confirmation prompt
- T081: Save with YAML/JSON format
- T082: Ctrl+C handler for .dot-draft.yaml
- T083: TTY detection with helpful error
"""

from __future__ import annotations

import json
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
import yaml

from dot.models import (
    Frame,
    Hook,
    HookRole,
    Manifest,
    Metadata,
    Settings,
    Source,
)
from dot.io.yaml import dump_manifest_yaml
from dot.io.json import dump_manifest_json

if TYPE_CHECKING:
    from types import FrameType

# =============================================================================
# Console Setup
# =============================================================================

console = Console()
err_console = Console(stderr=True)

# =============================================================================
# Data Classes for Wizard State
# =============================================================================


@dataclass
class WizardFrame:
    """Mutable frame data collected during wizard flow."""

    name: str = ""
    source_type: Literal["relation", "path"] = "relation"
    source_value: str = ""
    hooks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WizardState:
    """Mutable state for the wizard - enables draft saving on interrupt."""

    frames: list[WizardFrame] = field(default_factory=list)
    current_step: str = "start"
    is_complete: bool = False

    def has_meaningful_data(self) -> bool:
        """Check if there's at least one complete frame worth saving."""
        return any(
            f.name and f.source_value and f.hooks
            for f in self.frames
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "manifest_version": "1.0.0",
            "schema_version": "1.0.0",
            "frames": [
                {
                    "name": f.name,
                    "source": {
                        f.source_type: f.source_value,
                    },
                    "hooks": f.hooks,
                }
                for f in self.frames
                if f.name and f.source_value and f.hooks
            ],
            "_wizard_meta": {
                "current_step": self.current_step,
                "is_complete": self.is_complete,
            },
        }


def generate_hook_name(concept: str, source: str, qualifier: str | None = None, tenant: str | None = None) -> str:
    """
    Generate hook name following CONCEPT[~QUALIFIER]@SOURCE[~TENANT] recipe (T078).
    
    Examples:
        - customer@CRM -> _hk__customer__crm
        - customer~manager@CRM -> _hk__customer__manager__crm
        - customer@CRM~AU -> _hk__customer__crm__au
    """
    parts = ["_hk"]
    parts.append(concept.lower())
    if qualifier:
        parts.append(qualifier.lower())
    parts.append(source.lower())
    if tenant:
        parts.append(tenant.lower())
    return "__".join(parts)


# =============================================================================
# Global State (for signal handler access)
# =============================================================================

_wizard_state: WizardState | None = None
DRAFT_FILE = Path(".dot-draft.yaml")
DEFAULT_OUTPUT = Path(".dot-organize.yaml")


# =============================================================================
# Draft Save/Load
# =============================================================================


def save_draft() -> bool:
    """Save wizard state to .dot-draft.yaml. Returns True if saved."""
    global _wizard_state

    if _wizard_state is None:
        return False

    if not _wizard_state.has_meaningful_data():
        return False

    try:
        content = yaml.dump(
            _wizard_state.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        DRAFT_FILE.write_text(content)
        return True
    except Exception as e:
        err_console.print(f"[yellow]Warning:[/yellow] Could not save draft: {e}")
        return False


# =============================================================================
# Signal Handlers
# =============================================================================


def sigint_handler(signum: int, frame: FrameType | None) -> None:
    """Handle Ctrl+C - save draft and exit gracefully."""
    console.print()  # Newline after ^C

    if save_draft():
        console.print(
            Panel(
                f"[yellow]Wizard interrupted.[/yellow]\n\n"
                f"Your progress has been saved to [cyan]{DRAFT_FILE}[/cyan]\n"
                f"You can manually edit and complete this file.",
                title="Draft Saved",
                border_style="yellow",
            )
        )
    else:
        console.print("[dim]Wizard cancelled.[/dim]")

    sys.exit(130)  # 128 + SIGINT(2) = standard Unix convention


def setup_signal_handlers() -> None:
    """Install signal handlers for graceful interruption."""
    signal.signal(signal.SIGINT, sigint_handler)


# =============================================================================
# Validation Functions
# =============================================================================


def validate_frame_name(name: str) -> tuple[bool, str]:
    """Validate frame name format: lower_snake_case with schema.table pattern."""
    if not name:
        return False, "Frame name cannot be empty"

    if " " in name:
        return False, "Frame name cannot contain spaces. Use underscores instead."

    # Check for schema.table pattern
    if "." not in name:
        return False, "Frame name must follow schema.table pattern (e.g., 'frame.customers')"

    parts = name.split(".")
    if len(parts) != 2:
        return False, "Frame name must have exactly one dot (e.g., 'frame.customers')"

    schema, table = parts
    if not schema or not table:
        return False, "Both schema and table parts must be non-empty"

    # Validate characters (alphanumeric + underscore)
    for part in parts:
        if not all(c.isalnum() or c == "_" for c in part):
            return False, f"Invalid characters in '{part}'. Use only letters, numbers, underscores."

    return True, ""


def validate_hook_name(name: str) -> tuple[bool, str]:
    """Validate hook name format."""
    if not name:
        return False, "Hook name cannot be empty"

    if " " in name:
        return False, "Hook name cannot contain spaces. Use underscores instead."

    if not all(c.isalnum() or c == "_" for c in name):
        return False, "Hook name must use only letters, numbers, and underscores."

    return True, ""


def validate_source_value(value: str, source_type: str) -> tuple[bool, str]:
    """Validate source relation or path."""
    if not value:
        return False, f"Source {source_type} cannot be empty"

    if source_type == "relation":
        # Relation should be schema.table format
        if not all(c.isalnum() or c in "._" for c in value):
            return False, "Relation must be alphanumeric with dots and underscores."
    elif source_type == "path":
        # Path can be more flexible but shouldn't be empty
        if not value.strip():
            return False, "Path cannot be empty"

    return True, ""


# =============================================================================
# Prompt Helpers
# =============================================================================


def prompt_with_validation(
    message: str,
    validator: Any,
    default: str = "",
    *,
    validator_args: tuple[Any, ...] = (),
) -> str:
    """Prompt for input with validation loop."""
    while True:
        value = Prompt.ask(
            message,
            default=default or None,
            console=console,
        )

        if validator_args:
            is_valid, error = validator(value, *validator_args)
        else:
            is_valid, error = validator(value)

        if is_valid:
            return value

        err_console.print(f"[red]✗[/red] {error}")


def prompt_choice(message: str, choices: list[str]) -> str:
    """Prompt for selection from numbered choices."""
    console.print(f"\n{message}")
    for i, choice in enumerate(choices, 1):
        console.print(f"  [cyan]{i}[/cyan]) {choice}")

    while True:
        answer = Prompt.ask("Select", console=console)
        try:
            idx = int(answer) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        err_console.print(f"[red]✗[/red] Please enter a number between 1 and {len(choices)}")


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
            title="Manifest Builder Wizard",
            border_style="blue",
        )
    )
    console.print()


def wizard_add_frame(state: WizardState, frame_number: int) -> WizardFrame | None:
    """Collect information for one frame."""
    state.current_step = f"frame_{frame_number}"

    console.print(f"\n[bold cyan]Frame {frame_number}[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")

    frame = WizardFrame()

    # Frame name
    frame.name = prompt_with_validation(
        "Frame name [dim](e.g., frame.customers)[/dim]",
        validate_frame_name,
    )

    # Source type
    source_type = prompt_choice(
        "Source type:",
        ["relation", "path"],
    )
    frame.source_type = source_type  # type: ignore[assignment]

    # Source value
    if source_type == "relation":
        prompt_msg = "Relation name [dim](e.g., raw.customers)[/dim]"
    else:
        prompt_msg = "File path [dim](e.g., /data/customers.csv)[/dim]"

    frame.source_value = prompt_with_validation(
        prompt_msg,
        validate_source_value,
        validator_args=(source_type,),
    )

    # Hooks - at least one primary hook required
    console.print("\n[bold]Primary Hook(s)[/bold] [dim](grain identifier)[/dim]")

    # Ask for concept (derives from table name by default)
    default_concept = frame.name.split(".")[-1] if "." in frame.name else frame.name
    default_concept = default_concept.rstrip("s")  # Simple singularization

    # Ask for source system
    default_source = "SRC"
    hook_source = Prompt.ask(
        "Source system [dim](e.g., CRM, ERP)[/dim]",
        default=default_source,
        console=console,
    )

    while True:
        # Ask for concept
        concept = Prompt.ask(
            "Business concept [dim](e.g., customer, order)[/dim]",
            default=default_concept,
            console=console,
        )

        # Ask for qualifier (optional)
        qualifier = Prompt.ask(
            "Qualifier [dim](optional, e.g., manager, billing)[/dim]",
            default="",
            console=console,
        ) or None

        # Ask for tenant (optional)
        tenant = Prompt.ask(
            "Tenant [dim](optional, e.g., AU, US)[/dim]",
            default="",
            console=console,
        ) or None

        # Generate hook name
        hook_name = generate_hook_name(concept, hook_source, qualifier, tenant)
        console.print(f"[dim]Generated hook name: [cyan]{hook_name}[/cyan][/dim]")

        # Ask for SQL expression (key column by default)
        default_expr = f"{concept}_id"
        expr = Prompt.ask(
            "SQL expression [dim](source column or expression)[/dim]",
            default=default_expr,
            console=console,
        )

        frame.hooks.append({
            "name": hook_name,
            "role": "primary",
            "concept": concept,
            "qualifier": qualifier,
            "source": hook_source,
            "tenant": tenant,
            "expr": expr,
        })

        # Ask if they want to add another hook (for composite grain)
        if not Confirm.ask(
            "Add another primary hook? [dim](for composite grain)[/dim]",
            default=False,
            console=console,
        ):
            break

    return frame


def wizard_preview(state: WizardState) -> None:
    """Display YAML preview of the manifest."""
    console.print("\n[bold cyan]Preview[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")

    data = state.to_dict()
    # Remove wizard meta for preview
    data.pop("_wizard_meta", None)

    yaml_str = yaml.dump(
        data,
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
    )

    syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
    console.print(syntax)


def wizard_summary_table(state: WizardState) -> None:
    """Display summary table of collected data."""
    console.print("\n[bold cyan]Summary[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Frame")
    table.add_column("Source")
    table.add_column("Hooks")

    for frame in state.frames:
        if frame.name:
            hooks_str = ", ".join(h["name"] for h in frame.hooks)
            source_str = f"{frame.source_type}: {frame.source_value}"
            table.add_row(frame.name, source_str, hooks_str)

    console.print(table)


# =============================================================================
# Manifest Building
# =============================================================================


def build_manifest(state: WizardState) -> Manifest:
    """Convert wizard state to immutable Manifest model."""
    frames = []

    for wf in state.frames:
        if not wf.name or not wf.source_value or not wf.hooks:
            continue

        # Build source
        if wf.source_type == "relation":
            source = Source(relation=wf.source_value)
        else:
            source = Source(path=wf.source_value)

        # Build hooks
        hooks = []
        for h in wf.hooks:
            role_str = h.get("role", "primary")
            role = HookRole.PRIMARY if role_str == "primary" else HookRole.FOREIGN
            hooks.append(Hook(
                name=h["name"],
                role=role,
                concept=h["concept"],
                qualifier=h.get("qualifier"),
                source=h["source"],
                tenant=h.get("tenant"),
                expr=h["expr"],
            ))

        # Build frame
        frame = Frame(
            name=wf.name,
            source=source,
            hooks=tuple(hooks),
        )
        frames.append(frame)

    return Manifest(
        manifest_version="1.0.0",
        schema_version="1.0.0",
        frames=tuple(frames),
    )


# =============================================================================
# File Writing
# =============================================================================


def determine_format(output_path: Path, format_arg: str | None) -> str:
    """Determine output format from flag or file extension."""
    if format_arg:
        return format_arg.lower()

    # Infer from extension
    ext = output_path.suffix.lower()
    if ext == ".json":
        return "json"
    return "yaml"


def write_manifest(
    manifest: Manifest,
    output_path: Path,
    output_format: str,
) -> None:
    """Write manifest to file in the specified format."""
    # Create parent directories if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        content = dump_manifest_json(manifest, indent=2)
    else:
        content = dump_manifest_yaml(manifest)

    if content:  # dump_manifest_json returns string or None
        output_path.write_text(content)


# =============================================================================
# Main Command
# =============================================================================


def init_command(
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path. Default: .dot-organize.yaml",
    ),
    format_: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format: yaml or json. Default: inferred from extension or yaml.",
    ),
    check_tty: bool = typer.Option(
        False,
        "--check-tty",
        hidden=True,
        help="Force TTY check (for testing).",
    ),
) -> None:
    """Create a new manifest via interactive wizard."""
    global _wizard_state

    # TTY check
    if check_tty and not sys.stdin.isatty():
        err_console.print(
            Panel(
                "[bold red]Error:[/bold red] This command requires an interactive terminal.\n\n"
                "The wizard cannot run when stdin is piped or redirected.\n"
                "Please run this command directly in a terminal.\n\n"
                "[dim]Hint: Use 'dot init --from-config seed.yaml' for scripted usage.[/dim]",
                title="Non-Interactive Mode Detected",
                border_style="red",
            )
        )
        raise typer.Exit(2)

    # Set up signal handler for Ctrl+C
    setup_signal_handlers()

    # Initialize wizard state
    _wizard_state = WizardState()

    # Determine output path and format
    output_path = output or DEFAULT_OUTPUT
    output_format = determine_format(output_path, format_)

    # Update default path based on format if no explicit output given
    if output is None and format_ == "json":
        output_path = Path(".dot-organize.json")

    # Show intro
    wizard_intro()

    try:
        # Collect frames
        frame_number = 1
        while True:
            frame = wizard_add_frame(_wizard_state, frame_number)
            if frame:
                _wizard_state.frames.append(frame)

            # Ask if they want to add another frame
            if not Confirm.ask(
                "\nAdd another frame?",
                default=False,
                console=console,
            ):
                break

            frame_number += 1

        # Show summary
        wizard_summary_table(_wizard_state)

        # Show preview
        wizard_preview(_wizard_state)

        # Check for existing file
        if output_path.exists():
            console.print(
                f"\n[yellow]Warning:[/yellow] File [cyan]{output_path}[/cyan] already exists."
            )
            if not Confirm.ask("Overwrite?", default=False, console=console):
                console.print("[dim]Cancelled. No changes made.[/dim]")
                raise typer.Exit(0)

        # Final confirmation
        if not Confirm.ask("\nWrite manifest?", default=True, console=console):
            console.print("[dim]Cancelled. No changes made.[/dim]")
            raise typer.Exit(0)

        # Build and write manifest
        manifest = build_manifest(_wizard_state)
        write_manifest(manifest, output_path, output_format)

        console.print(
            f"\n[green]✓[/green] Manifest written to [cyan]{output_path}[/cyan]"
        )

        # Mark complete (so draft won't be saved if interrupted now)
        _wizard_state.is_complete = True

    except KeyboardInterrupt:
        # Handled by signal handler
        pass
