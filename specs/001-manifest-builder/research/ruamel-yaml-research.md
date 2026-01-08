# ruamel.yaml Research for Deterministic YAML Serialization

**Date**: 2026-01-06
**Status**: ✅ Complete
**Purpose**: Research ruamel.yaml for reading/writing HOOK manifest YAML files with deterministic key ordering and good error handling.

## Executive Summary

`ruamel.yaml` is ideal for our manifest tool because it:
- Preserves key insertion order (no alphabetical sorting)
- Provides line/column numbers in parse errors
- Supports comment preservation for round-trip editing
- Integrates well with Pydantic models via `CommentedMap` (dict-compatible)
- Allows fine-grained control over output formatting

## 1. Installation and Setup

### Installation with uv

```bash
uv add ruamel.yaml
```

Or with pip:

```bash
pip install ruamel.yaml
```

### Basic Imports

```python
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.parser import ParserError
from ruamel.yaml.constructor import DuplicateKeyError
from io import StringIO
```

### YAML Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `YAML()` (default) | Round-trip mode | Our use case - preserves order, comments, formatting |
| `YAML(typ='safe')` | Safe loader | When you need plain Python dicts |
| `YAML(pure=True)` | Pure Python | When C extensions unavailable |

**Recommendation**: Use default round-trip mode for our manifest tool.

```python
# Create configured YAML instance
def create_yaml() -> YAML:
    """Create a YAML instance configured for manifest serialization."""
    yaml = YAML()
    yaml.default_flow_style = False  # Always use block style
    yaml.indent(mapping=2, sequence=4, offset=2)  # Standard indentation
    yaml.width = 120  # Line width before wrapping
    yaml.allow_duplicate_keys = False  # Strict mode
    yaml.preserve_quotes = True  # Keep original quote style
    return yaml
```

## 2. Reading YAML

### Loading from File

```python
from pathlib import Path

yaml = create_yaml()

# From file path
with open(Path("manifest.yaml")) as f:
    data = yaml.load(f)

# Type of data is CommentedMap (dict-like)
print(type(data))  # <class 'ruamel.yaml.comments.CommentedMap'>
```

### Loading from String

```python
from io import StringIO

yaml_content = """
manifest_version: 1.0.0
metadata:
  name: my_project
"""

yaml = create_yaml()
data = yaml.load(StringIO(yaml_content))
```

### Converting to Plain Python Dicts

`CommentedMap` and `CommentedSeq` are dict/list-like and work directly with Pydantic. However, if you need plain Python types:

```python
def to_plain_python(obj):
    """Recursively convert ruamel.yaml objects to plain Python."""
    if isinstance(obj, CommentedMap):
        return {k: to_plain_python(v) for k, v in obj.items()}
    elif isinstance(obj, CommentedSeq):
        return [to_plain_python(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_plain_python(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_plain_python(item) for item in obj]
    return obj

plain_dict = to_plain_python(data)
```

### DateTime Handling

ruamel.yaml automatically parses ISO dates and datetimes:

```yaml
date_only: 2024-01-15           # Parsed as datetime.date
datetime_utc: 2024-01-15T10:30:00Z    # Parsed as datetime (TimeStamp)
datetime_tz: 2024-01-15T10:30:00+05:00
string_date: "2024-01-15"       # Stays as string (quoted)
```

Pydantic handles these types directly:

```python
from pydantic import BaseModel
from datetime import datetime

class Metadata(BaseModel):
    created_at: datetime  # Works with ruamel.yaml TimeStamp

# CommentedMap passes directly to Pydantic
model = Metadata.model_validate(data['metadata'])
```

## 3. Writing YAML with Ordered Keys

### Key Ordering Approach

ruamel.yaml preserves key insertion order. For deterministic output, we:
1. Define the canonical key order for each type
2. Convert Pydantic model to dict
3. Build `CommentedMap` with keys in correct order
4. Dump to YAML

### Canonical Key Orders

