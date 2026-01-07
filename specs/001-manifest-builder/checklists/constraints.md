# Constraints Checklist: Manifest Builder

**Purpose**: Validate that all constraints in the 001-manifest-builder feature are completely specified, clearly defined, measurable, and consistent across spec, plan, and data-model documents.
**Created**: 2026-01-07
**Feature**: [spec.md](../spec.md), [plan.md](../plan.md), [data-model.md](../data-model.md)

**Note**: This checklist is a "unit test for requirements" - it validates the quality of constraint specifications, not implementation correctness.

---

## Structural Constraints (Schema Requirements)

- [x] CHK001 - Are manifest root structure requirements complete with all required fields documented? [Completeness, Spec §Manifest Schema v1]
- [x] CHK002 - Is the `manifest_version` field format precisely specified (semver without pre-release)? [Clarity, Spec §FR-030, MANIFEST-001]
- [x] CHK003 - Is the `schema_version` field format precisely specified (semver without pre-release)? [Clarity, Spec §FR-031, MANIFEST-002]
- [x] CHK004 - Are `metadata` object required fields explicitly listed (name, created_at, updated_at)? [Completeness, Data-Model §Metadata]
- [x] CHK005 - Are `settings` object default values documented for hook_prefix, weak_hook_prefix, delimiter? [Completeness, Spec §FR-038]
- [x] CHK006 - Is the requirement for at least one frame explicitly stated? [Completeness, Spec §FR-032]
- [x] CHK007 - Is the `concepts` array optionality clearly documented? [Clarity, Spec §FR-037]

## Frame Constraints

- [x] CHK008 - Is FRAME-001 (frame must have at least one hook) clearly specified with rule ID? [Completeness, Spec §Validation Rules]
- [x] CHK009 - Is FRAME-002 (frame name must match `<schema>.<table>` lower_snake_case) quantified with regex pattern? [Clarity, Data-Model §Naming Conventions]
- [x] CHK010 - Is FRAME-003 (at least one primary hook per frame) explicitly documented? [Completeness, Spec §FR-035]
- [x] CHK011 - Is FRAME-004 (frame source object required) explicitly stated? [Completeness, Spec §Validation Rules]
- [x] CHK012 - Is FRAME-005 (source exclusivity: exactly one of relation/path) clearly specified? [Clarity, Spec §FR-033a, FR-033b]
- [x] CHK013 - Is FRAME-006 (source.relation/path must be non-empty string) explicitly documented? [Completeness, Spec §FR-033c]
- [x] CHK014 - Is the composite grain pattern (multiple primary hooks) documented with ordering semantics? [Completeness, Spec §Clarifications 2026-01-06]
- [x] CHK015 - Are frame naming convention examples provided to clarify the pattern? [Clarity, Data-Model §Frame]

## Hook Constraints

- [x] CHK016 - Is HOOK-001 (hook required fields: name, role, concept, source, expr) explicitly listed? [Completeness, Spec §FR-034]
- [x] CHK017 - Is HOOK-002 (hook name pattern `<prefix><concept>[__<qualifier>]`) quantified with regex? [Clarity, Data-Model §Naming Conventions]
- [x] CHK018 - Is HOOK-003 (role must be "primary" or "foreign") specified as enum constraint? [Clarity, Spec §FR-035]
- [x] CHK019 - Is HOOK-004 (concept must be lower_snake_case) quantified with regex pattern? [Clarity, Data-Model §Naming Conventions]
- [x] CHK020 - Is HOOK-005 (source must be UPPER_SNAKE_CASE) quantified with regex pattern? [Clarity, Data-Model §Naming Conventions]
- [x] CHK021 - Is HOOK-006 (expr must be non-empty valid SQL expression) specified with allowed/forbidden patterns? [Completeness, Data-Model §Expression Validation]
- [x] CHK022 - Is the `qualifier` field optionality and format (lower_snake_case) documented? [Completeness, Data-Model §Hook]
- [x] CHK023 - Is the `tenant` field optionality and format (UPPER_SNAKE_CASE) documented? [Completeness, Data-Model §Hook]
- [x] CHK024 - Are hook prefix defaults (_hk__ for strong, _wk__ for weak) clearly specified? [Clarity, Spec §FR-051]

## Key Set Constraints

