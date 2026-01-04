# Data Model: HOOK Manifest Builder

**Feature**: 001-manifest-builder  
**Created**: 2026-01-04  
**Spec Reference**: [spec.md](spec.md)

---

## Overview

This document defines the complete data model for the HOOK manifest. All models use Pydantic v2 with `frozen=True` for immutability.

**Design Principles**:
- Immutable data structures (frozen Pydantic models)
- Pure functions for all transformations
- Explicit optionality (no implicit defaults hidden in logic)
- Auto-derivation over manual declaration (key sets, concept registry)

---

## Entity Relationship

```text
Manifest (root)
├── metadata: Metadata
├── settings: Settings
├── frames: list[Frame]
│   └── hooks: list[Hook]
├── concepts: list[Concept]  (optional)
└── targets: Targets
```

---

## Models

### 1. Manifest (Root)

**File**: `src/hook/models/manifest.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1)

```python
class Manifest(BaseModel, frozen=True):
    manifest_version: str          # Required. Semver string (e.g., "1.0.0")
    schema_version: str            # Required. Manifest schema version (e.g., "1.0.0")
    metadata: Metadata             # Required. Name, description, timestamps
    settings: Settings             # Required. Hook prefixes, delimiter
    frames: list[Frame]            # Required. At least one frame
    concepts: list[Concept] = []   # Optional. Enrichment definitions
    targets: Targets               # Required. Extension points (empty in v1)
```

| Field | Type | Required | Default | Validation | Spec Reference |
|-------|------|----------|---------|------------|----------------|
| `manifest_version` | `str` | ✅ | — | Valid semver (MANIFEST-001) | FR-030 |
| `schema_version` | `str` | ✅ | — | Valid semver (MANIFEST-002) | FR-031 |
| `metadata` | `Metadata` | ✅ | — | — | FR-030 |
| `settings` | `Settings` | ✅ | — | — | FR-038 |
| `frames` | `list[Frame]` | ✅ | — | len >= 1 | FR-032 |
| `concepts` | `list[Concept]` | ❌ | `[]` | — | FR-037 |
| `targets` | `Targets` | ✅ | — | — | FR-039 |

---

### 2. Metadata

**File**: `src/hook/models/manifest.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1)

```python
class Metadata(BaseModel, frozen=True):
    name: str                      # Required. Human-readable name
    description: str | None = None # Optional. Description
    created_at: datetime           # Required. ISO 8601 timestamp
    updated_at: datetime           # Required. ISO 8601 timestamp
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `name` | `str` | ✅ | — | Non-empty |
| `description` | `str \| None` | ❌ | `None` | — |
| `created_at` | `datetime` | ✅ | — | ISO 8601 format |
| `updated_at` | `datetime` | ✅ | — | ISO 8601 format |

---

### 3. Settings

**File**: `src/hook/models/settings.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1), FR-038

```python
class Settings(BaseModel, frozen=True):
    hook_prefix: str = "_hk__"           # Default prefix for strong hooks
    weak_hook_prefix: str = "_wk__"      # Default prefix for weak hooks
    delimiter: str = "|"                 # Separates key set from business key
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `hook_prefix` | `str` | ❌ | `"_hk__"` | Non-empty |
| `weak_hook_prefix` | `str` | ❌ | `"_wk__"` | Non-empty |
| `delimiter` | `str` | ❌ | `"\|"` | Single character |

---

### 4. Frame

**File**: `src/hook/models/frame.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1), FR-032, FR-033

```python
class Frame(BaseModel, frozen=True):
    name: str                      # Required. Frame name (e.g., "frame.customer")
    source: str                    # Required. Source table reference (e.g., "psa.customer")
    description: str | None = None # Optional. Description
    hooks: list[Hook]              # Required. At least one hook
```