```python
KEY_ORDERS = {
    'manifest': [
        'manifest_version', 'schema_version', 'metadata',
        'settings', 'frames', 'concepts'
    ],
    'metadata': ['name', 'description', 'created_at', 'updated_at'],
    'settings': ['hook_prefix', 'weak_hook_prefix', 'delimiter'],
    'source': ['relation', 'path'],
    'frame': ['name', 'source', 'description', 'hooks'],
    'hook': ['name', 'role', 'concept', 'qualifier', 'source', 'tenant', 'expr'],
    'concept': ['name', 'description', 'examples', 'is_weak'],
}
```

### Building Ordered CommentedMap

```python
from ruamel.yaml.comments import CommentedMap, CommentedSeq

def to_commented_map(data: dict, type_hint: str | None = None) -> CommentedMap:
    """Convert dict to CommentedMap with ordered keys based on type."""
    cm = CommentedMap()
    key_order = KEY_ORDERS.get(type_hint, list(data.keys()))

    # Order: specified keys first, then any remaining
    ordered_keys = [k for k in key_order if k in data]
    ordered_keys += [k for k in data if k not in ordered_keys]

    for key in ordered_keys:
        value = data[key]
        # Determine child type hint
        child_hint = key if key in KEY_ORDERS else None

        if isinstance(value, dict):
            cm[key] = to_commented_map(value, child_hint)
        elif isinstance(value, list):
            cs = CommentedSeq()
            # Infer item type: frames -> frame, hooks -> hook
            item_hint = key.rstrip('s') if key.endswith('s') else None
            for item in value:
                if isinstance(item, dict):
                    cs.append(to_commented_map(item, item_hint))
                else:
                    cs.append(item)
            cm[key] = cs
        else:
            cm[key] = value

    return cm
```

### Dumping to String/File

```python
def dump_to_string(data, yaml_instance: YAML | None = None) -> str:
    """Dump data to YAML string."""
    if yaml_instance is None:
        yaml_instance = create_yaml()
    stream = StringIO()
    yaml_instance.dump(data, stream)
    return stream.getvalue()

def dump_to_file(data, path: Path, yaml_instance: YAML | None = None) -> None:
    """Dump data to YAML file."""
    if yaml_instance is None:
        yaml_instance = create_yaml()
    with open(path, 'w') as f:
        yaml_instance.dump(data, f)
```

### Handling None Values

By default, ruamel.yaml outputs `null` for None values. To omit them:

```python
def filter_none(data: dict) -> dict:
    """Recursively remove None values from dict."""
    if isinstance(data, dict):
        return {k: filter_none(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [filter_none(item) for item in data]
    return data

# With Pydantic, use exclude_none=True
data = model.model_dump(mode='json', exclude_none=True)
```

## 4. Formatting Options

### Indentation Settings

```python
yaml = YAML()

# Parameters:
# - mapping: indentation for mapping keys
# - sequence: indentation for sequence items
# - offset: offset of sequence content from the '-' indicator
yaml.indent(mapping=2, sequence=4, offset=2)
```

**Recommended settings** for readable output:

```python
yaml.indent(mapping=2, sequence=4, offset=2)
```

Produces:

```yaml
frames:
  - name: customers
    source:
      relation: raw.customers
    hooks:
      - name: _hk__customer_id
        role: primary
```

### Other Formatting Options

```python
yaml.default_flow_style = False  # Always block style, never {inline}
yaml.width = 120                  # Max line width
yaml.preserve_quotes = True       # Keep original quote style on round-trip
```

## 5. Error Handling

### Exception Hierarchy

```
YAMLError (base)
├── MarkedYAMLError (has line/column info)
│   ├── ScannerError (tokenization issues: unclosed quotes, tabs)
│   ├── ParserError (structure issues: bad indentation, invalid syntax)
│   └── DuplicateKeyError (repeated keys)
└── (other specialized errors)
```

### Extracting Line/Column Information

