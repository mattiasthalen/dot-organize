"""Composite manifest validation orchestrator.

T037: Combine all rules into validate_manifest function

Spec Reference: spec.md#validation-rules, data-model.md §Validation
"""

from typing import Any

from dot.models.diagnostic import Diagnostic, Severity
from dot.models.manifest import Manifest
from dot.models.settings import Settings

from dot.core.rules import (
    # MANIFEST rules
    validate_manifest_version,
    validate_schema_version,
    # FRAME rules
    validate_frame_has_hooks,
    validate_frame_name,
    validate_frame_has_primary_hook,
    validate_frame_source_present,
    validate_frame_source_exclusivity,
    validate_frame_source_nonempty,
    # HOOK rules
    validate_hook_required_fields,
    validate_hook_name,
    validate_hook_role,
    validate_hook_concept,
    validate_hook_source,
    validate_hook_expr,
    validate_hook_name_uniqueness,
    # CONCEPT rules
    validate_concept_in_frames,
    validate_concept_description,
    validate_no_duplicate_concepts,
    # WARN rules
    warn_concept_count,
    warn_weak_hook_mismatch,
    warn_duplicate_source,
    warn_too_many_hooks,
    warn_too_many_frames,
    warn_unknown_fields,
)


def validate_manifest(
    manifest: Manifest,
    *,
    include_warnings: bool = True,
    raw_data: dict[str, Any] | None = None,
) -> list[Diagnostic]:
    """Validate a manifest and return all diagnostics.

    Runs all ERROR and WARN validation rules against the manifest.

    Args:
        manifest: The parsed Manifest to validate.
        include_warnings: If True, include WARN diagnostics (default True).
        raw_data: Optional raw dict for unknown field detection.

    Returns:
        List of Diagnostic objects sorted by (severity, rule_id, path).
    """
    diagnostics: list[Diagnostic] = []
    settings = manifest.settings

    # ==========================================================================
    # MANIFEST-level rules
    # ==========================================================================
    diagnostics.extend(validate_manifest_version(manifest))
    diagnostics.extend(validate_schema_version(manifest))

    # ==========================================================================
    # FRAME-level rules
    # ==========================================================================
    for i, frame in enumerate(manifest.frames):
        path = f"frames[{i}]"

        diagnostics.extend(validate_frame_name(frame, path))
        diagnostics.extend(validate_frame_has_hooks(frame, path))
        diagnostics.extend(validate_frame_has_primary_hook(frame, path))
        diagnostics.extend(validate_frame_source_present(frame, path))
        diagnostics.extend(validate_frame_source_exclusivity(frame, path))
        diagnostics.extend(validate_frame_source_nonempty(frame, path))
        diagnostics.extend(validate_hook_name_uniqueness(frame, path))

        # HOOK-level rules within frame
        for j, hook in enumerate(frame.hooks):
            hook_path = f"{path}.hooks[{j}]"

            diagnostics.extend(validate_hook_required_fields(hook, hook_path))
            diagnostics.extend(validate_hook_name(hook, hook_path, settings))
            diagnostics.extend(validate_hook_role(hook, hook_path))
            diagnostics.extend(validate_hook_concept(hook, hook_path))
            diagnostics.extend(validate_hook_source(hook, hook_path))
            diagnostics.extend(validate_hook_expr(hook, hook_path))

            # WARN: weak hook mismatch
            if include_warnings:
                diagnostics.extend(
                    warn_weak_hook_mismatch(hook, hook_path, manifest.concepts)
                )

        # WARN: too many hooks
        if include_warnings:
            diagnostics.extend(warn_too_many_hooks(frame, path))

    # ==========================================================================
    # CONCEPT-level rules
    # ==========================================================================
    diagnostics.extend(validate_no_duplicate_concepts(manifest))

    for i, concept in enumerate(manifest.concepts):
        path = f"concepts[{i}]"

        diagnostics.extend(validate_concept_in_frames(concept, path, manifest))
        diagnostics.extend(validate_concept_description(concept, path))

    # ==========================================================================
    # WARN rules (if enabled)
    # ==========================================================================
    if include_warnings:
        diagnostics.extend(warn_concept_count(manifest))
        diagnostics.extend(warn_duplicate_source(manifest))
        diagnostics.extend(warn_too_many_frames(manifest))

        if raw_data is not None:
            diagnostics.extend(warn_unknown_fields(raw_data))

    # ==========================================================================
    # Sort by severity (ERROR first), then rule_id, then path
    # ==========================================================================
    def sort_key(d: Diagnostic) -> tuple[int, str, str]:
        severity_order = 0 if d.severity == Severity.ERROR else 1
        return (severity_order, d.rule_id, d.path)

    diagnostics.sort(key=sort_key)

    return diagnostics


def has_errors(diagnostics: list[Diagnostic]) -> bool:
    """Check if any diagnostics are ERROR severity."""
    return any(d.severity == Severity.ERROR for d in diagnostics)


def filter_errors(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Return only ERROR diagnostics."""
    return [d for d in diagnostics if d.severity == Severity.ERROR]


def filter_warnings(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    """Return only WARN diagnostics."""
    return [d for d in diagnostics if d.severity == Severity.WARN]
