#!/usr/bin/env python3
"""
JSON Schema + Pydantic Integration Research

Testing how to combine JSON Schema structural validation with
Pydantic semantic validation for HOOK manifests.
"""

import json
from enum import Enum
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field

# Load our actual schema
SCHEMA_PATH = Path(__file__).parent.parent / "contracts" / "manifest-schema.json"


def load_schema() -> dict:
    """Load the HOOK manifest schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


# ============================================================================
# SECTION 1: Diagnostic Model (matching data-model.md)
# ============================================================================


class Severity(str, Enum):
    """Diagnostic severity levels."""

    ERROR = "ERROR"
    WARN = "WARN"


class Diagnostic(BaseModel):
    """Validation diagnostic message."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(description="Diagnostic rule identifier")
    severity: Severity = Field(description="Severity level")
    message: str = Field(description="Human-readable message")
    path: str = Field(description="JSONPath to offending field")
    fix: str = Field(description="Suggested fix")

    def __str__(self) -> str:
        return f"{self.severity.value} [{self.rule_id}] {self.message}\n  at: {self.path}\n  fix: {self.fix}"


# ============================================================================
# SECTION 2: JSON Schema Error to Diagnostic Converter
# ============================================================================


def jsonschema_error_to_diagnostic(error) -> Diagnostic:
    """
    Convert a jsonschema ValidationError to our Diagnostic format.

    Maps JSON Schema validators to our rule IDs.
    """
    # Build JSONPath from absolute_path
    path_parts = list(error.absolute_path)
    if path_parts:
        json_path = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in path_parts).lstrip(
            "."
        )
    else:
        json_path = "(root)"

    # Map validator types to rule IDs
    rule_id = _map_error_to_rule_id(error, json_path)

    # Build human-readable fix message
    fix = _build_fix_message(error, json_path)

    return Diagnostic(
        rule_id=rule_id, severity=Severity.ERROR, message=error.message, path=json_path, fix=fix
    )


def _map_error_to_rule_id(error, json_path: str) -> str:
    """Map JSON Schema validation errors to our rule IDs."""
    validator = error.validator

    if validator == "required":
        # Determine which entity the required field belongs to
        if "frames" in json_path and "hooks" in json_path:
            return "HOOK-001"
        elif "frames" in json_path:
            return "FRAME-001"
        elif "metadata" in json_path:
            return "MANIFEST-003"
        else:
            return "MANIFEST-001"

    elif validator == "pattern":
        if "manifest_version" in json_path or "schema_version" in json_path:
            return "MANIFEST-002"
        elif "hooks" in json_path:
            if ".name" in json_path:
                return "HOOK-002"
            elif ".concept" in json_path or ".qualifier" in json_path:
                return "HOOK-004"
            elif ".source" in json_path or ".tenant" in json_path:
                return "HOOK-005"
        elif "frames" in json_path and ".name" in json_path:
            return "FRAME-002"
        return "SCHEMA-PATTERN"

    elif validator == "enum":
        if "role" in json_path:
            return "HOOK-003"
        return "SCHEMA-ENUM"

    elif validator == "oneOf":
        if "source" in json_path:
            return "FRAME-006"
        return "SCHEMA-ONEOF"

    elif validator == "minItems":
        if "frames" in json_path and "hooks" in json_path:
            return "FRAME-003"
        elif "frames" in json_path:
            return "MANIFEST-004"
        return "SCHEMA-MIN-ITEMS"

    elif validator == "minLength":
        return "SCHEMA-EMPTY-STRING"

    elif validator == "additionalProperties":
        return "SCHEMA-UNKNOWN-FIELD"

    else:
        return f"SCHEMA-{validator.upper()}"


