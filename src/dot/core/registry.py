"""Registry derivation functions.

T027-T029: Implement key set derivation, concept registry, hook registry

Spec Reference: data-model.md §Auto-Derived Registries
"""

from dot.models.frame import Hook
from dot.models.manifest import Manifest


def _build_key_set(hook: Hook) -> str:
    """Build key set string from hook.

    Pattern: CONCEPT[~QUALIFIER]@SOURCE[~TENANT]

    Examples:
        - CUSTOMER@CRM
        - EMPLOYEE~MANAGER@CRM
        - ORDER@SAP~AU
        - ORDER~BILLING@SAP~EU
    """
    # Build concept part
    concept_part = hook.concept.upper()
    if hook.qualifier:
        concept_part += f"~{hook.qualifier.upper()}"

    # Build source part
    source_part = hook.source.upper()
    if hook.tenant:
        source_part += f"~{hook.tenant.upper()}"

    return f"{concept_part}@{source_part}"


def derive_key_sets(manifest: Manifest) -> set[str]:
    """Derive unique key sets from all hooks in manifest.

    Returns a set of unique key set strings.
    """
    key_sets: set[str] = set()
    for frame in manifest.frames:
        for hook in frame.hooks:
            key_set = _build_key_set(hook)
            key_sets.add(key_set)
    return key_sets


def derive_concepts(manifest: Manifest) -> set[str]:
    """Derive unique concept names from all hooks in manifest.

    Returns a set of unique concept names (lowercase).
    """
    concepts: set[str] = set()
    for frame in manifest.frames:
        for hook in frame.hooks:
            concepts.add(hook.concept)
    return concepts


def derive_hook_registry(manifest: Manifest) -> dict[str, list[tuple[str, Hook]]]:
    """Index all hooks by name for relationship detection.

    Returns: {hook_name: [(frame_name, hook), ...]}

    This allows finding all frames that reference the same hook name,
    useful for relationship detection and join safety validation.
    """
    registry: dict[str, list[tuple[str, Hook]]] = {}
    for frame in manifest.frames:
        for hook in frame.hooks:
            if hook.name not in registry:
                registry[hook.name] = []
            registry[hook.name].append((frame.name, hook))
    return registry
