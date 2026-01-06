# JSON Schema Validation Research

**Date**: 2026-01-06  
**jsonschema Version**: 4.25.1  
**fastjsonschema Version**: 2.21.2  
**Python Version**: 3.12  
**Purpose**: Research JSON Schema validation for HOOK manifest structural validation

---

## Table of Contents

1. [Summary](#summary)
2. [Library Selection](#1-library-selection)
3. [Installation with uv](#2-installation-with-uv)
4. [Loading and Compiling Schema](#3-loading-and-compiling-schema)
5. [Basic Validation](#4-basic-validation)
6. [Collecting All Errors](#5-collecting-all-errors)
7. [Error Path Extraction](#6-error-path-extraction)
8. [Pattern Validation (Regex)](#7-pattern-validation-regex)
9. [oneOf Validation](#8-oneof-validation)
10. [Error to Diagnostic Conversion](#9-error-to-diagnostic-conversion)
11. [Integration Pattern: Schema + Pydantic](#10-integration-pattern-schema--pydantic)
12. [Complete Working Example](#11-complete-working-example)
13. [Recommendation](#12-recommendation)

---

## Summary

| Question | Answer |
|----------|--------|
| **Best library?** | `jsonschema` - full error collection, excellent Draft 2020-12 support |
| **Why not fastjsonschema?** | Only returns first error; we need all errors |
| **Draft 2020-12 support?** | ✅ Yes, via `Draft202012Validator` |
| **Pattern validation?** | ✅ Works correctly for all our patterns |
| **oneOf validation?** | ✅ Works for Source relation XOR path |
| **JSON Schema OR Pydantic?** | **Both** - Schema for structural, Pydantic for semantic |
| **Performance concern?** | No - jsonschema is ~2,000 ops/s, fast enough for CLI |

### Key Findings

| Feature | jsonschema | fastjsonschema |
|---------|-----------|---------------|
| All errors | ✅ `iter_errors()` | ❌ First only |
| Draft 2020-12 | ✅ `Draft202012Validator` | ✅ |
| Error paths | ✅ `absolute_path` | ✅ `path` |
| Performance | ~2,000 ops/s | ~46,000 ops/s |
| Schema compilation | Not needed | Required |
| Error details | Rich context | Basic |

**Verdict**: Use `jsonschema` for validation (all errors), not `fastjsonschema`.

---

## 1. Library Selection

### Options Evaluated

| Library | Pros | Cons | Verdict |
|---------|------|------|---------|
| **jsonschema** | Full Draft 2020-12, all errors, rich error context | Slower than compiled | ✅ **Recommended** |
| **fastjsonschema** | 22x faster, compiled | First error only | ❌ Not suitable |
| **Pydantic alone** | Already using it | Limited schema reuse | ❌ Use alongside |

### Why jsonschema?

1. **All Errors**: `iter_errors()` returns every validation error, not just the first
2. **Draft 2020-12**: Full support via `Draft202012Validator`
3. **Rich Error Context**: Provides path, validator type, schema path, and more
4. **Standard Library Style**: Follows Python conventions, well-maintained
5. **Schema Reuse**: Same schema works in IDEs, docs, other tools

### Why Not fastjsonschema?

```python
# fastjsonschema only returns FIRST error
try:
    validate(invalid_manifest)
except JsonSchemaValueException as e:
    print(e.message)  # Only one error!
```

For validation tools, users expect **all errors at once**, not one at a time.

### Performance Comparison

```
jsonschema:     0.492s for 1000 validations (2,031 ops/s)
fastjsonschema: 0.022s for 1000 validations (45,863 ops/s)
Speedup:        22.6x faster
```

For a CLI tool validating manifests, 2,000 ops/s is more than sufficient. We prioritize **complete error reporting** over raw speed.

---

## 2. Installation with uv

```bash
# Install jsonschema (includes referencing for $ref support)
uv pip install jsonschema

# Or add to pyproject.toml dependencies
# [project]
# dependencies = [
#     "jsonschema>=4.20.0",
# ]
```

**Note**: `jsonschema` automatically installs `referencing` for `$ref` resolution.

---

## 3. Loading and Compiling Schema

### Loading from File

```python
import json
from pathlib import Path
from jsonschema import Draft202012Validator

def load_schema(schema_path: Path) -> dict:
    """Load JSON Schema from file."""
    with open(schema_path) as f:
        return json.load(f)

# Load our manifest schema
schema = load_schema(Path("specs/001-manifest-builder/contracts/manifest-schema.json"))

# Create validator (no explicit compilation needed)
validator = Draft202012Validator(schema)
```

### Verifying Draft Version

```python
# Our schema declares Draft 2020-12
print(schema.get("$schema"))
# Output: https://json-schema.org/draft/2020-12/schema

# Use the matching validator
from jsonschema import Draft202012Validator
validator = Draft202012Validator(schema)
```

---

## 4. Basic Validation

### Simple Validation (Raises on Error)

```python
from jsonschema import validate

# Raises ValidationError if invalid
validate(instance=manifest_data, schema=schema)
```

### Check Validity Without Exception

```python
from jsonschema import Draft202012Validator

validator = Draft202012Validator(schema)

# Returns True/False
if validator.is_valid(manifest_data):
    print("Manifest is valid")
else:
    print("Manifest is invalid")
```

### Validate Python Dict from YAML

```python
import yaml
from pathlib import Path
from jsonschema import Draft202012Validator

def validate_yaml_file(yaml_path: Path, schema: dict) -> bool:
    """Load YAML and validate against schema."""
    with open(yaml_path) as f:
        manifest_data = yaml.safe_load(f)
    
    validator = Draft202012Validator(schema)
    return validator.is_valid(manifest_data)
```

---

## 5. Collecting All Errors

### Using `iter_errors()` (Critical!)

```python
from jsonschema import Draft202012Validator

validator = Draft202012Validator(schema)

# Get ALL validation errors
errors = list(validator.iter_errors(manifest_data))

print(f"Found {len(errors)} errors")
for error in errors:
    print(f"  - {error.message}")
```

### Error Object Properties

Each error provides rich context:

```python
for error in validator.iter_errors(manifest_data):
    print(f"Message: {error.message}")
    print(f"Path: {list(error.absolute_path)}")
    print(f"Schema Path: {list(error.absolute_schema_path)}")
    print(f"Validator: {error.validator}")
    print(f"Validator Value: {error.validator_value}")
    print(f"Instance: {error.instance}")
```

### Example Output

```
Found 6 errors

Error 1:
  Message: 'metadata' is a required property
  Path: []
  Schema Path: ['required']
  Validator: required
  Validator Value: ['manifest_version', 'schema_version', 'metadata', 'settings', 'frames']

Error 2:
  Message: 'invalid-version' does not match '^\d+\.\d+\.\d+$'
  Path: ['manifest_version']
  Schema Path: ['properties', 'manifest_version', 'pattern']
  Validator: pattern
  Validator Value: ^\d+\.\d+\.\d+$
```

---

## 6. Error Path Extraction

### Converting `absolute_path` to JSONPath String

```python
def error_path_to_jsonpath(error) -> str:
    """Convert jsonschema error path to JSONPath-like string."""
    path_parts = list(error.absolute_path)
    
    if not path_parts:
        return "(root)"
    
    json_path = "".join(
        f"[{p}]" if isinstance(p, int) else f".{p}"
        for p in path_parts
    ).lstrip(".")
    
    return json_path
```

### Example Paths for Nested Errors

```python
# Input: error in frames[0].hooks[0].name
# Output: "frames[0].hooks[0].name"

# Input: error in frames[0].hooks[1] (missing fields)
# Output: "frames[0].hooks[1]"

# Input: error at root (missing required field)
# Output: "(root)"
```

### Test Results

```
Path: frames[0].name
Error: 'INVALID_NAME' does not match '^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$'

Path: frames[0].hooks[0].role
Error: 'invalid_role' is not one of ['primary', 'foreign']

Path: frames[0].hooks[1]
Error: 'concept' is a required property
```

---

## 7. Pattern Validation (Regex)

### Our Schema Patterns

| Field | Pattern | Purpose |
|-------|---------|---------|
| `manifest_version` | `^\d+\.\d+\.\d+$` | Semver format |
| `frame.name` | `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` | `schema.table` format |
| `hook.name` | `^_(hk\|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$` | Hook naming |
| `hook.concept` | `^[a-z][a-z0-9_]*$` | lower_snake_case |
| `hook.source` | `^[A-Z][A-Z0-9_]*$` | UPPER_SNAKE_CASE |

### Pattern Validation Tests

All patterns work correctly:

```
✗ 'invalid' (should be semver) → Error: does not match pattern
✓ '1.0.0' (valid semver)
✗ '1.0' (missing patch) → Error: does not match pattern
✗ 'v1.0.0' (has 'v' prefix) → Error: does not match pattern

✓ '_hk__customer' (valid hook name)
✓ '_wk__ref__genre' (valid weak hook)
✓ '_hk__employee__manager' (valid with qualifier)
✗ 'hk__customer' (missing underscore) → Error: does not match pattern
✗ '_hk__Customer' (uppercase) → Error: does not match pattern
```

---

## 8. oneOf Validation

### Source Exclusivity (relation XOR path)

Our schema uses `oneOf` to enforce exactly one of `relation` OR `path`:

```json
{
  "oneOf": [
    { "required": ["relation"], "properties": { "path": false } },
    { "required": ["path"], "properties": { "relation": false } }
  ]
}
```

### Test Results

```
✓ {'relation': 'db.table'} (only relation) → Valid
✓ {'path': '/path/to/file.qvd'} (only path) → Valid
✗ {'relation': 'db.table', 'path': '/path'} (both) → Error: not valid under any schema
✗ {} (neither) → Error: not valid under any schema
```

### oneOf Error Messages

```python
# When both are provided or neither:
error.message = "{'relation': 'db.table', 'path': '/path'} is not valid under any of the given schemas"
error.validator = "oneOf"
```

**Note**: The error message is not very user-friendly. We improve this in our error-to-diagnostic mapping.

---

## 9. Error to Diagnostic Conversion

### Mapping Validators to Rule IDs

```python
def _map_error_to_rule_id(error, json_path: str) -> str:
    """Map JSON Schema validation errors to our rule IDs."""
    validator = error.validator
    
    if validator == "required":
        if "hooks" in json_path:
            return "HOOK-001"
        elif "frames" in json_path:
            return "FRAME-001"
        return "MANIFEST-001"
    
    elif validator == "pattern":
        if "manifest_version" in json_path:
            return "MANIFEST-002"
        elif "hooks" in json_path and ".name" in json_path:
            return "HOOK-002"
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
        if "hooks" in json_path:
            return "FRAME-003"
        elif "frames" in json_path:
            return "MANIFEST-004"
        return "SCHEMA-MIN-ITEMS"
    
    return f"SCHEMA-{validator.upper()}"
```

### Building Human-Friendly Fix Messages

```python
def _build_fix_message(error, json_path: str) -> str:
    """Build a helpful fix message based on error type."""
    validator = error.validator
    
    if validator == "required":
        missing = error.message.split("'")[1]
        return f"Add required field '{missing}'"
    
    elif validator == "pattern":
        if "manifest_version" in json_path:
            return "Use semver format: MAJOR.MINOR.PATCH (e.g., '1.0.0')"
        elif "hooks" in json_path and ".name" in json_path:
            return "Use format: _hk__<concept> or _wk__<concept>[__<qualifier>]"
        return f"Value must match pattern: {error.validator_value}"
    
    elif validator == "enum":
        allowed = ", ".join(repr(v) for v in error.validator_value)
        return f"Use one of: {allowed}"
    
    elif validator == "oneOf":
        if "source" in json_path:
            return "Provide exactly one of 'relation' OR 'path', not both or neither"
        return "Value must match exactly one of the allowed schemas"
    
    return f"Check value at '{json_path}'"
```

### Complete Conversion Function

```python
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"

class Diagnostic(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    rule_id: str
    severity: Severity
    message: str
    path: str
    fix: str

def jsonschema_error_to_diagnostic(error) -> Diagnostic:
    """Convert a jsonschema ValidationError to our Diagnostic format."""
    # Build JSONPath
    path_parts = list(error.absolute_path)
    json_path = "".join(
        f"[{p}]" if isinstance(p, int) else f".{p}"
        for p in path_parts
    ).lstrip(".") or "(root)"
    
    return Diagnostic(
        rule_id=_map_error_to_rule_id(error, json_path),
        severity=Severity.ERROR,
        message=error.message,
        path=json_path,
        fix=_build_fix_message(error, json_path)
    )
```

---

## 10. Integration Pattern: Schema + Pydantic

### Recommended Approach: **Both**

| Layer | Tool | Responsibility |
|-------|------|----------------|
| **Structural** | JSON Schema | Required fields, types, patterns, enums, oneOf |
| **Semantic** | Pydantic | Cross-field validation, business rules |

### Why Both?

1. **JSON Schema** catches malformed data quickly with clear error paths
2. **Pydantic** excels at cross-field validation (e.g., exactly one primary hook)
3. **Schema-first** means we can share the schema with IDEs, docs, other tools
4. **Early exit** on schema errors avoids confusing Pydantic errors

### Validation Flow

```
                    ┌──────────────────┐
    YAML/JSON ─────►│  JSON Schema     │──── Schema Errors ────► Diagnostics
    Manifest        │  (structural)    │
                    └────────┬─────────┘
                             │ (if valid)
                             ▼
                    ┌──────────────────┐
                    │  Pydantic        │──── Semantic Errors ──► Diagnostics
                    │  (semantic)      │
                    └────────┬─────────┘
                             │ (if valid)
                             ▼
                       Valid Manifest
```

### Implementation Pattern

```python
def validate_manifest(manifest_data: dict) -> list[Diagnostic]:
    """Complete manifest validation: Schema first, then Pydantic."""
    diagnostics: list[Diagnostic] = []
    
    # Step 1: JSON Schema validation (structural)
    schema_validator = SchemaValidator()
    schema_errors = schema_validator.validate(manifest_data)
    diagnostics.extend(schema_errors)
    
    # If schema fails, don't attempt Pydantic
    # (the data structure is invalid for parsing)
    if schema_errors:
        return diagnostics
    
    # Step 2: Pydantic validation (semantic)
    # Parse into Pydantic models (may raise ValidationError)
    # Then run semantic validators
    semantic_errors = validate_semantic_rules(manifest_data)
    diagnostics.extend(semantic_errors)
    
    return diagnostics
```

### What Goes Where?

| Validation Rule | Tool | Reason |
|-----------------|------|--------|
| Required fields | JSON Schema | Built-in `required` |
| Type checking | JSON Schema | Built-in `type` |
| String patterns (semver, snake_case) | JSON Schema | Built-in `pattern` |
| Enum values (role) | JSON Schema | Built-in `enum` |
| Exclusive fields (relation XOR path) | JSON Schema | Built-in `oneOf` |
| Array min/max items | JSON Schema | Built-in `minItems` |
| Exactly one primary hook per frame | **Pydantic** | Cross-field, needs iteration |
| Hook name matches concept | **Pydantic** | Cross-field comparison |
| Concept used in frames exists | **Pydantic** | Cross-entity reference |
| No duplicate frame names | **Pydantic** | Collection-wide check |

---

## 11. Complete Working Example

### SchemaValidator Class

```python
import json
from pathlib import Path
from jsonschema import Draft202012Validator

class SchemaValidator:
    """JSON Schema validator for HOOK manifests."""
    
    def __init__(self, schema_path: Path | None = None):
        if schema_path is None:
            schema_path = Path("specs/001-manifest-builder/contracts/manifest-schema.json")
        
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        self.validator = Draft202012Validator(self.schema)
    
    def validate(self, data: dict) -> list[Diagnostic]:
        """Validate data, returning list of Diagnostics."""
        errors = list(self.validator.iter_errors(data))
        return [jsonschema_error_to_diagnostic(e) for e in errors]
    
    def is_valid(self, data: dict) -> bool:
        """Quick validity check."""
        return self.validator.is_valid(data)
```

### Semantic Validator (Pydantic)

```python
def validate_semantic_rules(manifest_data: dict) -> list[Diagnostic]:
    """Semantic validation requiring cross-field checks."""
    diagnostics: list[Diagnostic] = []
    
    # Rule: Each frame must have exactly one primary hook
    for i, frame in enumerate(manifest_data.get("frames", [])):
        hooks = frame.get("hooks", [])
        primary_hooks = [h for h in hooks if h.get("role") == "primary"]
        
        if len(primary_hooks) == 0:
            diagnostics.append(Diagnostic(
                rule_id="FRAME-003",
                severity=Severity.ERROR,
                message=f"Frame '{frame.get('name')}' has no primary hook",
                path=f"frames[{i}].hooks",
                fix="Add exactly one hook with role='primary'"
            ))
        elif len(primary_hooks) > 1:
            diagnostics.append(Diagnostic(
                rule_id="FRAME-003",
                severity=Severity.ERROR,
                message=f"Frame '{frame.get('name')}' has {len(primary_hooks)} primary hooks",
                path=f"frames[{i}].hooks",
                fix="Ensure exactly one hook has role='primary'"
            ))
    
    return diagnostics
```

### Complete Usage

```python
def validate_manifest_file(yaml_path: Path) -> tuple[bool, list[Diagnostic]]:
    """Validate a YAML manifest file completely."""
    import yaml
    
    # Load YAML
    with open(yaml_path) as f:
        manifest_data = yaml.safe_load(f)
    
    # Validate
    diagnostics = validate_manifest(manifest_data)
    
    # Check for errors (not just warnings)
    has_errors = any(d.severity == Severity.ERROR for d in diagnostics)
    
    return (not has_errors, diagnostics)


# Example usage
valid, diagnostics = validate_manifest_file(Path("manifest.yaml"))

if valid:
    print("✓ Manifest is valid")
else:
    print("✗ Validation failed:")
    for d in diagnostics:
        print(f"\n{d.severity.value} [{d.rule_id}] {d.message}")
        print(f"  at: {d.path}")
        print(f"  fix: {d.fix}")
```

### JSON Output Format

```python
def format_diagnostics_json(diagnostics: list[Diagnostic]) -> str:
    """Format diagnostics as JSON for --json flag."""
    errors = [d.model_dump() for d in diagnostics if d.severity == Severity.ERROR]
    warnings = [d.model_dump() for d in diagnostics if d.severity == Severity.WARN]
    
    output = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
    
    return json.dumps(output, indent=2)
```

**Output**:

```json
{
  "valid": false,
  "errors": [
    {
      "rule_id": "MANIFEST-002",
      "severity": "ERROR",
      "message": "'invalid' does not match '^\\d+\\.\\d+\\.\\d+$'",
      "path": "manifest_version",
      "fix": "Use semver format: MAJOR.MINOR.PATCH (e.g., '1.0.0')"
    }
  ],
  "warnings": []
}
```

---

## 12. Recommendation

### Final Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Manifest Validation                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. YAML Parsing (ruamel.yaml)                                  │
│     └── Syntax errors → Diagnostic                              │
│                                                                  │
│  2. JSON Schema Validation (jsonschema)                         │
│     ├── Required fields                                         │
│     ├── Type checking                                           │
│     ├── Pattern validation (semver, snake_case)                 │
│     ├── Enum values (role: primary/foreign)                     │
│     ├── oneOf (relation XOR path)                               │
│     └── Array constraints (minItems)                            │
│     └── Errors → Diagnostic (with rule_id mapping)              │
│                                                                  │
│  3. Pydantic Semantic Validation                                │
│     ├── Exactly one primary hook per frame                      │
│     ├── Hook name matches concept                               │
│     ├── Concept references are valid                            │
│     ├── No duplicate frame names                                │
│     └── Business rule validations                               │
│     └── Errors → Diagnostic                                     │
│                                                                  │
│  4. All Diagnostics Combined                                    │
│     ├── Human-readable output (default)                         │
│     └── JSON output (--json flag)                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary library | `jsonschema` | All errors, rich context, Draft 2020-12 |
| Error collection | `iter_errors()` | Returns all errors, not just first |
| Schema draft | Draft 2020-12 | Modern, matches our schema `$schema` |
| Pydantic role | Semantic validation | Cross-field rules that JSON Schema can't express |
| Validation order | Schema → Pydantic | Early exit on structural errors |
| Error format | Custom Diagnostic | Matches spec requirements (FR-016) |

### Dependencies to Add

```toml
[project]
dependencies = [
    "jsonschema>=4.20.0",
    "pydantic>=2.0.0",
    "ruamel.yaml>=0.18.0",
]
```

### Files to Create

```
src/dot/
├── validation/
│   ├── __init__.py
│   ├── schema_validator.py    # JSON Schema validation
│   ├── semantic_validator.py  # Pydantic cross-field rules
│   └── validator.py           # Combined validation entry point
└── models/
    └── diagnostic.py          # Diagnostic model (already defined)
```

---

## Appendix: Test Scripts

The following test scripts were created during this research:

1. **[json-schema-validation-test.py](json-schema-validation-test.py)**: Core jsonschema and fastjsonschema exploration
2. **[json-schema-integration-test.py](json-schema-integration-test.py)**: Complete integration pattern with Pydantic

Both scripts validate against the actual [manifest-schema.json](../contracts/manifest-schema.json) and demonstrate all features documented above.