```python
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.parser import ParserError
from ruamel.yaml.constructor import DuplicateKeyError

def parse_yaml_with_errors(content: str, source_name: str = "<string>") -> dict:
    """Parse YAML with detailed error reporting."""
    yaml = create_yaml()

    try:
        return yaml.load(StringIO(content))
    except DuplicateKeyError as e:
        line, col = extract_position(e)
        raise ManifestParseError(
            f"Duplicate key in {source_name}",
            line=line,
            column=col,
            problem=e.problem
        ) from e
    except (ScannerError, ParserError) as e:
        line, col = extract_position(e)
        raise ManifestParseError(
            f"YAML syntax error in {source_name}",
            line=line,
            column=col,
            problem=e.problem,
            context=getattr(e, 'context', None)
        ) from e
    except YAMLError as e:
        raise ManifestParseError(f"YAML error: {e}") from e

def extract_position(error: YAMLError) -> tuple[int | None, int | None]:
    """Extract line and column from YAML error."""
    if hasattr(error, 'problem_mark') and error.problem_mark:
        mark = error.problem_mark
        return mark.line + 1, mark.column + 1  # Convert to 1-indexed
    return None, None
```

### User-Friendly Error Messages

```python
from dataclasses import dataclass

@dataclass
class ManifestParseError(Exception):
    """Error parsing manifest YAML."""
    message: str
    line: int | None = None
    column: int | None = None
    problem: str | None = None
    context: str | None = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.line:
            parts.append(f"at line {self.line}, column {self.column}")
        if self.problem:
            parts.append(f"- {self.problem}")
        if self.context:
            parts.append(f"({self.context})")
        return " ".join(parts)
```

### Common Error Types

| Error | Cause | Example |
|-------|-------|---------|
| `ScannerError` | Unclosed quotes | `name: "unclosed` |
| `ScannerError` | Tab characters | `\tvalue: x` |
| `ParserError` | Bad indentation | `name: x\n  bad: y` |
| `ParserError` | Invalid structure | Mixed list/map |
| `DuplicateKeyError` | Repeated keys | `name: a\nname: b` |

## 6. Integration with Pydantic

### Complete Integration Pattern

```python
from __future__ import annotations
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from pydantic import BaseModel, ValidationError
from io import StringIO
from pathlib import Path

class ManifestSerializer:
    """Serialize/deserialize manifests with ordered YAML output."""

    def __init__(self):
        self.yaml = self._create_yaml()

    def _create_yaml(self) -> YAML:
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.width = 120
        yaml.allow_duplicate_keys = False
        return yaml

    def load(self, source: str | Path) -> Manifest:
        """Load and validate manifest from file or string."""
        if isinstance(source, Path):
            content = source.read_text()
            source_name = str(source)
        else:
            content = source
            source_name = "<string>"

        # Parse YAML
        try:
            data = self.yaml.load(StringIO(content))
        except YAMLError as e:
            line, col = self._extract_position(e)
            raise ValueError(
                f"YAML parse error in {source_name}"
                f"{f' at line {line}, column {col}' if line else ''}: "
                f"{getattr(e, 'problem', str(e))}"
            ) from e

        # Validate with Pydantic
        try:
            return Manifest.model_validate(data)
        except ValidationError as e:
            raise ValueError(f"Manifest validation failed: {e}") from e

    def dump(self, manifest: Manifest) -> str:
        """Serialize manifest to ordered YAML string."""
        data = manifest.model_dump(mode='json', exclude_none=True)
        cm = self._to_commented_map(data, 'manifest')

        stream = StringIO()
        self.yaml.dump(cm, stream)
        return stream.getvalue()

    def dump_to_file(self, manifest: Manifest, path: Path) -> None:
        """Write manifest to file."""
        path.write_text(self.dump(manifest))

    def _to_commented_map(self, data: dict, type_hint: str | None) -> CommentedMap:
        """Convert dict to ordered CommentedMap."""
        cm = CommentedMap()
        key_order = KEY_ORDERS.get(type_hint, list(data.keys()))

        ordered_keys = [k for k in key_order if k in data]
        ordered_keys += [k for k in data if k not in ordered_keys]

        for key in ordered_keys:
            value = data[key]
            child_hint = key if key in KEY_ORDERS else None

            if isinstance(value, dict):
                cm[key] = self._to_commented_map(value, child_hint)
            elif isinstance(value, list):
                cs = CommentedSeq()
                item_hint = key.rstrip('s') if key.endswith('s') else None
                for item in value:
                    if isinstance(item, dict):
                        cs.append(self._to_commented_map(item, item_hint))
                    else:
                        cs.append(item)
                cm[key] = cs
            else:
                cm[key] = value

        return cm

    def _extract_position(self, e: YAMLError) -> tuple[int | None, int | None]:
        if hasattr(e, 'problem_mark') and e.problem_mark:
            return e.problem_mark.line + 1, e.problem_mark.column + 1
        return None, None
```

