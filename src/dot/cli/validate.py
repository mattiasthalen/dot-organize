"""Validate command implementation.

T069-T072a: Implement validate command with diagnostic output,
--json flag, exit codes, and --no-color flag
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from dot.core.validation import (
    filter_errors,
    filter_warnings,
    has_errors,
    validate_manifest,
)
from dot.io.yaml import ParseError, load_manifest_yaml
from dot.models.diagnostic import Diagnostic, Severity


def validate(
    manifest_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the manifest YAML file to validate.",
            exists=False,  # We handle existence check ourselves for better error message
        ),
    ],
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output results in JSON format for machine processing.",
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option(
            "--no-color",
            help="Disable colored output (for screen readers and CI).",
        ),
    ] = False,
) -> None:
    """Validate a HOOK manifest file.

    Exit codes:
    - 0: Manifest is valid (may have warnings)
    - 1: Manifest has validation errors or parse errors
    - 2: Usage error (file not found, etc.)
    """
    # Check file exists
    if not manifest_path.exists():
        if json_output:
            _output_json({"valid": False, "error": f"File not found: {manifest_path}"})
        else:
            typer.echo(f"Error: File not found: {manifest_path}", err=True)
        raise typer.Exit(code=2)

    # Try to parse and validate
    try:
        manifest, raw_data = load_manifest_yaml(manifest_path, return_raw=True)
    except ParseError as e:
        if json_output:
            _output_json(
                {
                    "valid": False,
                    "error": str(e),
                    "line": e.line,
                    "column": e.column,
                }
            )
        else:
            typer.echo(f"Parse error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        if json_output:
            _output_json({"valid": False, "error": str(e)})
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    # Run validation
    diagnostics = validate_manifest(manifest, raw_data=raw_data)

    # Prepare output
    errors = filter_errors(diagnostics)
    warnings = filter_warnings(diagnostics)

    if json_output:
        _output_json_diagnostics(errors, warnings)
    else:
        _output_human_diagnostics(errors, warnings, manifest_path)

    # Set exit code based on errors
    if has_errors(diagnostics):
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)


def _output_json(data: dict[str, Any]) -> None:
    """Output JSON data to stdout."""
    typer.echo(json.dumps(data, indent=2))


def _output_json_diagnostics(
    errors: list[Diagnostic],
    warnings: list[Diagnostic],
) -> None:
    """Output diagnostics in JSON format."""
    result = {
        "valid": len(errors) == 0,
        "errors": [_diagnostic_to_dict(d) for d in errors],
        "warnings": [_diagnostic_to_dict(d) for d in warnings],
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }
    _output_json(result)


def _diagnostic_to_dict(d: Diagnostic) -> dict[str, Any]:
    """Convert Diagnostic to JSON-serializable dict."""
    result: dict[str, Any] = {
        "rule_id": d.rule_id,
        "severity": d.severity.value,
        "message": d.message,
        "path": d.path,
    }
    if d.fix:
        result["fix"] = d.fix
    return result


def _output_human_diagnostics(
    errors: list[Diagnostic],
    warnings: list[Diagnostic],
    manifest_path: Path,
) -> None:
    """Output diagnostics in human-readable format.

    No ANSI escape codes for screen reader compatibility (NFR-010).
    """
    if errors:
        for d in errors:
            _print_diagnostic(d)
        typer.echo()

    if warnings:
        for d in warnings:
            _print_diagnostic(d)
        typer.echo()

    # Summary
    if errors:
        typer.echo(
            f"Manifest {manifest_path} is invalid: "
            f"{len(errors)} error(s), {len(warnings)} warning(s)"
        )
    elif warnings:
        typer.echo(f"Manifest {manifest_path} is valid with {len(warnings)} warning(s)")
    else:
        typer.echo(f"Manifest {manifest_path} is valid")


def _print_diagnostic(d: Diagnostic) -> None:
    """Print a single diagnostic in human-readable format.

    No ANSI escape codes for screen reader compatibility (NFR-010).
    """
    severity_str = "ERROR" if d.severity == Severity.ERROR else "WARN"
    typer.echo(f"{severity_str} [{d.rule_id}] at {d.path}")
    typer.echo(f"  {d.message}")
    if d.fix:
        typer.echo(f"  Fix: {d.fix}")