- [x] CHK025 - Is HOOK-007 (hook names must be unique within the same frame) explicitly stated? [Completeness, Spec §Validation Rules]
- [x] CHK026 - Is the key set derivation recipe `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]` precisely documented? [Clarity, Spec §FR-054, FR-055]
- [x] CHK027 - Are key set parsing rules (split on @ then ~) explicitly documented? [Clarity, Spec §FR-055]
- [x] CHK028 - Are key set allowed characters (a-z, 0-9, _, A-Z, @, ~) enumerated? [Completeness, Spec §FR-056]
- [x] CHK029 - Are key set derivation examples provided for all variants (with/without qualifier, with/without tenant)? [Clarity, Data-Model §Auto-Derived Registries]

## Concept Constraints

- [x] CHK030 - Is CONCEPT-001 (concept in concepts section must be used in at least one hook) explicitly stated? [Completeness, Spec §Validation Rules]
- [x] CHK031 - Is CONCEPT-002 (description must be 10-200 characters) quantified with bounds? [Clarity, Spec §Validation Rules]
- [x] CHK032 - Is CONCEPT-003 (no duplicate concept names in concepts section) explicitly stated? [Completeness, Spec §Edge Cases]
- [x] CHK033 - Is concept name format (lower_snake_case) documented with regex pattern? [Clarity, Spec §FR-050]

## Expression (Manifest SQL Subset) Constraints

- [x] CHK034 - Are allowed SQL tokens explicitly enumerated (column refs, literals, operators, functions)? [Completeness, Data-Model §Expression Validation]
- [x] CHK035 - Are forbidden SQL patterns explicitly enumerated with regex patterns (SELECT, FROM, JOIN, etc.)? [Completeness, Data-Model §Expression Validation]
- [x] CHK036 - Is the restriction to SQL-only expressions for Feature 001 documented? [Clarity, Spec §FR-034a]
- [x] CHK037 - Are non-deterministic function restrictions (RANDOM, GETDATE, NOW, etc.) documented? [Completeness, Data-Model §Forbidden Patterns]
- [x] CHK038 - Are DDL/DML restrictions (INSERT, UPDATE, DELETE, etc.) documented? [Completeness, Data-Model §Forbidden Patterns]

## Naming Convention Constraints

- [x] CHK039 - Is lower_snake_case regex pattern `^[a-z][a-z0-9_]*$` documented? [Clarity, Data-Model §Naming Conventions]
- [x] CHK040 - Is UPPER_SNAKE_CASE regex pattern `^[A-Z][A-Z0-9_]*$` documented? [Clarity, Data-Model §Naming Conventions]
- [x] CHK041 - Is hook_name regex pattern documented with prefix variants? [Clarity, Data-Model §Naming Conventions]
- [x] CHK042 - Is frame_name regex pattern `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$` documented? [Clarity, Data-Model §Naming Conventions]
- [x] CHK043 - Is semver regex pattern `^\d+\.\d+\.\d+$` documented? [Clarity, Data-Model §Naming Conventions]
- [x] CHK044 - Is the ASCII-only constraint for identifiers (no Unicode in names) documented? [Completeness, Spec §NFR-023]

## Warning Threshold Constraints

- [x] CHK045 - Is CONCEPT-W01 (>100 concepts) threshold documented with rationale (Dunbar guidance)? [Clarity, Spec §Advisory Rules, Limits and Constraints]
- [x] CHK046 - Is HOOK-W01 (weak hook prefix vs is_weak mismatch) clearly specified? [Completeness, Spec §Advisory Rules]
- [x] CHK047 - Is FRAME-W01 (frame with only foreign hooks, no primary) documented? [Completeness, Spec §Advisory Rules]
- [x] CHK048 - Is FRAME-W02 (multiple frames with same source) documented? [Completeness, Spec §Advisory Rules]
- [x] CHK049 - Is FRAME-W03 (>20 hooks per frame) threshold documented? [Clarity, Spec §Advisory Rules, Limits and Constraints]
- [x] CHK050 - Is MANIFEST-W01 (>50 frames) threshold documented? [Clarity, Spec §Advisory Rules, Limits and Constraints]
- [x] CHK051 - Is MANIFEST-W02 (unknown fields in manifest) forward compatibility warning documented? [Completeness, Spec §Advisory Rules, NFR-032]

## Performance Constraints

- [x] CHK052 - Is NFR-001 (<1 second for 1000-line manifest) quantified with hardware baseline? [Clarity, Spec §NFR-001]
- [x] CHK053 - Is NFR-002 (<5 seconds for 10,000-line manifest) quantified? [Clarity, Spec §NFR-002]
- [x] CHK054 - Is NFR-003 (<100MB memory for 1MB file) quantified? [Clarity, Spec §NFR-003]
- [x] CHK055 - Is the maximum manifest file size (1MB) documented? [Completeness, Spec §Limits and Constraints]

## CLI Behavior Constraints

