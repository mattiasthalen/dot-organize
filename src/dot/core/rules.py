"""Validation rules for HOOK manifests.

T031-T036: Implement all ERROR and WARN validation rules

Spec Reference: spec.md#validation-rules, data-model.md §Validation Rules Reference
"""

from typing import Any

from dot.core.expression import validate_expr
from dot.core.normalization import (
    is_lower_snake_case,
    is_upper_snake_case,
    is_valid_frame_name,
    is_valid_hook_name,
    is_valid_semver,
)
from dot.core.registry import derive_concepts
from dot.models.concept import Concept
from dot.models.diagnostic import Diagnostic, Severity
from dot.models.frame import Frame, Hook, HookRole
from dot.models.manifest import Manifest
from dot.models.settings import Settings

# =============================================================================
# MANIFEST Rules
# =============================================================================


def validate_manifest_version(manifest: Manifest) -> list[Diagnostic]:
    """MANIFEST-001: manifest_version must be valid semver."""
    diagnostics: list[Diagnostic] = []

    if not is_valid_semver(manifest.manifest_version):
        diagnostics.append(
            Diagnostic(
                rule_id="MANIFEST-001",
                severity=Severity.ERROR,
                message=f"Invalid manifest_version: '{manifest.manifest_version}'. "
                f"Must be valid semver (MAJOR.MINOR.PATCH)",
                path="manifest_version",
                fix="Use format like '1.0.0', '0.1.0', or '2.1.3'",
            )
        )

    return diagnostics


def validate_schema_version(manifest: Manifest) -> list[Diagnostic]:
    """MANIFEST-002: schema_version must be valid semver."""
    diagnostics: list[Diagnostic] = []

    if not is_valid_semver(manifest.schema_version):
        diagnostics.append(
            Diagnostic(
                rule_id="MANIFEST-002",
                severity=Severity.ERROR,
                message=f"Invalid schema_version: '{manifest.schema_version}'. "
                f"Must be valid semver (MAJOR.MINOR.PATCH)",
                path="schema_version",
                fix="Use format like '1.0.0'",
            )
        )

    return diagnostics


# =============================================================================
# FRAME Rules
# =============================================================================


def validate_frame_has_hooks(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-001: Frame must have at least one hook."""
    diagnostics: list[Diagnostic] = []

    if not frame.hooks:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-001",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' has no hooks",
                path=f"{path}.hooks",
                fix="Add at least one hook to the frame",
            )
        )

    return diagnostics


def validate_frame_name(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-002: Frame name must match <schema>.<table> lower_snake_case."""
    diagnostics: list[Diagnostic] = []

    if not is_valid_frame_name(frame.name):
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-002",
                severity=Severity.ERROR,
                message=f"Invalid frame name: '{frame.name}'. "
                f"Must match pattern <schema>.<table> in lower_snake_case",
                path=f"{path}.name",
                fix="Use format like 'frame.customer', 'psa.order', 'staging.order_header'",
            )
        )

    return diagnostics


def validate_frame_has_primary_hook(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-003: Frame must have at least one primary hook."""
    diagnostics: list[Diagnostic] = []

    has_primary = any(hook.role == HookRole.PRIMARY for hook in frame.hooks)

    if not has_primary:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-003",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' has no primary hook. "
                f"At least one hook must have role='primary' to define the grain",
                path=f"{path}.hooks",
                fix="Change at least one hook's role to 'primary'",
            )
        )

    return diagnostics


def validate_frame_source_present(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-004: Frame must have source object."""
    diagnostics: list[Diagnostic] = []

    if frame.source is None:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-004",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' is missing source",
                path=f"{path}.source",
                fix="Add a source with either 'relation' or 'path'",
            )
        )

    return diagnostics