def _build_fix_message(error, json_path: str) -> str:
    """Build a helpful fix message based on error type."""
    validator = error.validator

    if validator == "required":
        missing = error.message.split("'")[1]
        return f"Add required field '{missing}'"

    elif validator == "pattern":
        pattern = error.validator_value
        if "manifest_version" in json_path or "schema_version" in json_path:
            return "Use semver format: MAJOR.MINOR.PATCH (e.g., '1.0.0')"
        elif "hooks" in json_path and ".name" in json_path:
            return "Use format: _hk__<concept> or _wk__<concept>[__<qualifier>]"
        elif ".concept" in json_path or ".qualifier" in json_path:
            return "Use lower_snake_case (e.g., 'customer', 'order_line')"
        elif ".source" in json_path or ".tenant" in json_path:
            return "Use UPPER_SNAKE_CASE (e.g., 'CRM', 'SAP_FIN')"
        elif "frames" in json_path and ".name" in json_path:
            return "Use format: <schema>.<table> in lower_snake_case (e.g., 'frame.customer')"
        return f"Value must match pattern: {pattern}"

    elif validator == "enum":
        allowed = ", ".join(repr(v) for v in error.validator_value)
        return f"Use one of: {allowed}"

    elif validator == "oneOf":
        if "source" in json_path:
            return "Provide exactly one of 'relation' OR 'path', not both or neither"
        return "Value must match exactly one of the allowed schemas"

    elif validator == "minItems":
        return f"Add at least {error.validator_value} item(s)"

    elif validator == "minLength":
        return "Value cannot be empty"

    elif validator == "maxLength":
        return f"Value must be at most {error.validator_value} character(s)"

    elif validator == "additionalProperties":
        return "Remove unknown field(s)"

    return f"Check value at '{json_path}'"


# ============================================================================
# SECTION 3: Schema Validator Class
# ============================================================================


class SchemaValidator:
    """
    JSON Schema validator for HOOK manifests.

    Performs structural validation against the JSON Schema before
    semantic validation with Pydantic models.
    """

    def __init__(self, schema_path: Path | str | None = None):
        """
        Initialize the validator with a schema.

        Args:
            schema_path: Path to JSON Schema file. Uses default if None.
        """
        if schema_path is None:
            schema_path = SCHEMA_PATH

        with open(schema_path) as f:
            self.schema = json.load(f)

        self.validator = Draft202012Validator(self.schema)

    def validate(self, data: dict) -> list[Diagnostic]:
        """
        Validate data against the schema.

        Args:
            data: Dictionary to validate (parsed YAML/JSON manifest)

        Returns:
            List of Diagnostic objects for any validation errors.
            Empty list if validation passes.
        """
        errors = list(self.validator.iter_errors(data))
        return [jsonschema_error_to_diagnostic(e) for e in errors]

    def is_valid(self, data: dict) -> bool:
        """Check if data is valid without collecting errors."""
        return self.validator.is_valid(data)


# ============================================================================
# SECTION 4: Integration Pattern - Schema THEN Pydantic
# ============================================================================


def validate_manifest_integrated(manifest_data: dict) -> list[Diagnostic]:
    """
    Complete manifest validation: Schema first, then Pydantic semantic rules.

    This demonstrates the recommended integration pattern:
    1. First: JSON Schema validation (structural)
       - Required fields, types, patterns, enums, oneOf
       - Fast rejection of malformed manifests
    2. Then: Pydantic validation (semantic)
       - Cross-field validation (exactly one primary hook)
       - Business rules that span multiple fields

    Returns all diagnostics combined.
    """
    diagnostics: list[Diagnostic] = []

    # Step 1: Schema validation (structural)
    schema_validator = SchemaValidator()
    schema_errors = schema_validator.validate(manifest_data)
    diagnostics.extend(schema_errors)

    # If schema validation fails, don't attempt Pydantic parsing
    # (the data structure is invalid)
    if schema_errors:
        return diagnostics

    # Step 2: Pydantic validation (semantic)
    # This would use the actual Manifest model from data-model.md
    # Here we demonstrate with a simplified example
    pydantic_errors = validate_semantic_rules(manifest_data)
    diagnostics.extend(pydantic_errors)

    return diagnostics