- [x] CHK056 - Are exit codes precisely defined (0=success, 1=validation errors, 2=usage errors)? [Clarity, Spec §CLI Behavior Summary, SC-006]
- [x] CHK057 - Is FR-080 (collect all errors before reporting, no fail-fast) explicitly stated? [Completeness, Spec §FR-080]
- [x] CHK058 - Is FR-082 (exit 0 if valid with WARNs, exit 1 if ERRORs) explicitly stated? [Completeness, Spec §FR-082]
- [x] CHK059 - Is FR-085 (UTF-8 encoding for all CLI output) explicitly stated? [Completeness, Spec §FR-085]
- [x] CHK060 - Is NFR-010 (screen reader compatibility, no ANSI in errors) documented? [Completeness, Spec §NFR-010]
- [x] CHK061 - Is NFR-011 (--no-color flag support) documented? [Completeness, Spec §NFR-011]

## Diagnostic Format Constraints

- [x] CHK062 - Is FR-016 (diagnostic must include: rule_id, severity, message, path, fix) completely specified? [Completeness, Spec §FR-016]
- [x] CHK063 - Is the rule_id pattern `<ENTITY>-[W]<NNN>` documented? [Clarity, Data-Model §Diagnostic]
- [x] CHK064 - Are severity levels (ERROR, WARN) and their exit code mappings documented? [Clarity, Spec §Diagnostic Format]
- [x] CHK065 - Is human-readable diagnostic format example provided? [Clarity, Spec §Diagnostic Format]
- [x] CHK066 - Is JSON diagnostic format (`--json` flag) structure documented? [Clarity, Spec §Diagnostic Format]

## Schema Version Constraints

- [x] CHK067 - Is NFR-030 (semver semantics: patch, minor, major changes) documented? [Completeness, Spec §NFR-030]
- [x] CHK068 - Is NFR-031 (1.x.x backward compatibility) explicitly stated? [Completeness, Spec §NFR-031]
- [x] CHK069 - Is NFR-032 (unknown fields ignored with WARN) explicitly stated? [Completeness, Spec §NFR-032]

## I/O Constraints

- [x] CHK070 - Is deterministic YAML key ordering specified with full key sequence? [Completeness, Data-Model §I/O Contracts]
- [x] CHK071 - Is parse error format (line, column, message) documented? [Clarity, Data-Model §Parse Error Format]
- [x] CHK072 - Is FR-010 (support both YAML and JSON parsing) explicitly stated? [Completeness, Spec §FR-010]
- [x] CHK073 - Is FR-024 (wizard YAML default, JSON with --format json) documented? [Completeness, Spec §FR-024]

## Wizard Behavior Constraints

- [x] CHK074 - Is FR-020 (frame-first workflow order) documented with explicit step sequence? [Completeness, Spec §Clarifications]
- [x] CHK075 - Is FR-021 (validate each input before proceeding) explicitly stated? [Completeness, Spec §FR-021]
- [x] CHK076 - Is FR-022 (prevent prohibited patterns by construction) explicitly stated? [Completeness, Spec §FR-022]
- [x] CHK077 - Is FR-023 (display summary preview before writing) explicitly stated? [Completeness, Spec §FR-023]
- [x] CHK078 - Is FR-025 (prompt before overwriting existing files) explicitly stated? [Completeness, Spec §FR-025]
- [x] CHK079 - Is FR-084 (Ctrl+C saves .dot-draft.yaml if at least one frame completed) documented? [Completeness, Spec §FR-084]
- [x] CHK080 - Is the non-TTY error case (interactive mode requires terminal) documented? [Completeness, Spec §Edge Cases]

## Example Manifest Constraints

- [x] CHK081 - Is FR-060 (ship with at least 4 examples) quantified? [Completeness, Spec §FR-060]
- [x] CHK082 - Are the 4 example types explicitly listed (minimal/relation, file-based/path, typical, complex)? [Clarity, Spec §FR-060]
- [x] CHK083 - Is FR-061 (all examples must pass validation) explicitly stated? [Completeness, Spec §FR-061]
- [x] CHK084 - Is FR-062 (examples demonstrate different patterns) specified with pattern list? [Completeness, Spec §FR-062]

## Implementation Standard Constraints

- [x] CHK085 - Is NFR-040 (ruff check and ruff format) explicitly stated? [Completeness, Spec §NFR-040]
- [x] CHK086 - Is NFR-041 (mypy --strict) explicitly stated? [Completeness, Spec §NFR-041]
- [x] CHK087 - Is NFR-042 (pre-commit hooks for ruff and mypy) explicitly stated? [Completeness, Spec §NFR-042]
- [x] CHK088 - Is Python version constraint (3.10+) documented? [Completeness, Spec §Assumptions]