def validate_frame_source_exclusivity(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-005: Source must have exactly one of relation or path."""
    diagnostics: list[Diagnostic] = []

    if frame.source is None:
        return diagnostics

    has_relation = frame.source.relation is not None
    has_path = frame.source.path is not None

    if has_relation and has_path:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-005",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' source has both relation and path. "
                f"Only one is allowed",
                path=f"{path}.source",
                fix="Remove either 'relation' or 'path' from source",
            )
        )
    elif not has_relation and not has_path:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-005",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' source has neither relation nor path",
                path=f"{path}.source",
                fix="Add either 'relation' or 'path' to source",
            )
        )

    return diagnostics


def validate_frame_source_nonempty(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-006: Source relation/path must be non-empty string."""
    diagnostics: list[Diagnostic] = []

    if frame.source is None:
        return diagnostics

    if frame.source.relation is not None and frame.source.relation == "":
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-006",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' source.relation is empty",
                path=f"{path}.source.relation",
                fix="Provide a non-empty relation value (e.g., 'psa.customer')",
            )
        )

    if frame.source.path is not None and frame.source.path == "":
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-006",
                severity=Severity.ERROR,
                message=f"Frame '{frame.name}' source.path is empty",
                path=f"{path}.source.path",
                fix="Provide a non-empty path value (e.g., '//server/qvd/customer.qvd')",
            )
        )

    return diagnostics


# =============================================================================
# HOOK Rules
# =============================================================================


def validate_hook_required_fields(hook: Hook, path: str) -> list[Diagnostic]:
    """HOOK-001: Hook must have required fields (name, role, concept, source, expr)."""
    diagnostics: list[Diagnostic] = []

    missing_fields: list[str] = []

    if not hook.name:
        missing_fields.append("name")
    if hook.role is None:
        missing_fields.append("role")
    if not hook.concept:
        missing_fields.append("concept")
    if not hook.source:
        missing_fields.append("source")
    if not hook.expr:
        missing_fields.append("expr")

    if missing_fields:
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-001",
                severity=Severity.ERROR,
                message=f"Hook is missing required fields: {', '.join(missing_fields)}",
                path=path,
                fix=f"Add the missing fields: {', '.join(missing_fields)}",
            )
        )

    return diagnostics


def validate_hook_name(hook: Hook, path: str, settings: Settings) -> list[Diagnostic]:
    """HOOK-002: Hook name must match pattern <prefix><concept>[__<qualifier>]."""
    diagnostics: list[Diagnostic] = []

    if not is_valid_hook_name(hook.name):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-002",
                severity=Severity.ERROR,
                message=f"Invalid hook name: '{hook.name}'. "
                f"Must match pattern <prefix><concept>[__<qualifier>]",
                path=f"{path}.name",
                fix=f"Use format like '{settings.hook_prefix}customer' or "
                f"'{settings.hook_prefix}employee__manager'",
            )
        )

    return diagnostics


def validate_hook_role(hook: Hook, path: str) -> list[Diagnostic]:
    """HOOK-003: Hook role must be 'primary' or 'foreign'."""
    diagnostics: list[Diagnostic] = []

    if hook.role is not None and not isinstance(hook.role, HookRole):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-003",
                severity=Severity.ERROR,
                message=f"Invalid hook role: '{hook.role}'. "
                f"Must be 'primary' or 'foreign'",
                path=f"{path}.role",
                fix="Set role to 'primary' (defines grain) or 'foreign' (references)",
            )
        )

    return diagnostics


def validate_hook_concept(hook: Hook, path: str) -> list[Diagnostic]:
    """HOOK-004: Hook concept must be lower_snake_case."""
    diagnostics: list[Diagnostic] = []

    if hook.concept and not is_lower_snake_case(hook.concept):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-004",
                severity=Severity.ERROR,
                message=f"Invalid concept name: '{hook.concept}'. "
                f"Must be lower_snake_case",
                path=f"{path}.concept",
                fix="Use format like 'customer', 'order_line', 'product'",
            )
        )

    # Also validate qualifier if present
    if hook.qualifier and not is_lower_snake_case(hook.qualifier):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-004",
                severity=Severity.ERROR,
                message=f"Invalid qualifier: '{hook.qualifier}'. "
                f"Must be lower_snake_case",
                path=f"{path}.qualifier",
                fix="Use format like 'manager', 'billing', 'shipping'",
            )
        )

    return diagnostics