| Field | Type | Required | Default | Validation | Rule ID |
|-------|------|----------|---------|------------|---------|
| `name` | `str` | ✅ | — | `lower_snake_case`, pattern: `<schema>.<table>` | FRAME-002 |
| `source` | `str` | ✅ | — | Non-empty | FRAME-004 |
| `description` | `str \| None` | ❌ | `None` | — | — |
| `hooks` | `list[Hook]` | ✅ | — | len >= 1, exactly one `role="primary"` | FRAME-001, FRAME-003 |

**Naming Pattern**: `<schema>.<table>` in lower_snake_case  
**Examples**: `frame.customer`, `psa.order_header`, `staging.invoice_line`

---

### 5. Hook

**File**: `src/hook/models/frame.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1), FR-034, FR-035

```python
class HookRole(str, Enum):
    PRIMARY = "primary"    # Defines frame grain
    FOREIGN = "foreign"    # References other concept

class Hook(BaseModel, frozen=True):
    name: str                      # Required. Hook column name (e.g., "_hk__customer")
    role: HookRole                 # Required. "primary" or "foreign"
    concept: str                   # Required. Business concept (e.g., "customer")
    qualifier: str | None = None   # Optional. Qualifier suffix (e.g., "manager")
    source: str                    # Required. Source system (e.g., "CRM")
    tenant: str | None = None      # Optional. Tenant (e.g., "AU")
    expr_sql: str                  # Required. SQL expression for business key
    treatment: str | None = None   # Optional. Transformation (e.g., "TRIM|UPPER")
```

| Field | Type | Required | Default | Validation | Rule ID |
|-------|------|----------|---------|------------|---------|
| `name` | `str` | ✅ | — | Pattern: `<prefix><concept>[__<qualifier>]` | HOOK-002 |
| `role` | `HookRole` | ✅ | — | `"primary"` or `"foreign"` | HOOK-003 |
| `concept` | `str` | ✅ | — | `lower_snake_case` | HOOK-004 |
| `qualifier` | `str \| None` | ❌ | `None` | `lower_snake_case` if present | HOOK-004 |
| `source` | `str` | ✅ | — | `UPPER_SNAKE_CASE` | HOOK-005 |
| `tenant` | `str \| None` | ❌ | `None` | `UPPER_SNAKE_CASE` if present | HOOK-005 |
| `expr_sql` | `str` | ✅ | — | Pure SQL expression, no SELECT/JOIN | HOOK-006, HOOK-007 |
| `treatment` | `str \| None` | ❌ | `None` | Valid treatment syntax | HOOK-007 |

**Hook Name Pattern**: `<prefix><concept>[__<qualifier>]`
- Strong: `_hk__customer`, `_hk__employee__manager`
- Weak: `_wk__ref__genre`, `_wk__epoch__dob`

**Auto-Derived Key Set**: `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]`
- Examples: `CUSTOMER@CRM`, `EMPLOYEE~MANAGER@CRM`, `ORDER@SAP~AU`

---

### 6. Concept

**File**: `src/hook/models/concept.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1), FR-037

```python
class Concept(BaseModel, frozen=True):
    name: str                      # Required. Must match a concept used in frames
    description: str               # Required. 1-2 sentence definition
    examples: list[str] = []       # Optional. Real-world examples
    is_weak: bool = False          # Optional. True for reference/time concepts
```

| Field | Type | Required | Default | Validation | Rule ID |
|-------|------|----------|---------|------------|---------|
| `name` | `str` | ✅ | — | Must match hook concept | CONCEPT-001 |
| `description` | `str` | ✅ | — | 1-2 sentences | CONCEPT-002 |
| `examples` | `list[str]` | ❌ | `[]` | — | — |
| `is_weak` | `bool` | ❌ | `False` | — | — |

---

### 7. Targets (Extension Points)