## 7. Complete Working Example

```python
"""Complete round-trip example: create → serialize → parse → validate"""
from __future__ import annotations
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import YAMLError
from pydantic import BaseModel, Field, model_validator, ConfigDict, ValidationError
from typing import Self, Optional
from datetime import datetime, timezone
from enum import Enum
from io import StringIO

# ============== Models ==============

class HookRole(str, Enum):
    PRIMARY = "primary"
    FOREIGN = "foreign"

class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    hook_prefix: str = "_hk"
    weak_hook_prefix: str = "_wk"
    delimiter: str = "__"

class Source(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    relation: Optional[str] = None
    path: Optional[str] = None

    @model_validator(mode='after')
    def check_exclusivity(self) -> Self:
        if (self.relation is None) == (self.path is None):
            raise ValueError("Exactly one of 'relation' or 'path' required")
        return self

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str
    role: HookRole
    concept: Optional[str] = None
    qualifier: Optional[str] = None
    source: Optional[str] = None
    tenant: Optional[str] = None
    expr: Optional[str] = None

class Concept(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str = Field(min_length=1)
    description: Optional[str] = None
    examples: list[str] = Field(default_factory=list)
    is_weak: bool = False

class Frame(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str = Field(min_length=1)
    source: Source
    description: Optional[str] = None
    hooks: list[Hook] = Field(default_factory=list)

class Manifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    manifest_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    metadata: Metadata
    settings: Settings = Field(default_factory=Settings)
    frames: list[Frame] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)

# ============== YAML Utilities ==============

KEY_ORDERS = {
    'manifest': ['manifest_version', 'schema_version', 'metadata', 'settings', 'frames', 'concepts'],
    'metadata': ['name', 'description', 'created_at', 'updated_at'],
    'settings': ['hook_prefix', 'weak_hook_prefix', 'delimiter'],
    'source': ['relation', 'path'],
    'frame': ['name', 'source', 'description', 'hooks'],
    'hook': ['name', 'role', 'concept', 'qualifier', 'source', 'tenant', 'expr'],
    'concept': ['name', 'description', 'examples', 'is_weak'],
}

def create_yaml() -> YAML:
    """Create configured YAML instance."""
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 120
    yaml.allow_duplicate_keys = False
    return yaml

def to_commented_map(data: dict, type_hint: str | None = None) -> CommentedMap:
    """Convert dict to ordered CommentedMap."""
    cm = CommentedMap()
    key_order = KEY_ORDERS.get(type_hint, list(data.keys()))

    ordered_keys = [k for k in key_order if k in data]
    ordered_keys += [k for k in data if k not in ordered_keys]

    for key in ordered_keys:
        value = data[key]
        child_hint = key if key in KEY_ORDERS else None

        if isinstance(value, dict):
            cm[key] = to_commented_map(value, child_hint)
        elif isinstance(value, list):
            cs = CommentedSeq()
            item_hint = key.rstrip('s') if key.endswith('s') else None
            for item in value:
                if isinstance(item, dict):
                    cs.append(to_commented_map(item, item_hint))
                else:
                    cs.append(item)
            cm[key] = cs
        else:
            cm[key] = value

    return cm

def model_to_yaml(model: Manifest) -> str:
    """Convert Manifest to ordered YAML string."""
    data = model.model_dump(mode='json', exclude_none=True)
    cm = to_commented_map(data, 'manifest')
    yaml = create_yaml()
    stream = StringIO()
    yaml.dump(cm, stream)
    return stream.getvalue()

def yaml_to_model(content: str) -> Manifest:
    """Parse YAML and validate as Manifest."""
    yaml = create_yaml()

    try:
        data = yaml.load(StringIO(content))
    except YAMLError as e:
        line = col = None
        if hasattr(e, 'problem_mark') and e.problem_mark:
            line = e.problem_mark.line + 1
            col = e.problem_mark.column + 1
        location = f" at line {line}, column {col}" if line else ""
        raise ValueError(f"YAML parse error{location}: {e.problem or str(e)}") from e

    try:
        return Manifest.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Validation failed: {e}") from e

# ============== Usage Example ==============

if __name__ == "__main__":
    # Create manifest
    manifest = Manifest(
        metadata=Metadata(
            name="my_project",
            description="Example manifest",
            created_at=datetime.now(timezone.utc)
        ),
        frames=[
            Frame(
                name="customers",
                source=Source(relation="raw.customers"),
                hooks=[
                    Hook(name="_hk__customer_id", role=HookRole.PRIMARY, concept="customer"),
                    Hook(name="_hk__region_id", role=HookRole.FOREIGN),
                ]
            )
        ],
        concepts=[
            Concept(name="customer", description="A customer entity"),
        ]
    )

    # Serialize to YAML
    yaml_output = model_to_yaml(manifest)
    print("=== Generated YAML ===")
    print(yaml_output)

    # Parse back and validate
    parsed = yaml_to_model(yaml_output)
    print("=== Parsed Manifest ===")
    print(f"Name: {parsed.metadata.name}")
    print(f"Frames: {len(parsed.frames)}")
    print(f"Concepts: {len(parsed.concepts)}")

    # Verify round-trip
    yaml_output2 = model_to_yaml(parsed)
    assert yaml_output == yaml_output2, "Round-trip mismatch!"
    print("\n✅ Round-trip verified!")
```