def validate_hook_source(hook: Hook, path: str) -> list[Diagnostic]:
    """HOOK-005: Hook source must be UPPER_SNAKE_CASE."""
    diagnostics: list[Diagnostic] = []

    if hook.source and not is_upper_snake_case(hook.source):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-005",
                severity=Severity.ERROR,
                message=f"Invalid source: '{hook.source}'. Must be UPPER_SNAKE_CASE",
                path=f"{path}.source",
                fix="Use format like 'CRM', 'SAP', 'SAP_FIN'",
            )
        )

    # Also validate tenant if present
    if hook.tenant and not is_upper_snake_case(hook.tenant):
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-005",
                severity=Severity.ERROR,
                message=f"Invalid tenant: '{hook.tenant}'. Must be UPPER_SNAKE_CASE",
                path=f"{path}.tenant",
                fix="Use format like 'AU', 'US', 'EU_WEST'",
            )
        )

    return diagnostics


def validate_hook_expr(hook: Hook, path: str) -> list[Diagnostic]:
    """HOOK-006: Hook expr must be non-empty valid SQL expression."""
    return validate_expr(hook.expr, f"{path}.expr")


def validate_hook_name_uniqueness(frame: Frame, path: str) -> list[Diagnostic]:
    """HOOK-007: Hook names must be unique within frame."""
    diagnostics: list[Diagnostic] = []

    seen_names: set[str] = set()
    for i, hook in enumerate(frame.hooks):
        if hook.name in seen_names:
            diagnostics.append(
                Diagnostic(
                    rule_id="HOOK-007",
                    severity=Severity.ERROR,
                    message=f"Duplicate hook name '{hook.name}' in frame '{frame.name}'",
                    path=f"{path}.hooks[{i}].name",
                    fix="Use unique hook names within each frame. "
                    "Add a qualifier to distinguish (e.g., _hk__order__billing)",
                )
            )
        seen_names.add(hook.name)

    return diagnostics


# =============================================================================
# CONCEPT Rules
# =============================================================================


def validate_concept_in_frames(
    concept: Concept, path: str, manifest: Manifest
) -> list[Diagnostic]:
    """CONCEPT-001: Concept must be used in at least one hook."""
    diagnostics: list[Diagnostic] = []

    # Get all concepts used in hooks
    used_concepts = derive_concepts(manifest)

    if concept.name not in used_concepts:
        diagnostics.append(
            Diagnostic(
                rule_id="CONCEPT-001",
                severity=Severity.ERROR,
                message=f"Concept '{concept.name}' is defined but not used in any hook",
                path=path,
                fix="Either use this concept in a hook or remove it from the concepts section",
            )
        )

    return diagnostics


def validate_concept_description(concept: Concept, path: str) -> list[Diagnostic]:
    """CONCEPT-002: Concept description must be a string (type validation only).

    Note: Length validation removed per spec update. Empty descriptions are valid
    since wizard auto-populates with empty strings for user enrichment.
    Pydantic handles type validation, so this function now returns empty list.
    """
    # Type validation is handled by Pydantic model
    # No length constraints per updated CONCEPT-002 spec
    return []


def validate_no_duplicate_concepts(manifest: Manifest) -> list[Diagnostic]:
    """CONCEPT-003: No duplicate concept names in concepts section."""
    diagnostics: list[Diagnostic] = []

    seen_names: dict[str, int] = {}
    for i, concept in enumerate(manifest.concepts):
        if concept.name in seen_names:
            diagnostics.append(
                Diagnostic(
                    rule_id="CONCEPT-003",
                    severity=Severity.ERROR,
                    message=f"Duplicate concept name: '{concept.name}' "
                    f"(first defined at concepts[{seen_names[concept.name]}])",
                    path=f"concepts[{i}].name",
                    fix="Remove duplicate concept or rename one of them",
                )
            )
        else:
            seen_names[concept.name] = i

    return diagnostics


# =============================================================================
# WARN Rules
# =============================================================================


def warn_concept_count(manifest: Manifest) -> list[Diagnostic]:
    """CONCEPT-W01: Warn if more than 100 concepts (Dunbar guidance)."""
    diagnostics: list[Diagnostic] = []

    concept_count = len(manifest.concepts)

    if concept_count > 100:
        diagnostics.append(
            Diagnostic(
                rule_id="CONCEPT-W01",
                severity=Severity.WARN,
                message=f"Manifest has {concept_count} concepts (exceeds 100). "
                f"Consider splitting into multiple manifests",
                path="concepts",
                fix="Group related concepts into separate manifests by domain",
            )
        )

    return diagnostics


