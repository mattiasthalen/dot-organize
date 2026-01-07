# Pydantic v2 Frozen Models Research

**Date**: 2026-01-06  
**Pydantic Version**: 2.12.5  
**Python Version**: 3.12  
**Purpose**: Research frozen immutable models for HOOK manifest validation tool

---

## Table of Contents

1. [Summary](#summary)
2. [Frozen Model Declaration](#1-frozen-model-declaration)
3. [Field Validation with `Field()`](#2-field-validation-with-field)
4. [Custom Field Validators](#3-custom-field-validators)
5. [Model Validators (Cross-Field)](#4-model-validators-cross-field)
6. [String Enums](#5-string-enums)
7. [Nested Models](#6-nested-models)
8. [Serialization & Deserialization](#7-serialization--deserialization)
9. [Additional Configuration Options](#8-additional-configuration-options)
10. [Complete HOOK Manifest Example](#9-complete-hook-manifest-example)

---

## Summary

Pydantic v2 provides excellent support for immutable data models using `frozen=True`. Key findings:

| Feature | Approach | Notes |
|---------|----------|-------|
| Frozen models | `model_config = ConfigDict(frozen=True)` | Models are hashable, mutations raise `ValidationError` |
| Field constraints | `Field(min_length=1, pattern=r'...')` | Declarative validation |
| Custom validation | `@field_validator('field_name')` | Regex patterns, custom logic |
| Cross-field validation | `@model_validator(mode='after')` | Mutual exclusivity, count checks |
| Enums | `class MyEnum(str, Enum)` | Seamless serialization |
| Serialization | `model_dump()`, `model_dump_json()` | ISO 8601 datetime by default |
| Deserialization | `model_validate()`, `model_validate_json()` | Parses ISO strings to datetime |

---

## 1. Frozen Model Declaration

### Method 1: Using `model_config` dict (simplest)

```python
from pydantic import BaseModel

class FrozenModel(BaseModel):
    model_config = {"frozen": True}
    
    name: str
    value: int
```

### Method 2: Using `ConfigDict` (explicit typing, IDE support)

```python
from pydantic import BaseModel, ConfigDict

class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    value: int
```

### Behavior of Frozen Models

```python
m = FrozenModel(name="test", value=42)

# ✅ Frozen models are hashable (can be used in sets/dict keys)
hash(m)  # Returns integer hash

# ✅ Equality works by value
m1 = FrozenModel(name="test", value=42)
m2 = FrozenModel(name="test", value=42)
assert m1 == m2  # True

# ❌ Mutations are blocked
m.name = "changed"  # Raises ValidationError: Instance is frozen
```

### Key Differences from Pydantic v1

| Pydantic v1 | Pydantic v2 |
|-------------|-------------|
| `class Config: frozen = True` | `model_config = ConfigDict(frozen=True)` |
| `allow_mutation = False` | Removed (use `frozen=True`) |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |

---

## 2. Field Validation with `Field()`

### Basic Field Constraints

```python
from pydantic import BaseModel, Field, ConfigDict

class Entity(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    # Required field with description
    name: str = Field(description="Entity name")
    
    # Optional field (None allowed, with default)
    description: str | None = Field(default=None, description="Optional description")
    
    # Default value (non-None)
    enabled: bool = Field(default=True)
    
    # Numeric constraints
    count: int = Field(ge=0, le=100, description="Count between 0-100")
    priority: float = Field(gt=0.0, lt=1.0, description="Priority 0-1 exclusive")
    
    # String constraints
    code: str = Field(
        min_length=1,
        max_length=50,
        pattern=r'^[a-z][a-z0-9_]*$',
        description="Lowercase snake_case identifier"
    )
    
    # List constraints
    tags: list[str] = Field(default_factory=list, min_length=0, max_length=10)
```

### Field Constraint Reference

| Constraint | Types | Description |
|------------|-------|-------------|
| `gt`, `ge`, `lt`, `le` | `int`, `float` | Greater/less than (or equal) |
| `multiple_of` | `int`, `float` | Must be multiple of value |
| `min_length`, `max_length` | `str`, `list`, `set` | Length constraints |
| `pattern` | `str` | Regex pattern (fullmatch) |
| `strict` | all | Disable type coercion for field |

### Optional Fields: `| None` vs `Optional`

```python
from typing import Optional

class Example(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    # Preferred in Python 3.10+ (cleaner syntax)
    field1: str | None = None
    
    # Equivalent (works in Python 3.9+)
    field2: Optional[str] = None
    
    # Optional with Field()
    field3: str | None = Field(default=None, description="Optional with metadata")
```

**Recommendation**: Use `str | None` syntax for Python 3.10+.

---

## 3. Custom Field Validators

### Basic `@field_validator`

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_hook_name(cls, v: str) -> str:
        """Validate hook follows naming convention."""
        pattern = r'^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$'
        if not re.match(pattern, v):
            raise ValueError(f"Hook name must match pattern: {pattern}")
        return v
```

### Validating Multiple Fields

```python
class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    hook_prefix: str
    weak_hook_prefix: str
    
    @field_validator('hook_prefix', 'weak_hook_prefix')
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        if not v.startswith('_'):
            raise ValueError("Prefix must start with underscore")
        return v
```

### Validation Modes

```python
class Example(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    value: int
    
    # mode='before': runs before Pydantic's internal validation
    @field_validator('value', mode='before')
    @classmethod
    def preprocess_value(cls, v):
        if isinstance(v, str):
            return int(v.strip())
        return v
    
    # mode='after' (default): runs after Pydantic's validation
    @field_validator('value', mode='after')
    @classmethod
    def validate_value(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
```

---

## 4. Model Validators (Cross-Field)

### `@model_validator(mode='after')` for Cross-Field Validation

```python
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Self

class Source(BaseModel):
    """Source must have exactly one of 'relation' or 'path'."""
    model_config = ConfigDict(frozen=True)
    
    relation: str | None = Field(default=None, description="Database relation")
    path: str | None = Field(default=None, description="File system path")
    
    @model_validator(mode='after')
    def check_exclusivity(self) -> Self:
        """Ensure exactly one of relation or path is set."""
        has_relation = self.relation is not None
        has_path = self.path is not None
        
        if has_relation and has_path:
            raise ValueError("Source must have exactly one of 'relation' OR 'path', not both")
        if not has_relation and not has_path:
            raise ValueError("Source must have at least one of 'relation' OR 'path'")
        return self
```

### Validating List Contents

```python
from enum import Enum

class HookRole(str, Enum):
    PRIMARY = "primary"
    FOREIGN = "foreign"

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    role: HookRole

class Frame(BaseModel):
    """Frame must have exactly one primary hook."""
    model_config = ConfigDict(frozen=True)
    
    name: str
    hooks: list[Hook]
    
    @model_validator(mode='after')
    def validate_single_primary(self) -> Self:
        primary_hooks = [h for h in self.hooks if h.role == HookRole.PRIMARY]
        
        if len(primary_hooks) == 0:
            raise ValueError("Frame must have exactly one primary hook")
        if len(primary_hooks) > 1:
            raise ValueError(
                f"Frame must have exactly one primary hook, found {len(primary_hooks)}"
            )
        return self
```

### `@model_validator(mode='before')` for Preprocessing

```python
class FlexibleInput(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    value: int
    
    @model_validator(mode='before')
    @classmethod
    def preprocess(cls, data: dict) -> dict:
        """Receives raw input data before any field validation."""
        if isinstance(data, dict):
            # Normalize field names (e.g., camelCase to snake_case)
            if 'Name' in data:
                data['name'] = data.pop('Name')
            # Transform values
            if 'value' in data and isinstance(data['value'], str):
                data['value'] = int(data['value'])
        return data
```

---

## 5. String Enums

### Defining String Enums

```python
from enum import Enum

class HookRole(str, Enum):
    """Role of a hook in a frame."""
    PRIMARY = "primary"
    FOREIGN = "foreign"

class Severity(str, Enum):
    """Diagnostic severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
```

### Using Enums in Models

```python
class Hook(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    role: HookRole

# Both work:
h1 = Hook(name="_hk__id", role=HookRole.PRIMARY)  # Enum instance
h2 = Hook(name="_hk__id", role="primary")          # String (auto-converted)

# Access enum properties
print(h1.role.value)  # "primary"
print(h1.role.name)   # "PRIMARY"
print(isinstance(h1.role, HookRole))  # True
```

### Enum Serialization Behavior

```python
# Default behavior: enum stays as enum in model_dump()
h = Hook(name="_hk__id", role=HookRole.PRIMARY)
h.model_dump()      # {'name': '_hk__id', 'role': <HookRole.PRIMARY: 'primary'>}
h.model_dump_json() # '{"name":"_hk__id","role":"primary"}' (JSON uses value)

# With use_enum_values=True: converts to string in model_dump()
class HookEnumValues(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)
    name: str
    role: HookRole

h2 = HookEnumValues(name="_hk__id", role=HookRole.PRIMARY)
h2.model_dump()  # {'name': '_hk__id', 'role': 'primary'}
```

**Recommendation**: Keep default behavior (no `use_enum_values`) to preserve type safety. Use `model_dump(mode='json')` when you need string values.

---

## 6. Nested Models

### Composing Models

```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    created_at: datetime

class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    hook_prefix: str = "_hk"
    delimiter: str = "__"

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    role: HookRole

class Frame(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    source: Source                              # Nested model
    hooks: list[Hook] = Field(default_factory=list)  # List of models

class Manifest(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    metadata: Metadata                          # Required nested
    settings: Settings = Field(default_factory=Settings)  # Optional with default
    frames: list[Frame] = Field(default_factory=list)
```

### Forward References (Circular Dependencies)

```python
from __future__ import annotations  # Enable forward references
from pydantic import BaseModel, ConfigDict

class TreeNode(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    value: str
    children: list[TreeNode] = []  # Self-reference works with __future__ import

# Alternative: use string annotation
class TreeNodeAlt(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    value: str
    children: list["TreeNodeAlt"] = []

# Must rebuild model after all definitions
TreeNodeAlt.model_rebuild()
```

---

## 7. Serialization & Deserialization

### Serializing to Dict: `model_dump()`

```python
from datetime import datetime, timezone

class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    created_at: datetime
    updated_at: datetime | None = None

meta = Metadata(name="test", created_at=datetime.now(timezone.utc))

# Basic dict (datetime stays as datetime object)
meta.model_dump()
# {'name': 'test', 'created_at': datetime(...), 'updated_at': None}

# JSON-compatible dict (datetime becomes ISO string)
meta.model_dump(mode='json')
# {'name': 'test', 'created_at': '2026-01-06T01:43:10.307173Z', 'updated_at': None}

# Exclude None values
meta.model_dump(exclude_none=True)
# {'name': 'test', 'created_at': datetime(...)}

# Exclude specific fields
meta.model_dump(exclude={'updated_at'})

# Include only specific fields
meta.model_dump(include={'name', 'created_at'})

# Nested exclusion
manifest.model_dump(exclude={'frames': {'__all__': {'hooks'}}})
```

### Serializing to JSON: `model_dump_json()`

```python
# Compact JSON
meta.model_dump_json()
# '{"name":"test","created_at":"2026-01-06T01:43:10.307173Z","updated_at":null}'

# Pretty-printed JSON
meta.model_dump_json(indent=2)

# Exclude None in JSON output
meta.model_dump_json(exclude_none=True)
```

### Deserializing from Dict: `model_validate()`

```python
# From dict with ISO string (auto-parsed to datetime)
data = {
    "name": "from_dict",
    "created_at": "2024-01-15T10:30:00Z"
}
meta = Metadata.model_validate(data)
print(type(meta.created_at))  # <class 'datetime.datetime'>

# Strict validation (no type coercion)
Metadata.model_validate(data, strict=True)
```

### Deserializing from JSON: `model_validate_json()`

```python
json_str = '{"name": "from_json", "created_at": "2024-06-20T15:45:00+00:00"}'
meta = Metadata.model_validate_json(json_str)
```

### Datetime Handling

Pydantic automatically:
- Serializes `datetime` to ISO 8601 format in JSON
- Parses ISO 8601 strings back to `datetime` objects
- Preserves timezone information

```python
from datetime import datetime, timezone

# UTC datetime
dt = datetime.now(timezone.utc)

# Serialization preserves timezone
# Output: "2026-01-06T01:43:10.307173Z" (Z = UTC)

# Parsing ISO strings
data = {"name": "test", "created_at": "2024-01-15T10:30:00+05:30"}
meta = Metadata.model_validate(data)
# meta.created_at has tzinfo set correctly
```

---

## 8. Additional Configuration Options

### `ConfigDict` Options Reference

```python
from pydantic import ConfigDict

class MyModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,              # Make immutable
        strict=True,              # Disable type coercion
        extra='forbid',           # Reject unknown fields ('ignore' to silently drop)
        use_enum_values=True,     # Store enum values instead of enum instances
        validate_default=True,    # Validate default values
        populate_by_name=True,    # Allow populating by field name or alias
        str_strip_whitespace=True,# Strip whitespace from strings
    )
```

### Extra Fields Handling

```python
# Forbid extra fields (strict input validation)
class StrictInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str

StrictInput(name="test", unknown="value")  # Raises ValidationError

# Ignore extra fields (lenient parsing)
class LenientInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra='ignore')
    name: str

LenientInput(name="test", unknown="value")  # Works, unknown is dropped
```

### Reusable Type Constraints with `Annotated`

```python
from typing import Annotated
from pydantic import Field

# Define reusable constrained types
PositiveInt = Annotated[int, Field(gt=0)]
NonEmptyStr = Annotated[str, Field(min_length=1)]
SemVer = Annotated[str, Field(pattern=r'^\d+\.\d+\.\d+$')]
SnakeCase = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]*$')]

class Config(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    version: SemVer
    name: SnakeCase
    count: PositiveInt
```

---

## 9. Complete HOOK Manifest Example

```python
"""
Complete HOOK Manifest Models using Pydantic v2 Frozen Models

All models are immutable (frozen=True) for safety and hashability.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Self, Annotated
from datetime import datetime
from enum import Enum
import re


# ============================================
# ENUMS
# ============================================

class HookRole(str, Enum):
    """Role of a hook in a frame."""
    PRIMARY = "primary"
    FOREIGN = "foreign"


class Severity(str, Enum):
    """Diagnostic severity levels."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


# ============================================
# REUSABLE TYPE CONSTRAINTS
# ============================================

SemVer = Annotated[str, Field(pattern=r'^\d+\.\d+\.\d+$', description="Semantic version")]
SnakeCase = Annotated[str, Field(min_length=1, pattern=r'^[a-z][a-z0-9_]*$')]


# ============================================
# BASE MODELS
# ============================================

class Metadata(BaseModel):
    """Manifest metadata with timestamps."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    name: str = Field(min_length=1, max_length=100, description="Manifest name")
    description: str | None = Field(default=None, description="Manifest description")
    created_at: datetime = Field(description="Creation timestamp (ISO 8601)")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")


class Settings(BaseModel):
    """Manifest settings with sensible defaults."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    hook_prefix: str = Field(default="_hk", description="Strong hook prefix")
    weak_hook_prefix: str = Field(default="_wk", description="Weak hook prefix")
    delimiter: str = Field(default="__", description="Hook name delimiter")
    
    @field_validator('hook_prefix', 'weak_hook_prefix')
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        if not v.startswith('_'):
            raise ValueError("Prefix must start with underscore")
        return v


class Source(BaseModel):
    """Data source - exactly one of relation or path must be set."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    relation: str | None = Field(default=None, description="Database relation reference")
    path: str | None = Field(default=None, description="File system path")
    
    @model_validator(mode='after')
    def check_exclusivity(self) -> Self:
        """Ensure exactly one of relation or path is set."""
        has_relation = self.relation is not None
        has_path = self.path is not None
        
        if has_relation and has_path:
            raise ValueError(
                "Source must have exactly one of 'relation' OR 'path', not both"
            )
        if not has_relation and not has_path:
            raise ValueError(
                "Source must have at least one of 'relation' OR 'path'"
            )
        return self


class Hook(BaseModel):
    """Hook definition with naming convention validation."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    name: str = Field(description="Hook name following naming convention")
    role: HookRole = Field(description="Hook role (primary/foreign)")
    concept: str | None = Field(default=None, description="Associated concept name")
    qualifier: str | None = Field(default=None, description="Optional qualifier")
    source: str | None = Field(default=None, description="Source reference for foreign hooks")
    tenant: str | None = Field(default=None, description="Tenant identifier")
    expr: str | None = Field(default=None, description="Expression for computed hooks")
    
    @field_validator('name')
    @classmethod
    def validate_hook_name(cls, v: str) -> str:
        """Validate hook follows naming convention: _hk__<name> or _wk__<name>."""
        pattern = r'^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$'
        if not re.match(pattern, v):
            raise ValueError(
                f"Hook name must match pattern {pattern}, got: '{v}'"
            )
        return v


class Concept(BaseModel):
    """Business concept definition."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    name: str = Field(min_length=1, description="Concept name")
    description: str | None = Field(default=None, description="Concept description")
    examples: list[str] = Field(default_factory=list, description="Example values")
    is_weak: bool = Field(default=False, description="Whether this is a weak concept")


class Frame(BaseModel):
    """Data frame with hooks - must have exactly one primary hook."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    name: str = Field(min_length=1, description="Frame name")
    source: Source = Field(description="Data source")
    description: str | None = Field(default=None, description="Frame description")
    hooks: list[Hook] = Field(default_factory=list, description="Frame hooks")
    
    @model_validator(mode='after')
    def validate_single_primary(self) -> Self:
        """Ensure exactly one primary hook exists."""
        primary_hooks = [h for h in self.hooks if h.role == HookRole.PRIMARY]
        
        if len(primary_hooks) == 0:
            raise ValueError("Frame must have exactly one primary hook")
        if len(primary_hooks) > 1:
            raise ValueError(
                f"Frame must have exactly one primary hook, found {len(primary_hooks)}"
            )
        return self


class Diagnostic(BaseModel):
    """Validation diagnostic message."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    rule_id: str = Field(description="Diagnostic rule identifier")
    severity: Severity = Field(description="Severity level")
    message: str = Field(description="Human-readable message")
    path: str | None = Field(default=None, description="JSON path to error location")
    fix: str | None = Field(default=None, description="Suggested fix")


class Manifest(BaseModel):
    """Root manifest model containing all configuration."""
    model_config = ConfigDict(frozen=True, extra='forbid')
    
    manifest_version: SemVer = Field(default="1.0.0")
    schema_version: SemVer = Field(default="1.0.0")
    metadata: Metadata = Field(description="Manifest metadata")
    settings: Settings = Field(default_factory=Settings, description="Manifest settings")
    frames: list[Frame] = Field(default_factory=list, description="Data frames")
    concepts: list[Concept] = Field(default_factory=list, description="Business concepts")


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    from datetime import timezone
    import json
    
    # Create a complete manifest
    manifest = Manifest(
        metadata=Metadata(
            name="sales_manifest",
            description="Sales data hook manifest",
            created_at=datetime.now(timezone.utc)
        ),
        frames=[
            Frame(
                name="customers",
                source=Source(relation="raw.customers"),
                description="Customer master data",
                hooks=[
                    Hook(name="_hk__customer_id", role=HookRole.PRIMARY, concept="customer"),
                    Hook(name="_hk__region_id", role=HookRole.FOREIGN, concept="region"),
                ]
            ),
            Frame(
                name="orders",
                source=Source(path="/data/orders.parquet"),
                hooks=[
                    Hook(name="_hk__order_id", role=HookRole.PRIMARY, concept="order"),
                    Hook(name="_hk__customer_id", role=HookRole.FOREIGN, source="customers"),
                ]
            )
        ],
        concepts=[
            Concept(name="customer", description="A customer entity", examples=["CUST001"]),
            Concept(name="order", description="A sales order"),
        ]
    )
    
    # Serialize to JSON
    print(manifest.model_dump_json(indent=2, exclude_none=True))
    
    # Verify immutability
    try:
        manifest.metadata.name = "changed"
    except Exception as e:
        print(f"\n✓ Mutation blocked: {e}")
```

---

## Key Takeaways

1. **Always use `ConfigDict(frozen=True)`** for immutable models
2. **Use `extra='forbid'`** to catch typos and invalid fields early
3. **Prefer `| None` over `Optional[]`** for Python 3.10+
4. **Use `@model_validator(mode='after')`** for cross-field validation with `Self` return type
5. **Use `@field_validator`** with regex for pattern validation
6. **String enums (`str, Enum`)** serialize cleanly to JSON
7. **Use `model_dump(mode='json')`** when you need JSON-compatible dict output
8. **Use `Annotated[type, Field(...)]`** for reusable constrained types
9. **Datetime serializes to ISO 8601** automatically in JSON output
10. **Frozen models are hashable** - can be used in sets and as dict keys