def validate_semantic_rules(manifest_data: dict) -> list[Diagnostic]:
    """
    Semantic validation rules that require cross-field checks.

    These rules are better expressed in Pydantic model_validators
    than in JSON Schema.
    """
    diagnostics: list[Diagnostic] = []

    # Example: Validate each frame has exactly one primary hook
    for i, frame in enumerate(manifest_data.get("frames", [])):
        hooks = frame.get("hooks", [])
        primary_hooks = [h for h in hooks if h.get("role") == "primary"]

        if len(primary_hooks) == 0:
            diagnostics.append(
                Diagnostic(
                    rule_id="FRAME-003",
                    severity=Severity.ERROR,
                    message=f"Frame '{frame.get('name')}' has no primary hook",
                    path=f"frames[{i}].hooks",
                    fix="Add exactly one hook with role='primary'",
                )
            )
        elif len(primary_hooks) > 1:
            diagnostics.append(
                Diagnostic(
                    rule_id="FRAME-003",
                    severity=Severity.ERROR,
                    message=f"Frame '{frame.get('name')}' has {len(primary_hooks)} primary hooks (expected 1)",
                    path=f"frames[{i}].hooks",
                    fix="Ensure exactly one hook has role='primary'",
                )
            )

    # Example: Validate hook names match their concept
    for i, frame in enumerate(manifest_data.get("frames", [])):
        for j, hook in enumerate(frame.get("hooks", [])):
            name = hook.get("name", "")
            concept = hook.get("concept", "")

            # Extract concept from hook name pattern: _hk__<concept>[__<qualifier>]
            parts = name.split("__")
            if len(parts) >= 2:
                name_concept = parts[1]
                if name_concept != concept:
                    diagnostics.append(
                        Diagnostic(
                            rule_id="HOOK-007",
                            severity=Severity.WARN,
                            message=f"Hook name concept '{name_concept}' doesn't match concept field '{concept}'",
                            path=f"frames[{i}].hooks[{j}].name",
                            fix=f"Use '_hk__{concept}' or update concept field",
                        )
                    )

    return diagnostics


# ============================================================================
# SECTION 5: Complete Example
# ============================================================================


def demo_complete_validation():
    """Demonstrate complete validation flow."""
    print("\n" + "=" * 80)
    print("COMPLETE VALIDATION DEMO")
    print("=" * 80)

    # Test case 1: Schema error (stops early)
    manifest_with_schema_error = {
        "manifest_version": "invalid",  # MANIFEST-002: pattern
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z",
        },
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__customer",
                        "role": "foreign",
                        "concept": "order",
                        "source": "CRM",
                        "expr": "id",
                    }
                ],
            }
        ],
    }

    print("\n1. Testing manifest with SCHEMA error (early exit):")
    diagnostics = validate_manifest_integrated(manifest_with_schema_error)
    print(f"   Found {len(diagnostics)} diagnostics:\n")
    for d in diagnostics:
        print(f"   {d}\n")

    # Test case 2: Schema passes, semantic errors
    manifest_with_semantic_errors = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z",
        },
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__customer",  # Mismatch with concept
                        "role": "foreign",  # No primary hook!
                        "concept": "order",  # Doesn't match name
                        "source": "CRM",
                        "expr": "id",
                    }
                ],
            }
        ],
    }

    print("\n2. Testing manifest with SEMANTIC errors (schema passes):")
    diagnostics = validate_manifest_integrated(manifest_with_semantic_errors)
    print(f"   Found {len(diagnostics)} diagnostics:\n")
    for d in diagnostics:
        print(f"   {d}\n")

    # Test case 3: Valid manifest
    valid_manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test Manifest",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z",
        },
        "settings": {"hook_prefix": "_hk__", "weak_hook_prefix": "_wk__", "delimiter": "|"},
        "frames": [
            {
                "name": "frame.customer",
                "source": {"relation": "psa.customer"},
                "hooks": [
                    {
                        "name": "_hk__customer",
                        "role": "primary",
                        "concept": "customer",
                        "source": "CRM",
                        "expr": "customer_id",
                    }
                ],
            }
        ],
    }

    print("\n3. Testing valid manifest:")
    diagnostics = validate_manifest_integrated(valid_manifest)

    if not diagnostics:
        print("   ✓ Validation passed! No diagnostics.")
    else:
        print(f"   Found {len(diagnostics)} diagnostics (unexpected)")


def demo_json_output():
    """Demonstrate JSON output format for --json flag."""
    print("\n" + "=" * 80)
    print("JSON OUTPUT FORMAT (for --json flag)")
    print("=" * 80)

    manifest = {
        "manifest_version": "invalid",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z",
        },
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__test",
                        "role": "foreign",  # No primary hook
                        "concept": "test",
                        "source": "TEST",
                        "expr": "id",
                    }
                ],
            }
        ],
    }

    diagnostics = validate_manifest_integrated(manifest)

    errors = [d.model_dump() for d in diagnostics if d.severity == Severity.ERROR]
    warnings = [d.model_dump() for d in diagnostics if d.severity == Severity.WARN]

    output = {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    print("\n" + json.dumps(output, indent=2))


if __name__ == "__main__":
    demo_complete_validation()
    demo_json_output()

    print("\n" + "=" * 80)
    print("Integration Demo Complete!")
    print("=" * 80)