## Functional Programming Paradigm Constraints (Constitution §Project-Level)

- [x] CHK111 - Is the functional-first programming paradigm requirement documented? [Constitution, Spec §NFR-050]
- [x] CHK112 - Is immutable data structures requirement (frozen models) documented? [Constitution, Spec §NFR-051]
- [x] CHK113 - Is pure functions requirement documented? [Constitution, Spec §NFR-052]
- [x] CHK114 - Is state isolation at boundaries (io/, cli/) documented? [Constitution, Spec §NFR-053]
- [x] CHK115 - Are permitted class patterns explicitly listed (frozen data, Protocol/ABC, framework)? [Constitution, Spec §NFR-054]
- [x] CHK116 - Is inheritance prohibition for code reuse documented? [Constitution, Spec §NFR-055]
- [x] CHK117 - Are method restrictions on data classes documented? [Constitution, Spec §NFR-056]

## Consistency Across Documents

- [x] CHK089 - Are validation rule IDs consistent between spec.md and data-model.md? [Consistency]
- [x] CHK090 - Are regex patterns consistent between naming convention docs and validation rules? [Consistency]
- [x] CHK091 - Are field requirements (required vs optional) consistent between spec schema and data-model tables? [Consistency]
- [x] CHK092 - Are warning thresholds consistent between Limits and Constraints section and Advisory Rules table? [Consistency]
- [x] CHK093 - Is the frame source exclusivity constraint consistent across FR-033a/b/c and FRAME-005/006? [Consistency]
- [x] CHK094 - Is the composite grain clarification (2026-01-06) reflected in FRAME-003 rule update? [Consistency]

## Edge Case Coverage

- [x] CHK095 - Is file not found behavior documented with error message format? [Coverage, Spec §Edge Cases]
- [x] CHK096 - Is empty manifest behavior documented? [Coverage, Spec §Edge Cases]
- [x] CHK097 - Is malformed YAML/JSON error behavior documented with line/column? [Coverage, Spec §Edge Cases]
- [x] CHK098 - Is zero frames error case documented? [Coverage, Spec §Edge Cases, FRAME-001]
- [x] CHK099 - Is unused concept (defined but not in hooks) error case documented? [Coverage, Spec §Edge Cases, CONCEPT-001]
- [x] CHK100 - Is duplicate concept name error case documented? [Coverage, Spec §Edge Cases, CONCEPT-003]
- [x] CHK101 - Is file save permission denied error case documented? [Coverage, Spec §Edge Cases]
- [x] CHK102 - Is Unicode restriction in identifiers (ASCII only) documented? [Coverage, Spec §Edge Cases]
- [x] CHK103 - Is circular hook reference handling (deferred to v2) explicitly documented? [Coverage, Spec §Edge Cases]

## Ambiguities and Gaps

- [x] CHK104 - Is delimiter validation (single character) explicitly stated? [Gap, Data-Model §Settings]
- [x] CHK105 - Are hook_prefix and weak_hook_prefix non-empty constraints documented? [Gap, Data-Model §Settings]
- [x] CHK106 - Is metadata.name non-empty constraint documented? [Gap, Data-Model §Metadata]
- [x] CHK107 - Is the behavior when qualifier is provided without tenant explicitly documented? [Gap]
- [x] CHK108 - Is the behavior when tenant is provided without qualifier explicitly documented? [Gap]
- [x] CHK109 - Is maximum concept description length (200 chars) from CONCEPT-002 documented outside validation rules table? [Gap]
- [x] CHK110 - Is minimum concept description length (10 chars) from CONCEPT-002 documented? [Gap]

---

## Summary

| Category | Item Count |
|----------|------------|
| Structural Constraints | 7 |
| Frame Constraints | 8 |
| Hook Constraints | 9 |
| Key Set Constraints | 5 |
| Concept Constraints | 4 |
| Expression Constraints | 5 |
| Naming Convention Constraints | 6 |
| Warning Threshold Constraints | 7 |
| Performance Constraints | 4 |
| CLI Behavior Constraints | 6 |
| Diagnostic Format Constraints | 5 |
| Schema Version Constraints | 3 |
| I/O Constraints | 4 |
| Wizard Behavior Constraints | 7 |
| Example Manifest Constraints | 4 |
| Implementation Standard Constraints | 4 |
| Functional Programming Paradigm | 7 |
| Consistency Across Documents | 6 |
| Edge Case Coverage | 9 |
| Ambiguities and Gaps | 7 |
| **Total** | **117** |