### Expected Output

```yaml
manifest_version: 1.0.0
schema_version: 1.0.0
metadata:
  name: my_project
  description: Example manifest
  created_at: '2026-01-06T12:00:00.000000Z'
settings:
  hook_prefix: _hk
  weak_hook_prefix: _wk
  delimiter: __
frames:
  - name: customers
    source:
      relation: raw.customers
    hooks:
      - name: _hk__customer_id
        role: primary
        concept: customer
      - name: _hk__region_id
        role: foreign
concepts:
  - name: customer
    description: A customer entity
    examples: []
    is_weak: false
```

## 8. Advanced Features

### Comment Preservation

ruamel.yaml preserves comments on round-trip:

```python
yaml = YAML()

content = """
# Header comment
manifest_version: 1.0.0  # inline comment
metadata:
  name: test
"""

data = yaml.load(StringIO(content))
# Modify data...
yaml.dump(data, stream)  # Comments preserved!
```

### Adding Comments Programmatically

```python
from ruamel.yaml.comments import CommentedMap

cm = CommentedMap()
cm['version'] = '1.0.0'

# Comment before key
cm.yaml_set_comment_before_after_key('version', before='This is the version')

# End-of-line comment
cm.yaml_add_eol_comment('semantic version', 'version')
```

### Multiline Strings

```python
from ruamel.yaml.scalarstring import LiteralScalarString, FoldedScalarString

cm = CommentedMap()
cm['description'] = LiteralScalarString("line 1\nline 2")  # | style
cm['summary'] = FoldedScalarString("long text\ncontinues")  # > style
```

## 9. Recommendations for Manifest Tool

1. **Use round-trip mode** (default) for all operations
2. **Configure indentation** as `indent(mapping=2, sequence=4, offset=2)`
3. **Disable duplicate keys** with `allow_duplicate_keys = False`
4. **Use `model_dump(mode='json', exclude_none=True)`** for Pydantic serialization
5. **Build `CommentedMap` with explicit key ordering** for deterministic output
6. **Extract line/column from errors** via `problem_mark` attribute
7. **Test round-trip integrity** to ensure serialization is stable

## 10. Testing Checklist

- [x] Installation with `pip install ruamel.yaml`
- [x] Round-trip mode preserves key order
- [x] `CommentedMap` works directly with Pydantic `model_validate()`
- [x] Line/column extraction from parse errors works
- [x] Duplicate key detection works
- [x] Indentation settings produce readable output
- [x] None values can be omitted with `exclude_none=True`
- [x] DateTime parsing compatible with Pydantic
- [x] Complete round-trip (create → serialize → parse → verify) works

## References

- [ruamel.yaml documentation](https://yaml.readthedocs.io/)
- [ruamel.yaml GitHub](https://sourceforge.net/projects/ruamel-yaml/)
- [YAML 1.2 Specification](https://yaml.org/spec/1.2/spec.html)
