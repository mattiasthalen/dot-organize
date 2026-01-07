"""
Init command - Interactive manifest builder wizard (T074-T083, T110-T112).

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
- T110: Frozen dataclasses for WizardFrame/WizardState (NFR-057)
- T111: Pure functions for state operations (NFR-057)
- T112: Immutable state transitions (NFR-057)
"""

from __future__ import annotations

import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from dot.io.json import dump_manifest_json
from dot.io.yaml import dump_manifest_yaml
from dot.models import (
    Frame,
    Hook,
    HookRole,
    Manifest,
    Source,
)

if TYPE_CHECKING:
    from types import FrameType

# =============================================================================
# Console Setup
# =============================================================================

console = Console()
err_console = Console(stderr=True)

# =============================================================================
# Data Classes for Wizard State (Frozen per NFR-057)
# =============================================================================


@dataclass(frozen=True)
class WizardFrame:
    """Immutable frame data collected during wizard flow."""

    name: str = ""
    source_type: Literal["relation", "path"] = "relation"
    source_value: str = ""
    hooks: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class WizardState:
    """Immutable state for the wizard - enables draft saving on interrupt."""

    frames: tuple[WizardFrame, ...] = ()
    current_step: str = "start"
    is_complete: bool = False


# =============================================================================
# Pure Functions for Wizard State (NFR-057)
# =============================================================================


def wizard_state_has_meaningful_data(state: WizardState) -> bool:
    """Check if there's at least one complete frame worth saving.

    A frame is considered complete if it has a name, source value, and at least one hook.
    """
    return any(f.name and f.source_value and f.hooks for f in state.frames)


def wizard_state_to_dict(state: WizardState) -> dict[str, Any]:
    """Convert wizard state to dictionary for YAML serialization."""
    return {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "frames": [
            {
                "name": f.name,
                "source": {
                    f.source_type: f.source_value,
                },
                "hooks": list(f.hooks),
            }
            for f in state.frames
            if f.name and f.source_value and f.hooks
        ],
        "_wizard_meta": {
            "current_step": state.current_step,
            "is_complete": state.is_complete,
        },
    }


def wizard_state_with_step(state: WizardState, step: str) -> WizardState:
    """Return new WizardState with updated current_step."""
    return WizardState(
        frames=state.frames,
        current_step=step,
        is_complete=state.is_complete,
    )


def wizard_state_add_frame(state: WizardState, frame: WizardFrame) -> WizardState:
    """Return new WizardState with frame appended."""
    return WizardState(
        frames=state.frames + (frame,),
        current_step=state.current_step,
        is_complete=state.is_complete,
    )


def wizard_state_mark_complete(state: WizardState) -> WizardState:
    """Return new WizardState marked as complete."""
    return WizardState(
        frames=state.frames,
        current_step=state.current_step,
        is_complete=True,
    )


def wizard_frame_with_name(frame: WizardFrame, name: str) -> WizardFrame:
    """Return new WizardFrame with updated name."""
    return WizardFrame(
        name=name,
        source_type=frame.source_type,
        source_value=frame.source_value,
        hooks=frame.hooks,
    )


def wizard_frame_with_source(
    frame: WizardFrame,
    source_type: Literal["relation", "path"],
    source_value: str,
) -> WizardFrame:
    """Return new WizardFrame with updated source."""
    return WizardFrame(
        name=frame.name,
        source_type=source_type,
        source_value=source_value,
        hooks=frame.hooks,
    )


def wizard_frame_add_hook(frame: WizardFrame, hook: dict[str, Any]) -> WizardFrame:
    """Return new WizardFrame with hook appended."""
    return WizardFrame(
        name=frame.name,
        source_type=frame.source_type,
        source_value=frame.source_value,
        hooks=frame.hooks + (hook,),
    )


