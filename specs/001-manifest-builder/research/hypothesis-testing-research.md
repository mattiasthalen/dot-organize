# Hypothesis Property-Based Testing Research

**Date**: 2026-01-06
**Hypothesis Version**: 6.149.x
**Python Version**: 3.12
**Purpose**: Property-based testing for HOOK manifest validation

---

## Table of Contents

1. [Summary](#summary)
2. [Installation and Setup](#1-installation-and-setup)
3. [Basic Usage with @given](#2-basic-usage-with-given)
4. [String Strategies](#3-string-strategies)
5. [Composite Strategies](#4-composite-strategies)
6. [Pydantic Integration](#5-pydantic-integration)
7. [Testing Patterns](#6-testing-patterns)
8. [Best Practices and Configuration](#7-best-practices-and-configuration)
9. [Complete Examples for HOOK Manifest](#8-complete-examples-for-hook-manifest)

---

## Summary

Hypothesis is a property-based testing library that generates random test inputs to find edge cases. Key findings for our manifest validation use case:

| Feature | Approach | Notes |
|---------|----------|-------|
| Installation | `uv add hypothesis --dev` | Include with pytest |
| Regex matching | `st.from_regex(pattern, fullmatch=True)` | Generates matching strings |
| Invalid strings | `st.text().filter(lambda s: not re.match(...))` | Filter out valid patterns |
| Pydantic models | `st.builds(Model, field=strategy)` | Auto-infers from type hints |
| Composite strategies | `@st.composite` decorator | For dependent values |
| Explicit examples | `@example(...)` | Edge cases always tested |
| Settings | `@settings(max_examples=1000)` | Control test runs |

**Regex Patterns to Test**:
```python
LOWER_SNAKE_CASE = r"^[a-z][a-z0-9_]*$"
UPPER_SNAKE_CASE = r"^[A-Z][A-Z0-9_]*$"
HOOK_NAME = r"^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$"
FRAME_NAME = r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$"
SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"  # Use [0-9] not \d to avoid Unicode digits
```

> **Note on Unicode**: When using `st.from_regex()`, Hypothesis generates Unicode strings by default. The `\d` shorthand matches Unicode digit characters (not just 0-9). Use explicit character classes like `[0-9]` or `[a-z]` for ASCII-only matching.

---

## 1. Installation and Setup

### Installing with uv

```bash
# Add hypothesis as a dev dependency
uv add hypothesis --dev

# Or with pytest extras
uv add "hypothesis[pytest]" --dev
```

### Pytest Integration

Hypothesis integrates seamlessly with pytest. No special configuration needed:

```python
# tests/test_validators.py
from hypothesis import given, strategies as st

@given(st.integers())
def test_integers_are_integers(n):
    assert isinstance(n, int)
```

Run with pytest as normal:

```bash
pytest tests/test_validators.py -v
```

### Configuration via conftest.py

```python
# tests/conftest.py
from hypothesis import settings, Phase, Verbosity

# Register custom profiles
settings.register_profile(
    "ci",
    max_examples=1000,
    deadline=None,
    print_blob=True,
)

settings.register_profile(
    "dev",
    max_examples=100,
    deadline=200,  # milliseconds
)

settings.register_profile(
    "debug",
    max_examples=10,
    verbosity=Verbosity.verbose,
)

# Load profile based on environment
import os
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
```

Run with different profiles:

```bash
# Development (fast)
pytest tests/

# CI (thorough)
HYPOTHESIS_PROFILE=ci pytest tests/

# Debugging
HYPOTHESIS_PROFILE=debug pytest tests/
```

---

## 2. Basic Usage with @given

### The @given Decorator

`@given` is the main entry point. It takes strategies that describe input types:

```python
from hypothesis import given, strategies as st

@given(st.integers(), st.text())
def test_multiple_args(n, s):
    assert isinstance(n, int)
    assert isinstance(s, str)

# Keyword arguments work too
@given(name=st.text(min_size=1), age=st.integers(0, 150))
def test_person(name, age):
    assert len(name) >= 1
    assert 0 <= age <= 150
```

### The @example Decorator

Use `@example` to always test specific inputs (edge cases):

```python
from hypothesis import given, example, strategies as st

@example("")           # Empty string
@example("_")          # Single underscore
@example("a" * 1000)   # Very long string
@given(st.text())
def test_string_processing(s):
    result = process_string(s)
    assert isinstance(result, str)
```

### Expected Failures with @example.xfail

```python
from hypothesis import given, example, strategies as st

@example("INVALID_upper").xfail(reason="Upper case not allowed")
@example("123_starts_with_digit").xfail(raises=ValueError)
@given(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))
def test_lower_snake_case(s):
    validate_lower_snake_case(s)
```

### Using assume() for Filtering

```python
from hypothesis import given, assume, strategies as st

@given(st.integers(), st.integers())
def test_division(x, y):
    assume(y != 0)  # Skip if y is 0
    result = x / y
    assert isinstance(result, float)
```

---

## 3. String Strategies

### Generating Strings Matching Regex with st.from_regex()

The `st.from_regex()` strategy generates strings that match a regex pattern:

```python
from hypothesis import given, strategies as st

# Basic usage - generates strings containing a match
@given(st.from_regex(r"[a-z]+"))
def test_contains_lowercase(s):
    assert any(c.islower() for c in s)

# fullmatch=True - entire string must match
@given(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))
def test_lower_snake_case(s):
    assert s[0].islower()
    assert all(c.islower() or c.isdigit() or c == '_' for c in s)
```

### Strategies for HOOK Manifest Patterns

```python
import re
from hypothesis import strategies as st

# Pattern constants
LOWER_SNAKE_CASE = r"^[a-z][a-z0-9_]*$"
UPPER_SNAKE_CASE = r"^[A-Z][A-Z0-9_]*$"
HOOK_NAME = r"^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$"
FRAME_NAME = r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$"
SEMVER = r"^[0-9]+\.[0-9]+\.[0-9]+$"  # Note: Use [0-9] not \d to avoid Unicode digits

# Strategies for valid strings
def valid_lower_snake_case(min_size=1, max_size=50):
    """Generate valid lower_snake_case identifiers."""
    return st.from_regex(LOWER_SNAKE_CASE, fullmatch=True).filter(
        lambda s: min_size <= len(s) <= max_size
    )

def valid_upper_snake_case(min_size=1, max_size=50):
    """Generate valid UPPER_SNAKE_CASE identifiers."""
    return st.from_regex(UPPER_SNAKE_CASE, fullmatch=True).filter(
        lambda s: min_size <= len(s) <= max_size
    )

def valid_hook_name():
    """Generate valid hook names like _hk__customer_id."""
    return st.from_regex(HOOK_NAME, fullmatch=True)

def valid_frame_name():
    """Generate valid frame names like schema.table."""
    return st.from_regex(FRAME_NAME, fullmatch=True)

def valid_semver():
    """Generate valid semantic version strings."""
    return st.from_regex(SEMVER, fullmatch=True)
```

### Generating Invalid Strings (Negative Tests)

For testing that validators correctly reject invalid inputs:

```python
from hypothesis import given, strategies as st
import re

LOWER_SNAKE_CASE = r"^[a-z][a-z0-9_]*$"

def invalid_lower_snake_case():
    """Generate strings that DON'T match lower_snake_case."""
    return st.text(min_size=1).filter(
        lambda s: not re.match(LOWER_SNAKE_CASE, s)
    )

# More targeted invalid strings
def specific_invalid_lower_snake():
    """Generate specific types of invalid lower_snake_case."""
    return st.one_of(
        # Starts with uppercase
        st.from_regex(r"^[A-Z][a-z0-9_]*$", fullmatch=True),
        # Starts with digit
        st.from_regex(r"^[0-9][a-z0-9_]*$", fullmatch=True),
        # Contains uppercase
        st.from_regex(r"^[a-z][a-zA-Z0-9_]*[A-Z][a-zA-Z0-9_]*$", fullmatch=True),
        # Empty string
        st.just(""),
        # Contains special characters
        st.from_regex(r"^[a-z][a-z0-9_]*[-!@#][a-z0-9_]*$", fullmatch=True),
    )

@given(specific_invalid_lower_snake())
def test_rejects_invalid_lower_snake(s):
    assert not is_valid_lower_snake_case(s)
```

### Constraining String Length

```python
from hypothesis import strategies as st

# Using filter (less efficient but works with from_regex)
short_snake = st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True).filter(
    lambda s: 1 <= len(s) <= 20
)

# Using text with alphabet (more efficient for simple cases)
snake_chars = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=1,
    max_size=20
).filter(lambda s: s[0].isalpha())

# Building manually with sampled_from (most control)
first_char = st.sampled_from("abcdefghijklmnopqrstuvwxyz")
rest_chars = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
    min_size=0,
    max_size=19
)
snake_built = st.builds(lambda f, r: f + r, first_char, rest_chars)
```

---

## 4. Composite Strategies

### Using st.builds() for Simple Objects

`st.builds()` calls a constructor with generated arguments:

```python
from hypothesis import given, strategies as st
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Person:
    name: str
    age: int

# Explicit strategies for each field
person_strategy = st.builds(
    Person,
    name=st.text(min_size=1, max_size=50),
    age=st.integers(0, 150)
)

@given(person_strategy)
def test_person_creation(person):
    assert len(person.name) >= 1
    assert 0 <= person.age <= 150
```

### Using @st.composite for Dependent Values

When values depend on each other, use `@st.composite`:

```python
from hypothesis import strategies as st

@st.composite
def hook_with_matching_concept(draw):
    """Generate a hook name that matches its concept."""
    # First draw the concept
    concept = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))

    # Draw the prefix type
    prefix = draw(st.sampled_from(["_hk", "_wk"]))

    # Optionally draw a qualifier
    has_qualifier = draw(st.booleans())

    if has_qualifier:
        qualifier = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))
        hook_name = f"{prefix}__{concept}__{qualifier}"
    else:
        hook_name = f"{prefix}__{concept}"

    return {
        "hook_name": hook_name,
        "concept": concept,
        "prefix": prefix,
        "qualifier": qualifier if has_qualifier else None
    }

@given(hook_with_matching_concept())
def test_hook_concept_relationship(data):
    assert data["concept"] in data["hook_name"]
```

### Building Key Sets with @st.composite

```python
from hypothesis import strategies as st
from typing import Optional

@st.composite
def key_set_components(draw):
    """Generate components for key set derivation: CONCEPT[~QUALIFIER]@SOURCE[~TENANT]"""
    concept = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))

    # Optional qualifier
    qualifier: Optional[str] = None
    if draw(st.booleans()):
        qualifier = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))

    # Source is required
    source = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))

    # Optional tenant
    tenant: Optional[str] = None
    if draw(st.booleans()):
        tenant = draw(st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True))

    # Build expected key set
    key = concept
    if qualifier:
        key += f"~{qualifier}"
    key += f"@{source}"
    if tenant:
        key += f"~{tenant}"

    return {
        "concept": concept,
        "qualifier": qualifier,
        "source": source,
        "tenant": tenant,
        "expected_key": key
    }

@given(key_set_components())
def test_key_set_derivation(components):
    """Property: key set derivation is deterministic."""
    result = derive_key_set(
        concept=components["concept"],
        qualifier=components["qualifier"],
        source=components["source"],
        tenant=components["tenant"]
    )
    assert result == components["expected_key"]
```

---

## 5. Pydantic Integration

### Using st.builds() with Pydantic Models

```python
from hypothesis import given, strategies as st
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Strategy for valid Metadata
metadata_strategy = st.builds(
    Metadata,
    name=st.text(min_size=1, max_size=100).filter(lambda s: s.strip()),
    description=st.one_of(st.none(), st.text(max_size=500)),
    created_at=st.datetimes(),
    updated_at=st.one_of(st.none(), st.datetimes())
)

@given(metadata_strategy)
def test_metadata_is_valid(metadata):
    assert len(metadata.name) >= 1
    assert len(metadata.name) <= 100
```

### Handling Frozen Models

Frozen models work fine with `st.builds()` since we construct, not mutate:

```python
from hypothesis import given, strategies as st
from pydantic import BaseModel, ConfigDict, ValidationError
import pytest

class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    hook_prefix: str = "_hk"
    weak_hook_prefix: str = "_wk"
    delimiter: str = "__"

# Default values can be omitted or explicitly provided
settings_strategy = st.builds(
    Settings,
    hook_prefix=st.just("_hk"),  # Or omit to use default
    weak_hook_prefix=st.just("_wk"),
    delimiter=st.just("__")
)

# Test that frozen models are indeed frozen
@given(settings_strategy)
def test_settings_frozen(settings):
    with pytest.raises(ValidationError):
        settings.hook_prefix = "_new"  # Should fail
```

### Testing Model Validators

```python
from hypothesis import given, strategies as st
from pydantic import BaseModel, ConfigDict, model_validator, ValidationError
from typing import Self, Optional
import pytest

class Source(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    relation: Optional[str] = None
    path: Optional[str] = None

    @model_validator(mode='after')
    def check_exclusivity(self) -> Self:
        if (self.relation is None) == (self.path is None):
            raise ValueError("Exactly one of 'relation' or 'path' required")
        return self

# Strategy for valid Source (exactly one field set)
valid_source_strategy = st.one_of(
    st.builds(Source, relation=st.text(min_size=1), path=st.none()),
    st.builds(Source, relation=st.none(), path=st.text(min_size=1))
)

# Strategy for invalid Source (both or neither set)
invalid_source_strategy = st.one_of(
    # Both set
    st.fixed_dictionaries({
        "relation": st.text(min_size=1),
        "path": st.text(min_size=1)
    }),
    # Neither set
    st.fixed_dictionaries({
        "relation": st.none(),
        "path": st.none()
    })
)

@given(valid_source_strategy)
def test_valid_source_accepted(source):
    """Valid sources should be created without error."""
    assert (source.relation is None) != (source.path is None)

@given(invalid_source_strategy)
def test_invalid_source_rejected(data):
    """Invalid sources should raise ValidationError."""
    with pytest.raises(ValidationError):
        Source(**data)
```

### Complete Model Strategy with Nested Types

```python
from hypothesis import given, strategies as st
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum

class HookRole(str, Enum):
    PRIMARY = "primary"
    FOREIGN = "foreign"

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str
    role: HookRole
    concept: Optional[str] = None
    qualifier: Optional[str] = None
    source: Optional[str] = None
    tenant: Optional[str] = None
    expr: Optional[str] = None

# Strategy for valid hooks
def hook_strategy():
    return st.builds(
        Hook,
        name=st.from_regex(r"^_(hk|wk)__[a-z][a-z0-9_]*$", fullmatch=True),
        role=st.sampled_from(HookRole),
        concept=st.one_of(
            st.none(),
            st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True)
        ),
        qualifier=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
        source=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        tenant=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
        expr=st.one_of(st.none(), st.text(max_size=200))
    )
```

---

## 6. Testing Patterns

### Property: Valid Input → No Validation Errors

```python
from hypothesis import given, settings
import pytest

@settings(max_examples=500)
@given(valid_lower_snake_case())
def test_valid_lower_snake_accepted(s):
    """Property: valid lower_snake_case should never raise."""
    result = validate_lower_snake_case(s)  # Should not raise
    assert result is True
```

### Property: Invalid Input → Expected Errors

```python
from hypothesis import given
import pytest

@given(invalid_lower_snake_case())
def test_invalid_lower_snake_rejected(s):
    """Property: invalid input should raise ValueError."""
    with pytest.raises(ValueError, match="must be lower_snake_case"):
        validate_lower_snake_case(s)
```

### Property: Deterministic Functions

```python
from hypothesis import given

@given(key_set_components())
def test_key_set_derivation_deterministic(components):
    """Property: same inputs always produce same output."""
    result1 = derive_key_set(**components)
    result2 = derive_key_set(**components)
    assert result1 == result2
```

### Property: Round-Trip Serialization

```python
from hypothesis import given, settings

@settings(max_examples=200)
@given(manifest_strategy())
def test_yaml_round_trip(manifest):
    """Property: serialize → deserialize preserves data."""
    yaml_str = model_to_yaml(manifest)
    parsed = yaml_to_model(yaml_str)

    # Compare as dicts to avoid datetime precision issues
    assert manifest.model_dump() == parsed.model_dump()
```

### Property: Idempotent Operations

```python
from hypothesis import given

@given(st.text())
def test_normalize_idempotent(s):
    """Property: normalizing twice equals normalizing once."""
    once = normalize(s)
    twice = normalize(normalize(s))
    assert once == twice
```

### Property: Inverse Operations

```python
from hypothesis import given

@given(manifest_strategy())
def test_serialize_deserialize_inverse(manifest):
    """Property: serialize and deserialize are inverses."""
    serialized = serialize(manifest)
    deserialized = deserialize(serialized)
    reserialized = serialize(deserialized)
    assert serialized == reserialized
```

---

## 7. Best Practices and Configuration

### How Many Examples to Run?

| Context | max_examples | Use Case |
|---------|--------------|----------|
| Local dev | 50-100 | Quick feedback during development |
| CI pipeline | 500-1000 | Thorough testing, catch rare bugs |
| Pre-release | 5000-10000 | Extra confidence before release |
| Debugging | 10-20 | Fast iteration with verbose output |

```python
from hypothesis import settings

# Quick local testing
@settings(max_examples=50)
@given(...)
def test_fast(x):
    pass

# Thorough CI testing
@settings(max_examples=1000, deadline=None)
@given(...)
def test_thorough(x):
    pass
```

### Handling Flaky Tests

Flaky tests usually indicate non-determinism in your code:

```python
from hypothesis import settings, HealthCheck

# Suppress specific health checks
@settings(
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.filter_too_much
    ]
)
@given(...)
def test_might_be_slow(x):
    pass

# Disable deadline for timing-sensitive tests
@settings(deadline=None)
@given(...)
def test_variable_timing(x):
    pass

# Derandomize for reproducibility
@settings(derandomize=True)
@given(...)
def test_deterministic(x):
    pass
```

### Using @example for Known Edge Cases

Always include edge cases that you've discovered or designed for:

```python
from hypothesis import given, example

# Boundary conditions
@example("")
@example("a")
@example("a" * 100)
# Known problematic inputs
@example("__double__underscore")
@example("123_starts_with_digit")
@example("UPPERCASE")
# Unicode edge cases
@example("café")
@example("日本語")
@given(st.text())
def test_string_handling(s):
    result = process(s)
    assert_valid(result)
```

### Shrinking Failing Cases

Hypothesis automatically shrinks failing examples to minimal reproductions:

```python
# If this fails with a complex input like:
# "abcdefghijklmnop123_456_789"
# Hypothesis will try to shrink it to something like:
# "a0"
# (the smallest input that still triggers the bug)

@given(st.text(min_size=1))
def test_something(s):
    assert some_condition(s)

# The failing example printed will be minimal
```

### Database for Reproducibility

Hypothesis saves failing examples to replay on future runs:

```python
from hypothesis import settings
from hypothesis.database import DirectoryBasedExampleDatabase

# Custom database location
@settings(database=DirectoryBasedExampleDatabase(".hypothesis/examples"))
@given(...)
def test_with_database(x):
    pass

# Disable database (for ephemeral tests)
@settings(database=None)
@given(...)
def test_no_database(x):
    pass
```

---

## 8. Complete Examples for HOOK Manifest

### Naming Convention Validators

```python
"""
Test module for naming convention validators.
File: tests/test_validators.py
"""
import re
from hypothesis import given, example, settings, strategies as st
import pytest

# Patterns to test
PATTERNS = {
    "lower_snake": r"^[a-z][a-z0-9_]*$",
    "upper_snake": r"^[A-Z][A-Z0-9_]*$",
    "hook_name": r"^_(hk|wk)__[a-z][a-z0-9_]*(__[a-z][a-z0-9_]*)?$",
    "frame_name": r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$",
    "semver": r"^[0-9]+\.[0-9]+\.[0-9]+$",  # Use [0-9] not \d to avoid Unicode
}

# Validators under test
def is_lower_snake_case(s: str) -> bool:
    return bool(re.match(PATTERNS["lower_snake"], s))

def is_upper_snake_case(s: str) -> bool:
    return bool(re.match(PATTERNS["upper_snake"], s))

def is_valid_hook_name(s: str) -> bool:
    return bool(re.match(PATTERNS["hook_name"], s))

def is_valid_frame_name(s: str) -> bool:
    return bool(re.match(PATTERNS["frame_name"], s))

def is_valid_semver(s: str) -> bool:
    return bool(re.match(PATTERNS["semver"], s))


# ============== Strategy Definitions ==============

# Valid patterns
valid_lower_snake = st.from_regex(PATTERNS["lower_snake"], fullmatch=True)
valid_upper_snake = st.from_regex(PATTERNS["upper_snake"], fullmatch=True)
valid_hook_name = st.from_regex(PATTERNS["hook_name"], fullmatch=True)
valid_frame_name = st.from_regex(PATTERNS["frame_name"], fullmatch=True)
valid_semver = st.from_regex(PATTERNS["semver"], fullmatch=True)

# Invalid patterns (strings that don't match)
invalid_lower_snake = st.one_of(
    st.just(""),                                    # Empty
    st.from_regex(r"^[A-Z][a-z]*$", fullmatch=True),  # Starts upper
    st.from_regex(r"^[0-9][a-z]*$", fullmatch=True),  # Starts digit
    st.from_regex(r"^[a-z]*[A-Z][a-z]*$", fullmatch=True),  # Contains upper
    st.just("has-dash"),                            # Contains dash
    st.just("has space"),                           # Contains space
)


# ============== Tests for lower_snake_case ==============

class TestLowerSnakeCase:

    @example("a")
    @example("abc")
    @example("abc_def")
    @example("abc_123")
    @example("a1b2c3")
    @given(valid_lower_snake)
    def test_valid_lower_snake_accepted(self, s):
        """Property: valid lower_snake_case strings pass validation."""
        assert is_lower_snake_case(s) is True

    @example("")
    @example("A")
    @example("ABC")
    @example("Abc")
    @example("1abc")
    @example("abc-def")
    @example("abc def")
    @given(invalid_lower_snake)
    def test_invalid_lower_snake_rejected(self, s):
        """Property: invalid strings fail validation."""
        assert is_lower_snake_case(s) is False

    @given(st.text())
    def test_lower_snake_returns_bool(self, s):
        """Property: validator always returns a boolean."""
        result = is_lower_snake_case(s)
        assert isinstance(result, bool)


# ============== Tests for hook_name ==============

class TestHookName:

    @example("_hk__customer_id")
    @example("_wk__order_id")
    @example("_hk__customer__region")
    @example("_wk__product__category")
    @given(valid_hook_name)
    def test_valid_hook_name_accepted(self, s):
        """Property: valid hook names pass validation."""
        assert is_valid_hook_name(s) is True

    @example("")
    @example("hk__customer")      # Missing leading underscore
    @example("_hk_customer")      # Single underscore separator
    @example("_xx__customer")     # Invalid prefix
    @example("_hk__Customer")     # Uppercase in concept
    @example("_hk__123")          # Starts with digit
    @given(st.text().filter(lambda s: not re.match(PATTERNS["hook_name"], s)))
    @settings(max_examples=200)
    def test_invalid_hook_name_rejected(self, s):
        """Property: invalid hook names fail validation."""
        assert is_valid_hook_name(s) is False


# ============== Tests for semver ==============

class TestSemver:

    @example("0.0.0")
    @example("1.0.0")
    @example("1.2.3")
    @example("10.20.30")
    @example("999.999.999")
    @given(valid_semver)
    def test_valid_semver_accepted(self, s):
        """Property: valid semver strings pass validation."""
        assert is_valid_semver(s) is True

    @example("")
    @example("1")
    @example("1.2")
    @example("1.2.3.4")
    @example("v1.2.3")
    @example("1.2.3-beta")
    @given(st.text().filter(lambda s: not re.match(PATTERNS["semver"], s)))
    @settings(max_examples=100)
    def test_invalid_semver_rejected(self, s):
        """Property: invalid semver strings fail validation."""
        assert is_valid_semver(s) is False
```

### Key Set Derivation Tests

```python
"""
Test module for key set derivation.
File: tests/test_key_set.py
"""
from hypothesis import given, example, strategies as st
from typing import Optional


def derive_key_set(
    concept: str,
    source: str,
    qualifier: Optional[str] = None,
    tenant: Optional[str] = None
) -> str:
    """
    Derive a key set string: CONCEPT[~QUALIFIER]@SOURCE[~TENANT]

    Examples:
        - customer@orders
        - customer~region@orders
        - customer@orders~tenant1
        - customer~region@orders~tenant1
    """
    key = concept
    if qualifier:
        key += f"~{qualifier}"
    key += f"@{source}"
    if tenant:
        key += f"~{tenant}"
    return key


# ============== Strategies ==============

identifier = st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True).filter(
    lambda s: 1 <= len(s) <= 30
)

@st.composite
def key_set_components(draw):
    """Generate all components for a key set."""
    return {
        "concept": draw(identifier),
        "source": draw(identifier),
        "qualifier": draw(st.one_of(st.none(), identifier)),
        "tenant": draw(st.one_of(st.none(), identifier)),
    }


# ============== Tests ==============

class TestKeySetDerivation:

    @given(key_set_components())
    def test_derivation_is_deterministic(self, components):
        """Property: same inputs always produce same output."""
        result1 = derive_key_set(**components)
        result2 = derive_key_set(**components)
        assert result1 == result2

    @given(key_set_components())
    def test_concept_in_result(self, components):
        """Property: concept is always in the result."""
        result = derive_key_set(**components)
        assert result.startswith(components["concept"])

    @given(key_set_components())
    def test_source_in_result(self, components):
        """Property: source is always in the result after @."""
        result = derive_key_set(**components)
        assert f"@{components['source']}" in result

    @given(key_set_components())
    def test_qualifier_when_present(self, components):
        """Property: qualifier appears with ~ when provided."""
        result = derive_key_set(**components)
        if components["qualifier"]:
            assert f"~{components['qualifier']}" in result
            # Should appear before @
            at_pos = result.index("@")
            qual_pos = result.index(f"~{components['qualifier']}")
            assert qual_pos < at_pos

    @given(key_set_components())
    def test_tenant_when_present(self, components):
        """Property: tenant appears with ~ at end when provided."""
        result = derive_key_set(**components)
        if components["tenant"]:
            assert result.endswith(f"~{components['tenant']}")

    @example({"concept": "customer", "source": "orders", "qualifier": None, "tenant": None})
    @example({"concept": "customer", "source": "orders", "qualifier": "region", "tenant": None})
    @example({"concept": "customer", "source": "orders", "qualifier": None, "tenant": "tenant1"})
    @example({"concept": "customer", "source": "orders", "qualifier": "region", "tenant": "tenant1"})
    @given(key_set_components())
    def test_format_matches_specification(self, components):
        """Property: result matches CONCEPT[~QUALIFIER]@SOURCE[~TENANT] format."""
        result = derive_key_set(**components)

        # Build expected result
        expected = components["concept"]
        if components["qualifier"]:
            expected += f"~{components['qualifier']}"
        expected += f"@{components['source']}"
        if components["tenant"]:
            expected += f"~{components['tenant']}"

        assert result == expected
```

### Model Serialization Round-Trip Tests

```python
"""
Test module for YAML serialization round-trip.
File: tests/test_serialization.py
"""
from hypothesis import given, settings, strategies as st
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
from io import StringIO
from ruamel.yaml import YAML


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

class Hook(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str
    role: HookRole
    concept: Optional[str] = None

class Concept(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    name: str = Field(min_length=1)
    description: Optional[str] = None
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


# ============== Serialization Functions ==============

def model_to_yaml(model: Manifest) -> str:
    yaml = YAML()
    yaml.default_flow_style = False
    data = model.model_dump(mode='json', exclude_none=True)
    stream = StringIO()
    yaml.dump(data, stream)
    return stream.getvalue()

def yaml_to_model(content: str) -> Manifest:
    yaml = YAML()
    data = yaml.load(StringIO(content))
    return Manifest.model_validate(data)


# ============== Strategies ==============

valid_identifier = st.from_regex(r"^[a-z][a-z0-9_]*$", fullmatch=True).filter(
    lambda s: 1 <= len(s) <= 30
)

valid_hook_name_str = st.from_regex(
    r"^_(hk|wk)__[a-z][a-z0-9_]*$", fullmatch=True
)

# Build up from simple to complex
metadata_strategy = st.builds(
    Metadata,
    name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_"),
    description=st.one_of(st.none(), st.text(max_size=100)),
    created_at=st.datetimes(timezones=st.just(timezone.utc)),
    updated_at=st.none(),  # Keep simple for round-trip
)

hook_strategy = st.builds(
    Hook,
    name=valid_hook_name_str,
    role=st.sampled_from(HookRole),
    concept=st.one_of(st.none(), valid_identifier),
)

source_strategy = st.one_of(
    st.builds(Source, relation=valid_identifier, path=st.none()),
    st.builds(Source, relation=st.none(), path=st.text(min_size=1, max_size=50)),
)

frame_strategy = st.builds(
    Frame,
    name=valid_identifier,
    source=source_strategy,
    description=st.one_of(st.none(), st.text(max_size=100)),
    hooks=st.lists(hook_strategy, max_size=3),
)

concept_strategy = st.builds(
    Concept,
    name=valid_identifier,
    description=st.one_of(st.none(), st.text(max_size=100)),
    is_weak=st.booleans(),
)

manifest_strategy = st.builds(
    Manifest,
    manifest_version=st.just("1.0.0"),
    schema_version=st.just("1.0.0"),
    metadata=metadata_strategy,
    settings=st.just(Settings()),
    frames=st.lists(frame_strategy, max_size=2),
    concepts=st.lists(concept_strategy, max_size=2),
)


# ============== Tests ==============

class TestSerializationRoundTrip:

    @settings(max_examples=100)
    @given(manifest_strategy)
    def test_yaml_round_trip_preserves_data(self, manifest):
        """Property: serialize → deserialize preserves all data."""
        yaml_str = model_to_yaml(manifest)
        parsed = yaml_to_model(yaml_str)

        # Compare model dumps
        original = manifest.model_dump(mode='json')
        roundtrip = parsed.model_dump(mode='json')

        assert original == roundtrip

    @settings(max_examples=50)
    @given(manifest_strategy)
    def test_serialization_produces_valid_yaml(self, manifest):
        """Property: serialization always produces parseable YAML."""
        yaml_str = model_to_yaml(manifest)

        # Should not raise
        yaml = YAML()
        data = yaml.load(StringIO(yaml_str))

        assert isinstance(data, dict)
        assert "metadata" in data

    @settings(max_examples=50)
    @given(manifest_strategy)
    def test_double_serialization_is_idempotent(self, manifest):
        """Property: serialize twice produces identical output."""
        yaml1 = model_to_yaml(manifest)
        parsed = yaml_to_model(yaml1)
        yaml2 = model_to_yaml(parsed)

        assert yaml1 == yaml2
```

---

## Running the Tests

```bash
# Run all hypothesis tests
pytest tests/ -v

# Run with more examples
HYPOTHESIS_PROFILE=ci pytest tests/ -v

# Run with verbose output for debugging
HYPOTHESIS_PROFILE=debug pytest tests/ -v

# Run specific test class
pytest tests/test_validators.py::TestLowerSnakeCase -v

# Show hypothesis statistics
pytest tests/ --hypothesis-show-statistics
```

---

## Key Takeaways

1. **Use `st.from_regex(pattern, fullmatch=True)`** for generating strings that match your patterns
2. **Use `st.one_of()` or `.filter()`** for generating invalid inputs
3. **Use `st.builds()`** for Pydantic models - it works great with frozen models
4. **Use `@st.composite`** when values depend on each other
5. **Always include `@example()` decorators** for known edge cases
6. **Configure profiles** for different testing scenarios (dev/CI/debug)
7. **Test properties, not specific values**: "valid input → no error", "round-trip preserves data"
8. **Let Hypothesis shrink** failing cases to minimal reproductions
