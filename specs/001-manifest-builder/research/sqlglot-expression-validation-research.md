# sqlglot Expression Validation Research

**Date**: 2026-01-07  
**sqlglot Version**: 28.5.0  
**Python Version**: 3.12  
**Purpose**: Research SQL expression parsing for HOOK manifest `expr` field validation

---

## Table of Contents

1. [Summary](#summary)
2. [Why sqlglot?](#1-why-sqlglot)
3. [Dialect-Agnostic Parsing](#2-dialect-agnostic-parsing)
4. [Expression vs Statement Detection](#3-expression-vs-statement-detection)
5. [Forbidden Pattern Detection](#4-forbidden-pattern-detection)
6. [Qlik Expression Compatibility](#5-qlik-expression-compatibility)
7. [Custom Function Handling](#6-custom-function-handling)
8. [Warning Detection](#7-warning-detection)
9. [Dialect Transpilation](#8-dialect-transpilation)
10. [Recommended Validation Function](#9-recommended-validation-function)
11. [Integration with HOOK-006](#10-integration-with-hook-006)

---

## Summary

sqlglot is the ideal tool for validating hook expressions in the manifest builder. Key findings:

| Feature | Approach | Notes |
|---------|----------|-------|
| Parsing | `sqlglot.parse_one(expr)` | No dialect = generic SQL |
| Statement rejection | Check `isinstance(parsed, exp.Select)` | Reject full SQL statements |
| Subquery detection | `parsed.find(exp.Select)` | Detect embedded SELECT |
| Qlik compatibility | Works! `&`, `If()`, `Len()` all parse | Parsed as SQL equivalents |
| Custom functions | Accepted as `Anonymous` nodes | Permissive by design |
| Dialect transpilation | `parsed.sql(dialect='snowflake')` | Future generators can use |
| No dialect needed | Generic parser handles common syntax | Best for manifest validation |

**Recommendation**: Use `sqlglot.parse_one()` with **no dialect** for manifest validation. This provides syntax validation without assuming a target platform.

---

## 1. Why sqlglot?

### Problem

The HOOK manifest `expr` field contains SQL expressions like:
- `customer_id`
- `UPPER(customer_id) || '-' || order_id`
- `CASE WHEN status = 'A' THEN 'Active' ELSE 'Inactive' END`

We need to validate these expressions are:
1. Syntactically correct
2. Pure expressions (not full SQL statements)
3. Free of forbidden patterns (SELECT, INSERT, subqueries)

### Why Not Regex?

Regex-based validation is fragile:
- Hard to match balanced parentheses
- Can't distinguish `SELECT` in column name vs keyword
- Doesn't catch syntax errors like `CASE WHEN x THEN y` (missing END)

### Why sqlglot?

sqlglot is a mature SQL parser that:
- Parses expressions into an AST
- Supports 20+ SQL dialects
- Can detect statement types (SELECT vs expression)
- Is widely used (Databricks, Airbnb, etc.)

```bash
pip install sqlglot
```

---

## 2. Dialect-Agnostic Parsing

### Key Finding: No Dialect Required

When you call `parse_one()` without specifying a dialect, sqlglot uses a generic SQL parser that accepts common syntax:

```python
from sqlglot import parse_one

# No dialect = generic SQL
expr = "COALESCE(customer_id, 'UNKNOWN') || '-' || UPPER(source)"
parsed = parse_one(expr)

print(type(parsed).__name__)  # DPipe
print(parsed.sql())  # COALESCE(customer_id, 'UNKNOWN') || '-' || UPPER(source)
```

### Tested Expressions

| Expression | Parses? | Node Type |
|------------|---------|-----------|
| `customer_id` | ✅ | Column |
| `UPPER(customer_id)` | ✅ | Upper |
| `customer_id \|\| '-' \|\| order_id` | ✅ | DPipe |
| `COALESCE(customer_id, 'UNKNOWN')` | ✅ | Coalesce |
| `CASE WHEN status = 'A' THEN 'Active' ELSE 'Inactive' END` | ✅ | Case |
| `CAST(order_date AS DATE)` | ✅ | Cast |
| `1 + 2 * 3` | ✅ | Add |

All common expression patterns parse correctly without specifying a dialect.

---

## 3. Expression vs Statement Detection

### Expressions vs Statements

- **Expression**: Evaluates to a value (`customer_id`, `1 + 2`, `UPPER(name)`)
- **Statement**: Performs an action (`SELECT ...`, `INSERT ...`, `DELETE ...`)

Hook expressions MUST be expressions, not statements.

### Detection Method

```python
from sqlglot import parse_one, exp

def is_pure_expression(expr_str: str) -> bool:
    """Check if string is a pure expression, not a SQL statement."""
    try:
        parsed = parse_one(expr_str)
    except Exception:
        return False
    
    # Statement types that are NOT allowed
    statement_types = (
        exp.Select,
        exp.Insert, 
        exp.Update, 
        exp.Delete,
        exp.Create, 
        exp.Drop, 
        exp.Alter,
    )
    
    return not isinstance(parsed, statement_types)
```

### Test Results

| Input | Is Expression? | Reason |
|-------|----------------|--------|
| `customer_id` | ✅ Yes | Column reference |
| `UPPER(name) \|\| '-' \|\| id` | ✅ Yes | Concatenation |
| `SELECT id FROM table` | ❌ No | Select statement |
| `INSERT INTO t VALUES (1)` | ❌ No | Insert statement |
| `customer_id FROM customers` | ❌ No | Parse error (invalid syntax) |

---

## 4. Forbidden Pattern Detection

### Subquery Detection

Even if an expression contains a subquery, we can detect it:

```python
from sqlglot import parse_one, exp

def contains_subquery(expr_str: str) -> bool:
    """Check if expression contains embedded SELECT."""
    try:
        parsed = parse_one(expr_str)
        return parsed.find(exp.Select) is not None
    except Exception:
        return False

# Test
print(contains_subquery("(SELECT MAX(id) FROM orders)"))  # True
print(contains_subquery("customer_id"))  # False
```

### Test Results

| Input | Contains Subquery? |
|-------|-------------------|
| `customer_id` | ❌ No |
| `(SELECT MAX(id) FROM orders)` | ✅ Yes |
| `COALESCE(customer_id, (SELECT default_id FROM config))` | ✅ Yes |

---

## 5. Qlik Expression Compatibility

### Key Finding: Qlik Expressions Parse as SQL Equivalents

Even though Qlik uses different syntax, many Qlik expressions parse successfully:

```python
from sqlglot import parse_one

qlik_exprs = [
    ("customer_id & '-' & order_id", "BitwiseAnd"),  # Qlik uses & for concat
    ("If(x=1, 'A', 'B')", "If"),                     # Qlik If function
    ("Len(customer_id)", "Length"),                   # Qlik Len = SQL Length
    ("Left(name, 5)", "Left"),                        # Same in both
]

for expr, expected_type in qlik_exprs:
    parsed = parse_one(expr)
    print(f"'{expr}' -> {type(parsed).__name__}")
```

### Results

| Qlik Expression | Parses? | Node Type | Notes |
|-----------------|---------|-----------|-------|
| `customer_id & '-' & order_id` | ✅ | BitwiseAnd | `&` parsed as bitwise AND (different semantics!) |
| `If(x=1, 'A', 'B')` | ✅ | If | Works as expected |
| `Len(customer_id)` | ✅ | Length | Recognized as Length function |
| `Left(name, 5)` | ✅ | Left | Same in SQL and Qlik |

### Implication for Feature 001

Feature 001 is **SQL-only** per FR-034a:
> "Hook `expr` is a SQL expression (Manifest SQL subset) for Feature 001. Qlik expression support may be introduced in a later feature."

For now, we validate as SQL. Qlik support in a future feature may need dialect-specific validation.

---

## 6. Custom Function Handling

### Key Finding: Unknown Functions Are Accepted

sqlglot is permissive with unknown functions, parsing them as `Anonymous` nodes:

```python
from sqlglot import parse_one

custom_funcs = [
    "MY_CUSTOM_FUNC(x, y)",
    "dbo.GetCustomerId(x)",
    "HASH_MD5(customer_id)",
]

for expr in custom_funcs:
    parsed = parse_one(expr)
    print(f"'{expr}' -> {type(parsed).__name__}")
```

### Results

| Expression | Node Type | Accepted? |
|------------|-----------|-----------|
| `MY_CUSTOM_FUNC(x, y)` | Anonymous | ✅ Yes |
| `dbo.GetCustomerId(x)` | Dot | ✅ Yes |
| `HASH_MD5(customer_id)` | Anonymous | ✅ Yes |

This is good for validation—we don't need to enumerate all allowed functions.

---

## 7. Warning Detection

### Detecting Potential Issues

We can walk the AST to detect patterns that should trigger warnings:

```python
from sqlglot import parse_one, exp

def check_expression_warnings(expr_str: str) -> list[str]:
    """Check for patterns that should trigger warnings."""
    warnings = []
    
    try:
        parsed = parse_one(expr_str)
    except Exception:
        return []  # Parse errors handled separately
    
    # COALESCE may mask nulls (Constitution §II concern for future generators)
    if parsed.find(exp.Coalesce):
        warnings.append("COALESCE may mask null values")
    
    # Non-deterministic functions
    non_deterministic = {'GETDATE', 'NOW', 'RANDOM', 'NEWID', 'UUID', 
                         'CURRENT_TIMESTAMP', 'SYSDATE', 'RAND'}
    
    for node in parsed.walk():
        if isinstance(node, (exp.Anonymous, exp.Func)):
            func_name = getattr(node, 'name', '') or str(node.this) if hasattr(node, 'this') else ''
            if func_name.upper() in non_deterministic:
                warnings.append(f"Non-deterministic function: {func_name}")
    
    return warnings
```

### Test Results

| Expression | Warnings |
|------------|----------|
| `customer_id` | None |
| `COALESCE(customer_id, 'DEFAULT')` | "COALESCE may mask null values" |
| `GETDATE()` | "Non-deterministic function: GETDATE" |

---

## 8. Dialect Transpilation

### Future Use: Generator Transpilation

When we build SQL generators, we can transpile expressions to target dialects:

```python
from sqlglot import parse_one

expr = "customer_id || order_id"
parsed = parse_one(expr)

# Transpile to different dialects
print(parsed.sql(dialect='duckdb'))     # customer_id || order_id
print(parsed.sql(dialect='snowflake'))  # customer_id || order_id
print(parsed.sql(dialect='tsql'))       # customer_id + order_id  (TSQL uses + for concat)
print(parsed.sql(dialect='bigquery'))   # customer_id || order_id
```

### Dialect Differences

| Expression | DuckDB | Snowflake | TSQL | BigQuery |
|------------|--------|-----------|------|----------|
| `a \|\| b` | `a \|\| b` | `a \|\| b` | `a + b` | `a \|\| b` |

This is handled by future generators, not manifest validation.

---

## 9. Recommended Validation Function

### Complete Implementation for HOOK-006

```python
from sqlglot import parse_one, exp
from dataclasses import dataclass
from enum import Enum

class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"

@dataclass(frozen=True)
class Diagnostic:
    rule_id: str
    severity: Severity
    message: str
    path: str
    fix: str

def validate_hook_expr(
    expr: str, 
    path: str = "expr"
) -> list[Diagnostic]:
    """
    Validate hook expression using sqlglot.
    
    Returns list of diagnostics (empty if valid).
    """
    diagnostics: list[Diagnostic] = []
    
    # Check non-empty
    if not expr or not expr.strip():
        diagnostics.append(Diagnostic(
            rule_id="HOOK-006",
            severity=Severity.ERROR,
            message="Hook expression must not be empty",
            path=path,
            fix="Add a valid SQL expression for the business key"
        ))
        return diagnostics
    
    # Try to parse
    try:
        parsed = parse_one(expr)
    except Exception as e:
        diagnostics.append(Diagnostic(
            rule_id="HOOK-006",
            severity=Severity.ERROR,
            message=f"Invalid expression syntax: {e}",
            path=path,
            fix="Fix the SQL expression syntax"
        ))
        return diagnostics
    
    # Reject SQL statements
    statement_types = (
        exp.Select, exp.Insert, exp.Update, exp.Delete,
        exp.Create, exp.Drop, exp.Alter
    )
    if isinstance(parsed, statement_types):
        diagnostics.append(Diagnostic(
            rule_id="HOOK-006",
            severity=Severity.ERROR,
            message=f"Expression must not be a {type(parsed).__name__} statement",
            path=path,
            fix="Use a pure SQL expression, not a statement"
        ))
        return diagnostics
    
    # Reject subqueries
    if parsed.find(exp.Select):
        diagnostics.append(Diagnostic(
            rule_id="HOOK-006",
            severity=Severity.ERROR,
            message="Expression must not contain subqueries",
            path=path,
            fix="Remove subquery and use a direct column reference or expression"
        ))
        return diagnostics
    
    # Check for non-deterministic functions (warning only)
    non_deterministic = {'GETDATE', 'NOW', 'RANDOM', 'NEWID', 'UUID',
                         'CURRENT_TIMESTAMP', 'SYSDATE', 'RAND'}
    
    for node in parsed.walk():
        if isinstance(node, (exp.Anonymous, exp.Func)):
            func_name = getattr(node, 'name', '')
            if not func_name and hasattr(node, 'this'):
                func_name = str(node.this)
            if func_name.upper() in non_deterministic:
                diagnostics.append(Diagnostic(
                    rule_id="HOOK-W02",
                    severity=Severity.WARN,
                    message=f"Non-deterministic function '{func_name}' may cause inconsistent results",
                    path=path,
                    fix="Consider using a deterministic expression for hook values"
                ))
    
    return diagnostics
```

### Test Cases

```python
# Valid expressions
assert validate_hook_expr("customer_id") == []
assert validate_hook_expr("UPPER(name) || '-' || id") == []
assert validate_hook_expr("CASE WHEN x = 1 THEN 'A' ELSE 'B' END") == []

# Invalid: empty
assert len(validate_hook_expr("")) == 1
assert validate_hook_expr("")[0].rule_id == "HOOK-006"

# Invalid: SQL statement
assert len(validate_hook_expr("SELECT id FROM table")) == 1

# Invalid: subquery
assert len(validate_hook_expr("(SELECT MAX(id) FROM t)")) == 1

# Warning: non-deterministic
diagnostics = validate_hook_expr("GETDATE()")
assert len(diagnostics) == 1
assert diagnostics[0].severity == Severity.WARN
```

---

## 10. Integration with HOOK-006

### Current Spec (data-model.md)

Current HOOK-006 uses regex-based forbidden pattern detection:

```python
# Current approach (regex)
FORBIDDEN_PATTERNS = [
    (r"\bSELECT\b", "SELECT keyword"),
    (r"\bFROM\b", "FROM clause"),
    # ... more patterns
]
```

### Recommended Enhancement

Replace regex validation with sqlglot parsing:

```python
# Enhanced approach (sqlglot)
def validate_hook_expr(expr: str) -> list[Diagnostic]:
    try:
        parsed = sqlglot.parse_one(expr)
    except Exception as e:
        return [error(f"Invalid syntax: {e}")]
    
    if isinstance(parsed, (exp.Select, exp.Insert, ...)):
        return [error("Expression must not be a SQL statement")]
    
    if parsed.find(exp.Select):
        return [error("Expression must not contain subqueries")]
    
    return []
```

### Benefits

| Aspect | Regex Approach | sqlglot Approach |
|--------|----------------|------------------|
| Syntax validation | ❌ Can't detect | ✅ Full parsing |
| Balanced parens | ❌ Hard | ✅ Automatic |
| False positives | ⚠️ "SELECT" in column name | ✅ AST-aware |
| Statement detection | ⚠️ Pattern matching | ✅ Type checking |
| Subquery detection | ⚠️ Fragile regex | ✅ AST traversal |
| Maintainability | ❌ Growing regex list | ✅ Clean AST logic |

---

## Appendix: Available Dialects

sqlglot supports 20+ SQL dialects:

```
bigquery, clickhouse, databricks, doris, drill, duckdb, 
hive, materialize, mysql, oracle, postgres, presto, 
prql, redshift, snowflake, spark, spark2, sqlite, 
starrocks, tableau, teradata, trino, tsql
```

For manifest validation, use **no dialect** (generic SQL).
For future generators, use the appropriate target dialect.

---

## Appendix: Dependencies

```toml
[project.dependencies]
sqlglot = ">=28.0.0"
```

sqlglot has **no external dependencies** (pure Python), making it lightweight.

---

## Conclusion

**Recommendation**: Add sqlglot to dependencies and enhance HOOK-006 validation to use `sqlglot.parse_one()` for expression validation. This provides:

1. ✅ Syntax validation (catches typos, unbalanced parens)
2. ✅ Statement rejection (no SELECT, INSERT, etc.)  
3. ✅ Subquery detection
4. ✅ Future-proof for dialect transpilation in generators
5. ✅ Better error messages than regex

**Dialect choice**: Use **no dialect** for manifest validation. Generic SQL parsing handles common expression syntax without assuming a target platform.