def warn_weak_hook_mismatch(
    hook: Hook, path: str, concepts: list[Concept]
) -> list[Diagnostic]:
    """HOOK-W01: Warn if weak hook prefix but concept is_weak=False."""
    diagnostics: list[Diagnostic] = []

    # Check if hook uses weak prefix
    uses_weak_prefix = hook.name.startswith("_wk__")

    # Find matching concept
    matching_concept = next((c for c in concepts if c.name == hook.concept), None)

    if uses_weak_prefix and matching_concept and not matching_concept.is_weak:
        diagnostics.append(
            Diagnostic(
                rule_id="HOOK-W01",
                severity=Severity.WARN,
                message=f"Hook '{hook.name}' uses weak prefix but concept "
                f"'{hook.concept}' has is_weak=False",
                path=path,
                fix="Either set concept is_weak=True or use strong hook prefix",
            )
        )

    return diagnostics


def warn_no_primary_only_foreign(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-W01: Warn if frame has only foreign hooks (no primary)."""
    diagnostics: list[Diagnostic] = []

    if not frame.hooks:
        return diagnostics

    has_primary = any(hook.role == HookRole.PRIMARY for hook in frame.hooks)

    if not has_primary:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-W01",
                severity=Severity.WARN,
                message=f"Frame '{frame.name}' has no primary hook. "
                f"This frame may be a lookup table or needs review",
                path=f"{path}.hooks",
                fix="Add a primary hook or confirm this is intentional for a lookup",
            )
        )

    return diagnostics


def warn_duplicate_source(manifest: Manifest) -> list[Diagnostic]:
    """FRAME-W02: Warn if multiple frames use same source."""
    diagnostics: list[Diagnostic] = []

    sources: dict[str, list[str]] = {}
    for frame in manifest.frames:
        if frame.source:
            source_key = frame.source.relation or frame.source.path or ""
            if source_key:
                if source_key not in sources:
                    sources[source_key] = []
                sources[source_key].append(frame.name)

    for source, frame_names in sources.items():
        if len(frame_names) > 1:
            diagnostics.append(
                Diagnostic(
                    rule_id="FRAME-W02",
                    severity=Severity.WARN,
                    message=f"Source '{source}' is used by multiple frames: "
                    f"{', '.join(frame_names)}",
                    path="frames",
                    fix="Review if these frames should share a source or be consolidated",
                )
            )

    return diagnostics


def warn_too_many_hooks(frame: Frame, path: str) -> list[Diagnostic]:
    """FRAME-W03: Warn if frame has more than 20 hooks."""
    diagnostics: list[Diagnostic] = []

    hook_count = len(frame.hooks)

    if hook_count > 20:
        diagnostics.append(
            Diagnostic(
                rule_id="FRAME-W03",
                severity=Severity.WARN,
                message=f"Frame '{frame.name}' has {hook_count} hooks (exceeds 20). "
                f"Consider splitting into multiple frames",
                path=f"{path}.hooks",
                fix="Group related hooks into separate frames by concern",
            )
        )

    return diagnostics


def warn_too_many_frames(manifest: Manifest) -> list[Diagnostic]:
    """MANIFEST-W01: Warn if more than 50 frames."""
    diagnostics: list[Diagnostic] = []

    frame_count = len(manifest.frames)

    if frame_count > 50:
        diagnostics.append(
            Diagnostic(
                rule_id="MANIFEST-W01",
                severity=Severity.WARN,
                message=f"Manifest has {frame_count} frames (exceeds 50). "
                f"Consider splitting into multiple manifests",
                path="frames",
                fix="Group related frames into separate manifests by domain",
            )
        )

    return diagnostics


def warn_unknown_fields(raw_data: dict[str, Any]) -> list[Diagnostic]:
    """MANIFEST-W02: Warn on unknown fields for forward compatibility."""
    diagnostics: list[Diagnostic] = []

    known_fields = {
        "manifest_version",
        "schema_version",
        "metadata",
        "settings",
        "frames",
        "concepts",
    }

    unknown_fields = set(raw_data.keys()) - known_fields

    for field in unknown_fields:
        diagnostics.append(
            Diagnostic(
                rule_id="MANIFEST-W02",
                severity=Severity.WARN,
                message=f"Unknown field '{field}' in manifest root. "
                f"This may be from a newer schema version",
                path=field,
                fix="Check schema version compatibility or remove unknown field",
            )
        )

    return diagnostics