def generate_hook_name(
    concept: str, qualifier: str | None = None, is_weak: bool = False
) -> str:
    """
    Generate hook name following FR-051 pattern: <prefix><concept>[__<qualifier>].

    Source and tenant are NOT part of the hook name - they belong in the
    auto-derived key set per FR-054.

    Examples:
        - customer -> _hk__customer
        - customer + manager -> _hk__customer__manager
        - customer (weak) -> _wk__customer
    """
    prefix = "_wk" if is_weak else "_hk"
    parts = [prefix]
    parts.append(concept.lower())
    if qualifier:
        parts.append(qualifier.lower())
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

    if not wizard_state_has_meaningful_data(_wizard_state):
        return False

    try:
        content = yaml.dump(
            wizard_state_to_dict(_wizard_state),
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
        return (
            False,
            "Frame name must follow schema.table pattern (e.g., 'frame.customers')",
        )

    parts = name.split(".")
    if len(parts) != 2:
        return False, "Frame name must have exactly one dot (e.g., 'frame.customers')"

    schema, table = parts
    if not schema or not table:
        return False, "Both schema and table parts must be non-empty"

    # Validate characters (alphanumeric + underscore)
    for part in parts:
        if not all(c.isalnum() or c == "_" for c in part):
            return (
                False,
                f"Invalid characters in '{part}'. Use only letters, numbers, underscores.",
            )

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
    elif source_type == "path" and not value.strip():
        # Path can be more flexible but shouldn't be empty
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
    value: str = ""
    while True:
        value = Prompt.ask(
            message,
            default=default if default else "",
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


def wizard_add_frame(frame_number: int) -> WizardFrame | None:
    """Collect information for one frame using immutable state transitions."""
    console.print(f"\n[bold cyan]Frame {frame_number}[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")

    # Start with empty frame
    frame = WizardFrame()

    # Frame name
    name = prompt_with_validation(
        "Frame name [dim](e.g., frame.customers)[/dim]",
        validate_frame_name,
    )
    frame = wizard_frame_with_name(frame, name)

    # Source type
    source_type_str = prompt_choice(
        "Source type:",
        ["relation", "path"],
    )
    # Cast to Literal type - prompt_choice guarantees one of these values
    source_type: Literal["relation", "path"] = (
        "relation" if source_type_str == "relation" else "path"
    )

    # Source value
    if source_type == "relation":
        prompt_msg = "Relation name [dim](e.g., raw.customers)[/dim]"
    else:
        prompt_msg = "File path [dim](e.g., /data/customers.csv)[/dim]"

    source_value = prompt_with_validation(
        prompt_msg,
        validate_source_value,
        validator_args=(source_type,),
    )
    frame = wizard_frame_with_source(
        frame,
        source_type,
        source_value,
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
        qualifier = (
            Prompt.ask(
                "Qualifier [dim](optional, e.g., manager, billing)[/dim]",
                default="",
                console=console,
            )
            or None
        )

        # Ask for tenant (optional)
        tenant = (
            Prompt.ask(
                "Tenant [dim](optional, e.g., AU, US)[/dim]",
                default="",
                console=console,
            )
            or None
        )

        # Generate suggested hook name and prompt user (FR-026: auto-suggest, not auto-generate)
        suggested_hook_name = generate_hook_name(concept, qualifier)
        hook_name = Prompt.ask(
            "Hook name",
            default=suggested_hook_name,
            console=console,
        )

        # Ask for SQL expression (key column by default)
        default_expr = f"{concept}_id"
        expr = Prompt.ask(
            "SQL expression [dim](source column or expression)[/dim]",
            default=default_expr,
            console=console,
        )

        frame = wizard_frame_add_hook(
            frame,
            {
                "name": hook_name,
                "role": "primary",
                "concept": concept,
                "qualifier": qualifier,
                "source": hook_source,
                "tenant": tenant,
                "expr": expr,
            },
        )

        # Ask if they want to add another hook (for composite grain)
        if not Confirm.ask(
            "Add another primary hook? [dim](for composite grain)[/dim]",
            default=False,
            console=console,
        ):
            break

    # Foreign hooks - optional, for relationships to other concepts (FR-028)
    if Confirm.ask(
        "Add foreign hooks? [dim](relationships to other concepts)[/dim]",
        default=False,
        console=console,
    ):
        console.print("\n[bold]Foreign Hook(s)[/bold] [dim](references to other concepts)[/dim]")

        while True:
            # Ask for concept
            concept = Prompt.ask(
                "Business concept [dim](e.g., customer, order)[/dim]",
                console=console,
            )

            # Ask for qualifier (optional)
            qualifier = (
                Prompt.ask(
                    "Qualifier [dim](optional, e.g., manager, billing)[/dim]",
                    default="",
                    console=console,
                )
                or None
            )

            # Ask for tenant (optional)
            tenant = (
                Prompt.ask(
                    "Tenant [dim](optional, e.g., AU, US)[/dim]",
                    default="",
                    console=console,
                )
                or None
            )

            # Generate suggested hook name and prompt user (FR-026: auto-suggest)
            suggested_hook_name = generate_hook_name(concept, qualifier)
            hook_name = Prompt.ask(
                "Hook name",
                default=suggested_hook_name,
                console=console,
            )

            # Ask for SQL expression (key column by default)
            default_expr = f"{concept}_id"
            expr = Prompt.ask(
                "SQL expression [dim](source column or expression)[/dim]",
                default=default_expr,
                console=console,
            )

            frame = wizard_frame_add_hook(
                frame,
                {
                    "name": hook_name,
                    "role": "foreign",
                    "concept": concept,
                    "qualifier": qualifier,
                    "source": hook_source,
                    "tenant": tenant,
                    "expr": expr,
                },
            )

            # Ask if they want to add another foreign hook
            if not Confirm.ask(
                "Add another foreign hook?",
                default=False,
                console=console,
            ):
                break

    return frame


def wizard_preview(state: WizardState) -> None:
    """Display YAML preview of the manifest."""
    console.print("\n[bold cyan]Preview[/bold cyan]")
    console.print("[dim]─" * 40 + "[/dim]")

    data = wizard_state_to_dict(state)
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
            hooks.append(
                Hook(
                    name=h["name"],
                    role=role,
                    concept=h["concept"],
                    qualifier=h.get("qualifier"),
                    source=h["source"],
                    tenant=h.get("tenant"),
                    expr=h["expr"],
                )
            )

        # Build frame
        frame = Frame(
            name=wf.name,
            source=source,
            hooks=list(hooks),
        )
        frames.append(frame)

    return Manifest(
        manifest_version="1.0.0",
        schema_version="1.0.0",
        frames=list(frames),
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


# =============================================================================
# Non-Interactive Mode Functions
# =============================================================================


def load_seed_config(path: Path) -> dict[str, Any]:
    """Load and validate seed config from YAML file.

    Returns:
        Parsed seed config dictionary.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ParseError: If YAML is invalid.
        ValueError: If config is missing required fields.
    """
    if not path.exists():
        raise FileNotFoundError(f"Seed file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in seed file: {e}") from e

    if not data:
        raise ValueError("Seed file is empty")

    if "frames" not in data:
        raise ValueError("Seed file must contain 'frames' list")

    if not data["frames"]:
        raise ValueError("Seed file must contain at least one frame")

    return data


def validate_seed_frames(frames: list[dict[str, Any]]) -> list[str]:
    """Validate seed frame definitions.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    for i, frame in enumerate(frames):
        prefix = f"frames[{i}]"

        if "name" not in frame:
            errors.append(f"{prefix}: missing 'name'")

        if "source" not in frame:
            errors.append(f"{prefix}: missing 'source'")
        elif not isinstance(frame["source"], dict):
            errors.append(f"{prefix}.source: must be an object")
        elif "relation" not in frame["source"] and "path" not in frame["source"]:
            errors.append(f"{prefix}.source: must contain 'relation' or 'path'")

        if "hooks" not in frame:
            errors.append(f"{prefix}: missing 'hooks'")
        elif not frame["hooks"]:
            errors.append(f"{prefix}.hooks: must contain at least one hook")
        else:
            for j, hook in enumerate(frame["hooks"]):
                hook_prefix = f"{prefix}.hooks[{j}]"
                if "concept" not in hook:
                    errors.append(f"{hook_prefix}: missing 'concept'")
                if "source" not in hook:
                    errors.append(f"{hook_prefix}: missing 'source'")
                if "expr" not in hook:
                    errors.append(f"{hook_prefix}: missing 'expr'")

    return errors


def build_manifest_from_seed(seed: dict[str, Any]) -> Manifest:
    """Build manifest from seed config."""
    frames = []

    for seed_frame in seed.get("frames", []):
        # Build source
        source_dict = seed_frame.get("source", {})
        if "relation" in source_dict:
            source = Source(relation=source_dict["relation"])
        else:
            source = Source(path=source_dict.get("path"))

        # Build hooks with auto-generated names
        hooks = []
        for h in seed_frame.get("hooks", []):
            concept = h["concept"]
            hook_source = h["source"]
            qualifier = h.get("qualifier")
            tenant = h.get("tenant")
            expr = h["expr"]

            # Auto-generate hook name if not provided
            name = h.get("name") or generate_hook_name(concept, qualifier)

            hooks.append(
                Hook(
                    name=name,
                    role=HookRole.PRIMARY,  # Default to primary
                    concept=concept,
                    qualifier=qualifier,
                    source=hook_source,
                    tenant=tenant,
                    expr=expr,
                )
            )

        frame = Frame(
            name=seed_frame["name"],
            source=source,
            hooks=list(hooks),
        )
        frames.append(frame)

    return Manifest(
        manifest_version="1.0.0",
        schema_version="1.0.0",
        frames=list(frames),
    )


def build_manifest_from_flags(concept: str, source: str) -> Manifest:
    """Build minimal manifest from --concept and --source flags."""
    # Auto-derive frame name
    frame_name = f"frame.{concept}s"  # Simple pluralization

    # Auto-derive relation
    relation = f"raw.{concept}s"

    # Auto-generate hook
    hook_name = generate_hook_name(concept)
    expr = f"{concept}_id"

    hook = Hook(
        name=hook_name,
        role=HookRole.PRIMARY,
        concept=concept,
        source=source,
        expr=expr,
    )

    frame = Frame(
        name=frame_name,
        source=Source(relation=relation),
        hooks=[hook],
    )

    return Manifest(
        manifest_version="1.0.0",
        schema_version="1.0.0",
        frames=[frame],
    )


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
    from_config: Path | None = typer.Option(
        None,
        "--from-config",
        help="Generate manifest from seed config file (non-interactive).",
    ),
    concept: str | None = typer.Option(
        None,
        "--concept",
        help="Business concept for quick manifest (requires --source).",
    ),
    source: str | None = typer.Option(
        None,
        "--source",
        help="Source system for quick manifest (requires --concept).",
    ),
    check_tty: bool = typer.Option(
        False,
        "--check-tty",
        hidden=True,
        help="Force TTY check (for testing).",
    ),
) -> None:
    """Create a new manifest via interactive wizard or from config."""
    global _wizard_state

    # Determine output path and format
    output_path = output or DEFAULT_OUTPUT
    output_format = determine_format(output_path, format_)

    # Update default path based on format if no explicit output given
    if output is None and format_ == "json":
        output_path = Path(".dot-organize.json")

    # ==========================================================================
    # Non-interactive: --from-config
    # ==========================================================================
    if from_config is not None:
        try:
            seed = load_seed_config(from_config)
            errors = validate_seed_frames(seed.get("frames", []))

            if errors:
                err_console.print("[bold red]Error:[/bold red] Invalid seed config:")
                for error in errors:
                    err_console.print(f"  • {error}")
                raise typer.Exit(1)

            manifest = build_manifest_from_seed(seed)
            write_manifest(manifest, output_path, output_format)
            console.print(f"[green]✓[/green] Manifest written to [cyan]{output_path}[/cyan]")
            return

        except FileNotFoundError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)
        except ValueError as e:
            err_console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(1)

    # ==========================================================================
    # Non-interactive: --concept and --source flags
    # ==========================================================================
    if concept is not None or source is not None:
        if concept is None:
            err_console.print(
                "[bold red]Error:[/bold red] --concept is required when using --source"
            )
            raise typer.Exit(1)
        if source is None:
            err_console.print(
                "[bold red]Error:[/bold red] --source is required when using --concept"
            )
            raise typer.Exit(1)

        manifest = build_manifest_from_flags(concept, source)
        write_manifest(manifest, output_path, output_format)
        console.print(f"[green]✓[/green] Manifest written to [cyan]{output_path}[/cyan]")
        return

    # ==========================================================================
    # Interactive wizard mode
    # ==========================================================================

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

    # Initialize wizard state (immutable - reassigned on each transition)
    _wizard_state = WizardState()

    # Show intro
    wizard_intro()

    try:
        # Collect frames using immutable state transitions
        frame_number = 1
        while True:
            # Update current step
            _wizard_state = wizard_state_with_step(_wizard_state, f"frame_{frame_number}")

            frame = wizard_add_frame(frame_number)
            if frame:
                _wizard_state = wizard_state_add_frame(_wizard_state, frame)

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

        console.print(f"\n[green]✓[/green] Manifest written to [cyan]{output_path}[/cyan]")

        # Mark complete using immutable transition
        _wizard_state = wizard_state_mark_complete(_wizard_state)

    except KeyboardInterrupt:
        # Handled by signal handler
        pass