**File**: `src/hook/models/manifest.py`  
**Spec Reference**: [spec.md#manifest-schema-v1](spec.md#manifest-schema-v1), FR-039, FR-040

```python
class Targets(BaseModel, frozen=True):
    hook_sql: dict[str, Any] = {}  # Reserved for HOOK SQL generator
    uss_sql: dict[str, Any] = {}   # Reserved for USS SQL generator
    qlik: dict[str, Any] = {}      # Reserved for Qlik generator
```

| Field | Type | Required | Default | Validation | Rule ID |
|-------|------|----------|---------|------------|---------|
| `hook_sql` | `dict` | ❌ | `{}` | Allowed but ignored in v1 | TARGET-W01 |
| `uss_sql` | `dict` | ❌ | `{}` | Allowed but ignored in v1 | TARGET-W01 |
| `qlik` | `dict` | ❌ | `{}` | Allowed but ignored in v1 | TARGET-W01 |

---

### 8. Diagnostic

**File**: `src/hook/models/diagnostic.py`  
**Spec Reference**: [spec.md#diagnostic-format](spec.md#diagnostic-format), FR-016

```python
class Severity(str, Enum):
    ERROR = "ERROR"    # Exit code 1
    WARN = "WARN"      # Exit code 0, but reported

class Diagnostic(BaseModel, frozen=True):
    rule_id: str                   # Required. Stable identifier (e.g., "HOOK-001")
    severity: Severity             # Required. ERROR or WARN
    message: str                   # Required. Human-readable message
    path: str                      # Required. JSONPath to offending field
    fix: str                       # Required. Suggested fix
```

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `rule_id` | `str` | ✅ | — | Pattern: `<ENTITY>-[W]<NNN>` |
| `severity` | `Severity` | ✅ | — | `ERROR` or `WARN` |
| `message` | `str` | ✅ | — | Non-empty |
| `path` | `str` | ✅ | — | Valid JSONPath |
| `fix` | `str` | ✅ | — | Non-empty |

---

## Auto-Derived Registries

These are computed from the manifest, not stored:

**File**: `src/hook/core/registry.py`

### Key Set Registry

```python
def derive_key_sets(manifest: Manifest) -> set[str]:
    """
    Derive unique key sets from all hooks.
    
    Pattern: CONCEPT[~QUALIFIER]@SOURCE[~TENANT]
    
    Examples:
        - CUSTOMER@CRM
        - EMPLOYEE~MANAGER@CRM
        - ORDER@SAP~AU
    """
```

**Derivation Logic**:
1. For each hook in each frame:
2. Build concept part: `UPPER(concept)` + (`~` + `UPPER(qualifier)` if qualifier)
3. Build source part: `UPPER(source)` + (`~` + `UPPER(tenant)` if tenant)
4. Combine: `{concept_part}@{source_part}`

### Concept Registry

```python
def derive_concepts(manifest: Manifest) -> set[str]:
    """
    Derive unique concept names from all hooks.
    """
```

### Hook Registry

```python
def derive_hook_registry(manifest: Manifest) -> dict[str, list[tuple[str, Hook]]]:
    """
    Index all hooks by name for relationship detection.
    
    Returns: {hook_name: [(frame_name, hook), ...]}
    """
```

---

## Naming Conventions

**File**: `src/hook/core/normalization.py`

### Patterns

| Pattern | Regex | Examples | Used For |
|---------|-------|----------|----------|
| `lower_snake_case` | `^[a-z][a-z0-9_]*$` | `customer`, `order_line` | concept, qualifier, frame name |
| `UPPER_SNAKE_CASE` | `^[A-Z][A-Z0-9_]*$` | `CRM`, `SAP_FIN` | source, tenant |
| `hook_name` | `^_(hk\|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$` | `_hk__customer`, `_wk__ref__genre` | hook name |
| `frame_name` | `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` | `frame.customer`, `psa.order` | frame name |
| `semver` | `^\d+\.\d+\.\d+$` | `1.0.0`, `2.1.3` | version fields |

### Validation Functions

```python
def is_lower_snake_case(s: str) -> bool: ...
def is_upper_snake_case(s: str) -> bool: ...
def is_valid_hook_name(s: str, prefix: str) -> bool: ...
def is_valid_frame_name(s: str) -> bool: ...
def is_valid_semver(s: str) -> bool: ...
```

---

## Treatment Syntax

**File**: `src/hook/core/normalization.py`  
**Spec Reference**: [spec.md](spec.md) FR-070 to FR-073

### Supported Operations

| Operation | Syntax | Arguments | Example | Result |
|-----------|--------|-----------|---------|--------|
| `LPAD` | `LPAD:<width>:<char>` | width (int), char (single) | `LPAD:6:0` on `"123"` | `"000123"` |
| `RPAD` | `RPAD:<width>:<char>` | width (int), char (single) | `RPAD:6:X` on `"AB"` | `"ABXXXX"` |
| `UPPER` | `UPPER` | — | `UPPER` on `"abc"` | `"ABC"` |
| `LOWER` | `LOWER` | — | `LOWER` on `"ABC"` | `"abc"` |
| `TRIM` | `TRIM` | — | `TRIM` on `" x "` | `"x"` |

### Chaining

Multiple treatments separated by `|`:
```
TRIM|UPPER|LPAD:6:0
```

Applied left-to-right: `" abc "` → `"abc"` → `"ABC"` → `"000ABC"`

### Validation

```python
def parse_treatment(treatment: str) -> list[Treatment]: ...
def validate_treatment(treatment: str) -> list[Diagnostic]: ...
```

---

## expr_sql Validation

**File**: `src/hook/core/expression.py`  
**Spec Reference**: [plan.md#expr_sql-validation-rules](plan.md#expr_sql-validation-rules)

### Allowed Tokens

| Category | Allowed |
|----------|---------|
| Column references | `customer_id`, `"Customer ID"`, `[Column Name]` |
| Literals | `'string'`, `123`, `123.45`, `NULL`, `TRUE`, `FALSE` |
| Operators | `\|\|`, `+`, `-`, `*`, `/`, `%`, `=`, `<>`, `!=`, `<`, `>`, `<=`, `>=`, `AND`, `OR`, `NOT` |
| Parentheses | `(`, `)` |
| CASE | `CASE`, `WHEN`, `THEN`, `ELSE`, `END` |
| CAST | `CAST`, `AS`, type names |
| Functions | `COALESCE`, `NULLIF`, `TRIM`, `UPPER`, `LOWER`, `SUBSTRING`, `LEFT`, `RIGHT`, `ABS`, `ROUND`, `FLOOR`, `CEILING`, `LEN`, `LENGTH` |

### Forbidden Patterns (ERROR)

| Pattern | Regex | Example |
|---------|-------|---------|
| SELECT keyword | `\bSELECT\b` | `(SELECT x FROM y)` |
| FROM clause | `\bFROM\b` | `x FROM table` |
| JOIN | `\bJOIN\b` | `LEFT JOIN` |
| WHERE | `\bWHERE\b` | `WHERE x = 1` |
| GROUP BY | `\bGROUP\s+BY\b` | `GROUP BY x` |
| ORDER BY | `\bORDER\s+BY\b` | `ORDER BY x` |
| Subquery | `\(\s*SELECT` | `(SELECT ...)` |
| CTE | `\bWITH\b` | `WITH cte AS` |
| Non-deterministic | `\b(RANDOM|NEWID|GETDATE|NOW|CURRENT_TIMESTAMP|SYSDATE)\b` | `GETDATE()` |
| DDL/DML | `\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b` | `INSERT INTO` |

### Validation Function

```python
def validate_expr_sql(expr: str) -> list[Diagnostic]:
    """
    Validate that expr_sql is a pure SQL expression.
    
    Returns empty list if valid, list of diagnostics if invalid.
    """
```

---

## Validation Rules Reference

**File**: `src/hook/core/rules.py`  
**Spec Reference**: [spec.md#validation-rules](spec.md#validation-rules)

### ERROR Rules (exit code 1)

| Rule ID | Validation Function | Spec Line |
|---------|---------------------|-----------|
| FRAME-001 | `validate_frame_has_hooks(frame)` | Validation Rules table |
| FRAME-002 | `validate_frame_name(frame.name)` | FR-052 |
| FRAME-003 | `validate_frame_has_primary_hook(frame)` | FR-035 |
| FRAME-004 | `validate_frame_source(frame.source)` | Validation Rules table |
| HOOK-001 | `validate_hook_required_fields(hook)` | FR-034 |
| HOOK-002 | `validate_hook_name(hook.name, settings)` | FR-051 |
| HOOK-003 | `validate_hook_role(hook.role)` | FR-035 |
| HOOK-004 | `validate_hook_concept(hook.concept)` | FR-050 |
| HOOK-005 | `validate_hook_source(hook.source)` | FR-053 |
| HOOK-006 | `validate_hook_expr_sql(hook.expr_sql)` | FR-034 |
| HOOK-007 | `validate_hook_treatment(hook.treatment)` | FR-070-073 |
| KEYSET-001 | `validate_keyset_uniqueness(manifest)` | FR-036 |
| CONCEPT-001 | `validate_concept_in_frames(concept, manifest)` | Validation Rules table |
| CONCEPT-002 | `validate_concept_description(concept)` | Validation Rules table |
| MANIFEST-001 | `validate_manifest_version(manifest.manifest_version)` | FR-030 |
| MANIFEST-002 | `validate_schema_version(manifest.schema_version)` | FR-031 |

### WARN Rules (exit code 0)

| Rule ID | Validation Function | Spec Line |
|---------|---------------------|-----------|
| CONCEPT-W01 | `warn_concept_count(manifest)` | Advisory Rules table |
| HOOK-W01 | `warn_weak_hook_prefix(hook, concepts)` | Advisory Rules table |
| FRAME-W01 | `warn_no_unique_hooks(frame)` | Advisory Rules table |
| FRAME-W02 | `warn_duplicate_source(manifest)` | Advisory Rules table |
| TARGET-W01 | `warn_reserved_targets(manifest)` | Advisory Rules table |

---

## I/O Contracts

### YAML Key Ordering

Output YAML must have keys in this order for deterministic serialization:

```yaml
manifest_version: ...
schema_version: ...
metadata:
  name: ...
  description: ...
  created_at: ...
  updated_at: ...
settings:
  hook_prefix: ...
  weak_hook_prefix: ...
  delimiter: ...
frames:
  - name: ...
    source: ...
    description: ...
    hooks:
      - name: ...
        role: ...
        concept: ...
        qualifier: ...
        source: ...
        tenant: ...
        expr_sql: ...
        treatment: ...
concepts:
  - name: ...
    description: ...
    examples: ...
    is_weak: ...
targets:
  hook_sql: ...
  uss_sql: ...
  qlik: ...
```

### Parse Error Format

```python
class ParseError(BaseModel, frozen=True):
    line: int | None       # 1-indexed line number
    column: int | None     # 1-indexed column number
    message: str           # Error description
```

---

## Cross-Reference Index

| Model | Plan Task | Spec Section |
|-------|-----------|--------------|
| `Manifest` | M1-02 | Manifest Schema (v1) |
| `Metadata` | M1-02 | Manifest Schema (v1) |
| `Settings` | M1-06 | Manifest Schema (v1), FR-038 |
| `Frame` | M1-03 | Manifest Schema (v1), FR-032, FR-033 |
| `Hook` | M1-04 | Manifest Schema (v1), FR-034, FR-035 |
| `Concept` | M1-05 | Manifest Schema (v1), FR-037 |
| `Targets` | M1-02 | Manifest Schema (v1), FR-039, FR-040 |
| `Diagnostic` | M1-07 | Diagnostic Format, FR-016 |
| Naming validators | M1-08 | FR-050 to FR-056 |
| Schema validation | M1-09 | FR-010 to FR-016 |
| FRAME rules | M2-01 | Validation Rules table |
| HOOK rules | M2-02 | Validation Rules table |
| KEYSET rules | M2-03 | Validation Rules table |
| CONCEPT rules | M2-04 | Validation Rules table |
| MANIFEST rules | M2-05 | Validation Rules table |
| WARN rules | M2-06 | Advisory Rules table |
| Key set derivation | M2-07 | Auto-Derived Registries, FR-036, FR-054, FR-055 |
| expr_sql validation | M2-10 | expr_sql Validation Rules (plan.md) |
| YAML I/O | M3-01, M3-02 | I/O Contracts (this document) |

---

## Implementation Cookbook

This section provides step-by-step guidance for implementing each milestone.

### File Creation Order (M1)

Create files in this sequence to respect dependencies:

```text
1. src/hook/__init__.py              # Package root
2. src/hook/py.typed                  # PEP 561 marker (empty file)
3. src/hook/models/__init__.py        # Models package
4. src/hook/models/diagnostic.py      # Diagnostic first (no deps)
5. src/hook/models/settings.py        # Settings (no deps)
6. src/hook/models/concept.py         # Concept (no deps)
7. src/hook/models/frame.py           # Frame + Hook (HookRole enum)
8. src/hook/models/manifest.py        # Manifest (imports all above)
9. src/hook/core/__init__.py          # Core package
10. src/hook/core/normalization.py    # Naming validators (no deps)
11. src/hook/core/validation.py       # Schema validation (imports models)
```

### Function Patterns

#### Pattern A: Validator Functions

All validation functions follow this signature:

```python
from hook.models.diagnostic import Diagnostic, Severity

def validate_<entity>_<aspect>(entity: EntityType, context: Context | None = None) -> list[Diagnostic]:
    """
    Validate a specific aspect of an entity.
    
    Args:
        entity: The model instance to validate
        context: Optional context (e.g., manifest for cross-references)
    
    Returns:
        Empty list if valid, list of Diagnostics if invalid.
    """
    diagnostics: list[Diagnostic] = []
    
    if <condition_violated>:
        diagnostics.append(Diagnostic(
            rule_id="ENTITY-NNN",
            severity=Severity.ERROR,
            message="Description of what's wrong",
            path="path.to.field",
            fix="How to fix it"
        ))
    
    return diagnostics
```

#### Pattern B: Naming Validators (Predicates)

Naming validators return `bool`:

```python
import re

LOWER_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
UPPER_SNAKE_CASE = re.compile(r"^[A-Z][A-Z0-9_]*$")
HOOK_NAME = re.compile(r"^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$")
FRAME_NAME = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

def is_lower_snake_case(s: str) -> bool:
    return bool(LOWER_SNAKE_CASE.match(s))

def is_upper_snake_case(s: str) -> bool:
    return bool(UPPER_SNAKE_CASE.match(s))

def is_valid_hook_name(s: str) -> bool:
    return bool(HOOK_NAME.match(s))

def is_valid_frame_name(s: str) -> bool:
    return bool(FRAME_NAME.match(s))

def is_valid_semver(s: str) -> bool:
    return bool(SEMVER.match(s))
```

#### Pattern C: Registry Derivation (Pure Functions)

```python
from hook.models.manifest import Manifest

def derive_key_sets(manifest: Manifest) -> set[str]:
    """Derive unique key sets from all hooks."""
    key_sets: set[str] = set()
    for frame in manifest.frames:
        for hook in frame.hooks:
            key_set = _build_key_set(hook)
            key_sets.add(key_set)
    return key_sets

def _build_key_set(hook: Hook) -> str:
    """Build key set string: CONCEPT[~QUALIFIER]@SOURCE[~TENANT]"""
    concept_part = hook.concept.upper()
    if hook.qualifier:
        concept_part += f"~{hook.qualifier.upper()}"
    
    source_part = hook.source.upper()
    if hook.tenant:
        source_part += f"~{hook.tenant.upper()}"
    
    return f"{concept_part}@{source_part}"
```

#### Pattern D: Composite Validation

Combine all rules into a single entry point:

```python
def validate_manifest(manifest: Manifest) -> list[Diagnostic]:
    """Run all validation rules and collect diagnostics."""
    diagnostics: list[Diagnostic] = []
    
    # Manifest-level rules
    diagnostics.extend(validate_manifest_version(manifest))
    diagnostics.extend(validate_schema_version(manifest))
    
    # Frame-level rules
    for i, frame in enumerate(manifest.frames):
        ctx = f"frames[{i}]"
        diagnostics.extend(validate_frame(frame, ctx, manifest))
    
    # Concept-level rules
    for i, concept in enumerate(manifest.concepts):
        ctx = f"concepts[{i}]"
        diagnostics.extend(validate_concept(concept, ctx, manifest))
    
    # Global rules (cross-entity)
    diagnostics.extend(validate_keyset_uniqueness(manifest))
    diagnostics.extend(warn_concept_count(manifest))
    diagnostics.extend(warn_duplicate_source(manifest))
    diagnostics.extend(warn_reserved_targets(manifest))
    
    return diagnostics
```

### Test Patterns

#### Unit Test: Model Instantiation

```python
# tests/unit/test_models.py
from datetime import datetime, timezone
import pytest
from hook.models.manifest import Manifest, Metadata
from hook.models.settings import Settings
from hook.models.frame import Frame, Hook, HookRole

def test_settings_defaults():
    """Settings use correct defaults."""
    settings = Settings()
    assert settings.hook_prefix == "_hk__"
    assert settings.weak_hook_prefix == "_wk__"
    assert settings.delimiter == "|"

def test_settings_frozen():
    """Settings are immutable."""
    settings = Settings()
    with pytest.raises(Exception):  # pydantic.ValidationError
        settings.hook_prefix = "changed"

def test_hook_required_fields():
    """Hook requires name, role, concept, source, expr_sql."""
    with pytest.raises(Exception):
        Hook(name="_hk__test")  # Missing required fields
```

#### Unit Test: Naming Validators

```python
# tests/unit/test_normalization.py
import pytest
from hook.core.normalization import (
    is_lower_snake_case,
    is_upper_snake_case,
    is_valid_hook_name,
    is_valid_frame_name,
    is_valid_semver,
)

@pytest.mark.parametrize("value,expected", [
    ("customer", True),
    ("order_line", True),
    ("Customer", False),
    ("order-line", False),
    ("123abc", False),
    ("", False),
])
def test_lower_snake_case(value: str, expected: bool):
    assert is_lower_snake_case(value) == expected

@pytest.mark.parametrize("value,expected", [
    ("CRM", True),
    ("SAP_FIN", True),
    ("crm", False),
    ("Crm", False),
])
def test_upper_snake_case(value: str, expected: bool):
    assert is_upper_snake_case(value) == expected
```

#### Unit Test: Validation Rules

```python
# tests/unit/test_validation.py
from hook.core.rules import validate_frame_has_hooks
from hook.models.frame import Frame

def test_frame_001_missing_hooks():
    """FRAME-001: Frame must have at least one hook."""
    frame = Frame(name="frame.test", source="psa.test", hooks=[])
    diagnostics = validate_frame_has_hooks(frame, "frames[0]")
    
    assert len(diagnostics) == 1
    assert diagnostics[0].rule_id == "FRAME-001"
    assert diagnostics[0].severity == Severity.ERROR
    assert "frames[0]" in diagnostics[0].path
```

#### Property-Based Test: Key Set Derivation

```python
# tests/unit/test_registry.py
from hypothesis import given, strategies as st
from hook.core.registry import _build_key_set
from hook.models.frame import Hook, HookRole

@given(
    concept=st.from_regex(r"[a-z][a-z0-9_]{0,20}", fullmatch=True),
    source=st.from_regex(r"[A-Z][A-Z0-9_]{0,10}", fullmatch=True),
)
def test_key_set_format(concept: str, source: str):
    """Key set always matches CONCEPT@SOURCE pattern."""
    hook = Hook(
        name=f"_hk__{concept}",
        role=HookRole.PRIMARY,
        concept=concept,
        source=source,
        expr_sql="id",
    )
    key_set = _build_key_set(hook)
    
    assert "@" in key_set
    assert key_set == f"{concept.upper()}@{source.upper()}"
```

### Fixture Templates

#### Valid Fixture: minimal.yaml

```yaml
# tests/fixtures/valid/minimal.yaml
manifest_version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Minimal Test Fixture"
  description: "Single concept, single hook, one frame"
  created_at: "2026-01-04T00:00:00Z"
  updated_at: "2026-01-04T00:00:00Z"

settings:
  hook_prefix: "_hk__"
  weak_hook_prefix: "_wk__"
  delimiter: "|"

frames:
  - name: "frame.customer"
    source: "psa.customer"
    hooks:
      - name: "_hk__customer"
        role: "primary"
        concept: "customer"
        source: "CRM"
        expr_sql: "customer_id"

concepts: []

targets:
  hook_sql: {}
  uss_sql: {}
  qlik: {}
```

#### Invalid Fixture: missing_primary_hook.yaml

```yaml
# tests/fixtures/invalid/missing_primary_hook.yaml
# Expected: FRAME-003 error (no primary hook)
manifest_version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Invalid - Missing Primary"
  created_at: "2026-01-04T00:00:00Z"
  updated_at: "2026-01-04T00:00:00Z"

settings: {}

frames:
  - name: "frame.order_line"
    source: "psa.order_line"
    hooks:
      - name: "_hk__order"
        role: "foreign"  # No primary!
        concept: "order"
        source: "ERP"
        expr_sql: "order_id"

targets: {}
```

### Module Exports

#### src/hook/__init__.py

```python
"""HOOK Manifest Builder - validate and create HOOK manifests."""
from hook.models.manifest import Manifest, Metadata
from hook.models.settings import Settings
from hook.models.frame import Frame, Hook, HookRole
from hook.models.concept import Concept
from hook.models.diagnostic import Diagnostic, Severity

__all__ = [
    "Manifest",
    "Metadata", 
    "Settings",
    "Frame",
    "Hook",
    "HookRole",
    "Concept",
    "Diagnostic",
    "Severity",
]
__version__ = "0.1.0"
```

#### src/hook/models/__init__.py

```python
"""Immutable Pydantic models for HOOK manifests."""
from hook.models.manifest import Manifest, Metadata
from hook.models.settings import Settings
from hook.models.frame import Frame, Hook, HookRole
from hook.models.concept import Concept
from hook.models.diagnostic import Diagnostic, Severity

__all__ = [
    "Manifest",
    "Metadata",
    "Settings", 
    "Frame",
    "Hook",
    "HookRole",
    "Concept",
    "Diagnostic",
    "Severity",
]
```

#### src/hook/core/__init__.py

```python
"""Pure validation functions for HOOK manifests."""
from hook.core.validation import validate_manifest
from hook.core.normalization import (
    is_lower_snake_case,
    is_upper_snake_case,
    is_valid_hook_name,
    is_valid_frame_name,
    is_valid_semver,
)
from hook.core.registry import (
    derive_key_sets,
    derive_concepts,
    derive_hook_registry,
)

__all__ = [
    "validate_manifest",
    "is_lower_snake_case",
    "is_upper_snake_case",
    "is_valid_hook_name",
    "is_valid_frame_name",
    "is_valid_semver",
    "derive_key_sets",
    "derive_concepts",
    "derive_hook_registry",
]
```

### Task Dependencies (Explicit)

```text
M1-01 (pyproject.toml)
  └─► M1-02 to M1-11 (all code tasks)

M1-07 (Diagnostic model)
  └─► M1-09 (schema validation uses Diagnostic)
  └─► M2-01 to M2-06 (all rules produce Diagnostics)

M1-08 (naming validators)
  └─► M2-02 (HOOK rules use naming validators)
  └─► M2-01 (FRAME-002 uses naming validators)

M1-02 to M1-06 (all models)
  └─► M1-09 (schema validation needs models)
  └─► M2-07 to M2-09 (registries need models)

M2-07 (key set derivation)
  └─► M2-03 (KEYSET-001 uses derived key sets)

M2-01 to M2-06 (all rules)
  └─► M3-01 (YAML reader calls validation)
  └─► M4-02 (validate command calls validation)
```
