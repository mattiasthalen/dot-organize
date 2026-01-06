#!/usr/bin/env python3
"""
JSON Schema Validation Research Script

Testing jsonschema and fastjsonschema libraries for HOOK manifest validation.
"""

import json
from pathlib import Path
from typing import Any
from datetime import datetime

# Load our actual schema
SCHEMA_PATH = Path(__file__).parent.parent / "contracts" / "manifest-schema.json"

def load_schema() -> dict:
    """Load the HOOK manifest schema."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)

# ============================================================================
# SECTION 1: jsonschema library exploration
# ============================================================================

def test_jsonschema_basic():
    """Test basic jsonschema validation."""
    print("\n" + "="*80)
    print("SECTION 1: jsonschema Basic Validation")
    print("="*80)
    
    import jsonschema
    from jsonschema import Draft202012Validator, ValidationError, validate
    
    schema = load_schema()
    
    # Check which draft is supported
    print(f"\n1.1 jsonschema version: {jsonschema.__version__}")
    print(f"    Schema $schema: {schema.get('$schema')}")
    
    # Simple validation - valid manifest
    valid_manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test Manifest",
            "description": "Test description",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z"
        },
        "settings": {
            "hook_prefix": "_hk__",
            "weak_hook_prefix": "_wk__",
            "delimiter": "|"
        },
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
                        "expr": "customer_id"
                    }
                ]
            }
        ]
    }
    
    print("\n1.2 Validating a correct manifest...")
    try:
        validate(instance=valid_manifest, schema=schema)
        print("    ✓ Validation passed!")
    except ValidationError as e:
        print(f"    ✗ Validation failed: {e.message}")
    
    return schema


def test_jsonschema_error_collection():
    """Test collecting all validation errors."""
    print("\n" + "="*80)
    print("SECTION 2: Collecting ALL Validation Errors")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    # Create a manifest with multiple errors
    invalid_manifest = {
        "manifest_version": "invalid-version",  # Should be semver
        "schema_version": "1.0",  # Should be semver (3 parts)
        # Missing: metadata
        "settings": {
            "hook_prefix": "",  # Empty string (minLength: 1)
            "delimiter": "||"   # Too long (maxLength: 1)
        },
        "frames": []  # Empty array (minItems: 1)
    }
    
    print("\n2.1 Getting all errors (not just first):")
    errors = list(validator.iter_errors(invalid_manifest))
    print(f"    Found {len(errors)} errors\n")
    
    for i, error in enumerate(errors, 1):
        print(f"    Error {i}:")
        print(f"      Message: {error.message}")
        print(f"      Path: {list(error.absolute_path)}")
        print(f"      Schema Path: {list(error.absolute_schema_path)}")
        print(f"      Validator: {error.validator}")
        print(f"      Validator Value: {error.validator_value}")
        print()
    
    return errors


def test_jsonschema_error_paths():
    """Test extracting paths for nested errors."""
    print("\n" + "="*80)
    print("SECTION 3: Error Paths for Nested Structures")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    # Manifest with errors in nested hooks
    manifest_with_hook_errors = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z"
        },
        "settings": {},
        "frames": [
            {
                "name": "INVALID_NAME",  # Should be lowercase with dot
                "source": {"relation": "psa.customer"},
                "hooks": [
                    {
                        "name": "wrong_hook_name",  # Should match hook pattern
                        "role": "invalid_role",      # Should be primary/foreign
                        "concept": "WRONG_CASE",     # Should be lowercase
                        "source": "lowercase",       # Should be UPPERCASE
                        "expr": "id"
                    },
                    {
                        "name": "_hk__order",
                        "role": "foreign",
                        # Missing: concept, source, expr
                    }
                ]
            }
        ]
    }
    
    print("\n3.1 Nested errors with full paths:")
    errors = list(validator.iter_errors(manifest_with_hook_errors))
    
    for error in errors:
        # Convert path to JSONPath-like string
        path_parts = list(error.absolute_path)
        if path_parts:
            json_path = "".join(
                f"[{p}]" if isinstance(p, int) else f".{p}"
                for p in path_parts
            ).lstrip(".")
        else:
            json_path = "(root)"
        
        print(f"    Path: {json_path}")
        print(f"    Error: {error.message}")
        print(f"    Validator: {error.validator}")
        print()


def test_jsonschema_pattern_validation():
    """Test regex pattern validation."""
    print("\n" + "="*80)
    print("SECTION 4: Pattern (Regex) Validation")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    # Test various pattern violations
    test_cases = [
        ("manifest_version", "invalid", "should be semver"),
        ("manifest_version", "1.0.0", "valid semver"),
        ("manifest_version", "1.0", "missing patch version"),
        ("manifest_version", "v1.0.0", "has 'v' prefix"),
    ]
    
    print("\n4.1 Testing manifest_version patterns:")
    for field, value, description in test_cases:
        test_doc = {
            field: value,
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test",
                "created_at": "2026-01-04T00:00:00Z",
                "updated_at": "2026-01-04T00:00:00Z"
            },
            "settings": {},
            "frames": [
                {
                    "name": "frame.test",
                    "source": {"relation": "test"},
                    "hooks": [
                        {
                            "name": "_hk__test",
                            "role": "primary",
                            "concept": "test",
                            "source": "TEST",
                            "expr": "id"
                        }
                    ]
                }
            ]
        }
        errors = [e for e in validator.iter_errors(test_doc) if field in str(e.absolute_path)]
        status = "✓" if not errors else "✗"
        print(f"    {status} '{value}' ({description})")
        if errors:
            print(f"        Error: {errors[0].message}")
    
    print("\n4.2 Testing hook name patterns:")
    hook_names = [
        ("_hk__customer", True),
        ("_wk__ref__genre", True),
        ("_hk__employee__manager", True),
        ("hk__customer", False),           # Missing leading underscore
        ("_hk_customer", False),            # Only one underscore after hk
        ("_hk__Customer", False),           # Uppercase
        ("_hk__123", False),                # Starts with number
    ]
    
    for hook_name, expected_valid in hook_names:
        test_doc = {
            "manifest_version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test",
                "created_at": "2026-01-04T00:00:00Z",
                "updated_at": "2026-01-04T00:00:00Z"
            },
            "settings": {},
            "frames": [
                {
                    "name": "frame.test",
                    "source": {"relation": "test"},
                    "hooks": [
                        {
                            "name": hook_name,
                            "role": "primary",
                            "concept": "test",
                            "source": "TEST",
                            "expr": "id"
                        }
                    ]
                }
            ]
        }
        errors = [e for e in validator.iter_errors(test_doc) 
                  if "name" in str(e.absolute_path) and "pattern" in str(e.validator)]
        is_valid = len(errors) == 0
        status = "✓" if is_valid == expected_valid else "✗ UNEXPECTED"
        expected = "valid" if expected_valid else "invalid"
        print(f"    {status} '{hook_name}' (expected: {expected})")


def test_jsonschema_oneof():
    """Test oneOf validation for Source (relation XOR path)."""
    print("\n" + "="*80)
    print("SECTION 5: oneOf Validation (relation XOR path)")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    def make_manifest(source: dict) -> dict:
        return {
            "manifest_version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {
                "name": "Test",
                "created_at": "2026-01-04T00:00:00Z",
                "updated_at": "2026-01-04T00:00:00Z"
            },
            "settings": {},
            "frames": [
                {
                    "name": "frame.test",
                    "source": source,
                    "hooks": [
                        {
                            "name": "_hk__test",
                            "role": "primary",
                            "concept": "test",
                            "source": "TEST",
                            "expr": "id"
                        }
                    ]
                }
            ]
        }
    
    test_cases = [
        ({"relation": "db.table"}, True, "only relation"),
        ({"path": "/path/to/file.qvd"}, True, "only path"),
        ({"relation": "db.table", "path": "/path/file"}, False, "both relation and path"),
        ({}, False, "neither relation nor path"),
    ]
    
    print("\n5.1 Testing Source oneOf validation:")
    for source, expected_valid, description in test_cases:
        manifest = make_manifest(source)
        errors = list(validator.iter_errors(manifest))
        # Filter to source-related errors
        source_errors = [e for e in errors 
                        if "source" in str(e.absolute_path) or "oneOf" in str(e.validator)]
        is_valid = len(source_errors) == 0
        status = "✓" if is_valid == expected_valid else "✗ UNEXPECTED"
        print(f"    {status} {source} ({description})")
        if source_errors:
            for err in source_errors:
                print(f"        Error: {err.message[:80]}...")


def test_fastjsonschema():
    """Test fastjsonschema library."""
    print("\n" + "="*80)
    print("SECTION 6: fastjsonschema Library")
    print("="*80)
    
    import fastjsonschema
    from fastjsonschema import JsonSchemaValueException
    from importlib.metadata import version
    
    schema = load_schema()
    
    print(f"\n6.1 fastjsonschema version: {version('fastjsonschema')}")
    
    # Compile the schema
    print("\n6.2 Compiling schema...")
    try:
        validate = fastjsonschema.compile(schema)
        print("    ✓ Schema compiled successfully")
    except Exception as e:
        print(f"    ✗ Compilation failed: {e}")
        return
    
    # Test valid manifest
    valid_manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z"
        },
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__test",
                        "role": "primary",
                        "concept": "test",
                        "source": "TEST",
                        "expr": "id"
                    }
                ]
            }
        ]
    }
    
    print("\n6.3 Testing valid manifest:")
    try:
        validate(valid_manifest)
        print("    ✓ Validation passed")
    except JsonSchemaValueException as e:
        print(f"    ✗ Validation failed: {e.message}")
    
    # Test invalid manifest
    invalid_manifest = {
        "manifest_version": "invalid",
        "schema_version": "1.0.0",
        "metadata": {"name": "Test", "created_at": "2026-01-04T00:00:00Z", "updated_at": "2026-01-04T00:00:00Z"},
        "settings": {},
        "frames": []
    }
    
    print("\n6.4 Testing invalid manifest (fastjsonschema only returns FIRST error):")
    try:
        validate(invalid_manifest)
        print("    ✓ Validation passed (unexpected)")
    except JsonSchemaValueException as e:
        print(f"    ✗ Error: {e.message}")
        print(f"      Path: {e.path}")
        print(f"      Rule: {e.rule}")
        print(f"      Rule definition: {e.rule_definition}")


def test_performance():
    """Compare performance of jsonschema vs fastjsonschema."""
    print("\n" + "="*80)
    print("SECTION 7: Performance Comparison")
    print("="*80)
    
    import time
    import jsonschema
    from jsonschema import Draft202012Validator
    import fastjsonschema
    
    schema = load_schema()
    
    valid_manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {
            "name": "Test",
            "created_at": "2026-01-04T00:00:00Z",
            "updated_at": "2026-01-04T00:00:00Z"
        },
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__test",
                        "role": "primary",
                        "concept": "test",
                        "source": "TEST",
                        "expr": "id"
                    }
                ]
            }
        ]
    }
    
    iterations = 1000
    
    # jsonschema
    validator = Draft202012Validator(schema)
    start = time.perf_counter()
    for _ in range(iterations):
        list(validator.iter_errors(valid_manifest))
    jsonschema_time = time.perf_counter() - start
    
    # fastjsonschema
    validate_fast = fastjsonschema.compile(schema)
    start = time.perf_counter()
    for _ in range(iterations):
        try:
            validate_fast(valid_manifest)
        except:
            pass
    fastjsonschema_time = time.perf_counter() - start
    
    print(f"\n7.1 Performance ({iterations} validations):")
    print(f"    jsonschema:     {jsonschema_time:.3f}s ({iterations/jsonschema_time:.0f} ops/s)")
    print(f"    fastjsonschema: {fastjsonschema_time:.3f}s ({iterations/fastjsonschema_time:.0f} ops/s)")
    print(f"    Speedup:        {jsonschema_time/fastjsonschema_time:.1f}x faster")


def test_best_format_errors():
    """Test the best_match helper for better error formatting."""
    print("\n" + "="*80)
    print("SECTION 8: Better Error Formatting with best_match")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import best_match
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    invalid_manifest = {
        "manifest_version": "invalid",
        "schema_version": "1.0.0",
        "metadata": {"name": "Test", "created_at": "2026-01-04T00:00:00Z", "updated_at": "2026-01-04T00:00:00Z"},
        "settings": {},
        "frames": [
            {
                "name": "INVALID",
                "source": {},  # Missing both relation and path
                "hooks": []
            }
        ]
    }
    
    print("\n8.1 Using best_match for most relevant error:")
    errors = list(validator.iter_errors(invalid_manifest))
    best = best_match(errors)
    if best:
        print(f"    Best match: {best.message}")
        print(f"    Path: {list(best.absolute_path)}")
    
    print("\n8.2 All errors formatted as Diagnostic-compatible:")
    for error in sorted(errors, key=lambda e: list(e.absolute_path)):
        path_parts = list(error.absolute_path)
        json_path = "".join(
            f"[{p}]" if isinstance(p, int) else f".{p}"
            for p in path_parts
        ).lstrip(".") or "(root)"
        
        # Determine a rule_id based on error type
        if error.validator == "pattern":
            if "manifest_version" in json_path or "schema_version" in json_path:
                rule_id = "MANIFEST-001"
            elif "hooks" in json_path and "name" in json_path:
                rule_id = "HOOK-002"
            elif "frames" in json_path and json_path.endswith(".name"):
                rule_id = "FRAME-002"
            else:
                rule_id = "SCHEMA-PATTERN"
        elif error.validator == "required":
            rule_id = "SCHEMA-REQUIRED"
        elif error.validator == "oneOf":
            rule_id = "SCHEMA-ONEOF"
        elif error.validator == "enum":
            rule_id = "SCHEMA-ENUM"
        elif error.validator == "minItems":
            rule_id = "SCHEMA-MIN-ITEMS"
        else:
            rule_id = f"SCHEMA-{error.validator.upper()}"
        
        print(f"    rule_id:  {rule_id}")
        print(f"    severity: ERROR")
        print(f"    message:  {error.message}")
        print(f"    path:     {json_path}")
        print(f"    fix:      Check value at '{json_path}'")
        print()


def test_error_context():
    """Test getting context from errors for better messages."""
    print("\n" + "="*80)
    print("SECTION 9: Error Context for Human-Readable Messages")
    print("="*80)
    
    from jsonschema import Draft202012Validator
    
    schema = load_schema()
    validator = Draft202012Validator(schema)
    
    invalid_manifest = {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "metadata": {"name": "Test", "created_at": "2026-01-04T00:00:00Z", "updated_at": "2026-01-04T00:00:00Z"},
        "settings": {},
        "frames": [
            {
                "name": "frame.test",
                "source": {"relation": "test"},
                "hooks": [
                    {
                        "name": "_hk__test",
                        "role": "invalid_role",  # Should be primary/foreign
                        "concept": "test",
                        "source": "TEST",
                        "expr": "id"
                    }
                ]
            }
        ]
    }
    
    print("\n9.1 Error details for enum violation:")
    errors = list(validator.iter_errors(invalid_manifest))
    for error in errors:
        if error.validator == "enum":
            print(f"    Validator: {error.validator}")
            print(f"    Invalid value: {error.instance!r}")
            print(f"    Allowed values: {error.validator_value}")
            print(f"    Path: {list(error.absolute_path)}")
            print(f"    Schema path: {list(error.absolute_schema_path)}")
            
            # Build human-readable message
            allowed = ", ".join(repr(v) for v in error.validator_value)
            human_msg = f"Invalid role '{error.instance}': must be one of {allowed}"
            print(f"    Human message: {human_msg}")


if __name__ == "__main__":
    test_jsonschema_basic()
    test_jsonschema_error_collection()
    test_jsonschema_error_paths()
    test_jsonschema_pattern_validation()
    test_jsonschema_oneof()
    test_fastjsonschema()
    test_performance()
    test_best_format_errors()
    test_error_context()
    
    print("\n" + "="*80)
    print("Research Complete!")
    print("="*80)
