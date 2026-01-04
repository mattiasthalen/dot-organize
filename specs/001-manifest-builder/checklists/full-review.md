# Requirements Quality Checklist: Full Spec Review

**Feature**: 001-manifest-builder  
**Purpose**: Comprehensive requirements quality validation (unit tests for English)  
**Audience**: Author (self-review, pre-commit)  
**Created**: 2026-01-04

---

## Requirement Completeness

- [ ] CHK001 - Are all 8 Pydantic models fully specified with field types, defaults, and validation rules? [Completeness, Spec §5] [M1-02 to M1-07]
- [ ] CHK002 - Are all 16 ERROR validation rules documented with rule ID, description, and constitution reference? [Completeness, Spec §7.1] [M2-01 to M2-05]
- [ ] CHK003 - Are all 5 WARN validation rules documented with rule ID, description, and constitution reference? [Completeness, Spec §7.2] [M2-06]
- [ ] CHK004 - Are CLI exit codes defined for all commands (validate, init, examples)? [Completeness, Spec §6.4] [M4-02]
- [ ] CHK005 - Are all edge cases documented with expected behavior? [Completeness, Spec Edge Cases] [M4-12]
- [ ] CHK006 - Are treatment operations (LPAD, RPAD, UPPER, LOWER, TRIM) fully specified with syntax and examples? [Completeness, Spec FR-070 to FR-073] [M1-04]
- [ ] CHK007 - Is the expr_sql validation allowlist complete (all allowed tokens documented)? [Completeness, data-model.md §12] [M2-10]
- [ ] CHK008 - Is the expr_sql validation forbidden list complete (all rejected patterns documented)? [Completeness, data-model.md §12] [M2-10]
- [ ] CHK009 - Are auto-derived registries (key sets, concepts, hooks) fully specified? [Completeness, data-model.md §9] [M2-07 to M2-09]
- [ ] CHK010 - Are all functional requirements (FR-001 to FR-085) traceable to acceptance scenarios? [Completeness, Spec §Requirements] [M1-11, M2-12, M4-12]

---

## Requirement Clarity

- [ ] CHK011 - Is the key set recipe `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]` unambiguous with parsing rules? [Clarity, Spec FR-054, FR-055] [M2-07]
- [ ] CHK012 - Is the hook naming pattern `<prefix><concept>[__<qualifier>]` quantified with regex? [Clarity, data-model.md §10] [M1-08]
- [ ] CHK013 - Is "1-2 sentence description" for concepts measurable (word count? character limit?)? [Ambiguity, Spec CONCEPT-002] [M2-04]
- [ ] CHK014 - Is "under 1 second" validation performance quantified with test conditions (file size, hardware)? [Clarity, Spec SC-001] [M7-06]
- [ ] CHK015 - Is "under 5 minutes" wizard completion quantified with test conditions (concept count, user expertise)? [Clarity, Spec SC-002] [M4-05]
- [ ] CHK016 - Are all naming convention patterns defined with explicit regex? [Clarity, data-model.md §10] [M1-08]
- [ ] CHK017 - Is the wizard "frame-first workflow" defined with explicit step sequence? [Clarity, Spec FR-020] [M4-05]
- [ ] CHK018 - Is "valid semver" defined with specific pattern (major.minor.patch only, or pre-release allowed)? [Clarity, Spec MANIFEST-001, MANIFEST-002] [M2-05]
- [ ] CHK019 - Is the delimiter field constraint ("single character") unambiguous (1 byte? 1 Unicode codepoint?)? [Clarity, data-model.md §3] [M1-06]
- [ ] CHK020 - Are JSONPath expressions in diagnostics defined with specific syntax rules? [Clarity, data-model.md §8] [M1-07]

---

## Requirement Consistency

- [ ] CHK021 - Do hook field names match between spec.md and data-model.md? [Consistency] [M1-04]
- [ ] CHK022 - Does the key set recipe in spec.md match the derivation logic in data-model.md? [Consistency] [M2-07]
- [ ] CHK023 - Are default values for Settings consistent between spec.md, data-model.md, and JSON Schema? [Consistency] [M1-06]
- [ ] CHK024 - Do validation rule IDs match between spec.md §7 and data-model.md §13? [Consistency] [M2-01 to M2-06]
- [ ] CHK025 - Are exit codes consistent between spec.md CLI Behavior table and implementation plan? [Consistency] [M4-02]
- [ ] CHK026 - Do example manifests in spec.md use the same field names as schema definitions? [Consistency] [M5-01 to M5-03]
- [ ] CHK027 - Is the treatment syntax (pipe separator) consistent with delimiter field (also pipe default)? [Potential Conflict] [M1-04]

---

## Acceptance Criteria Quality

- [ ] CHK028 - Can each acceptance scenario be independently tested without implementation? [Measurability, Spec User Stories] [M4-12]
- [ ] CHK029 - Does each user story have at least one negative test scenario? [Coverage, Spec User Stories] [M2-11]
- [ ] CHK030 - Are all success criteria (SC-001 to SC-007) objectively measurable? [Measurability, Spec Success Criteria] [M7-06]
- [ ] CHK031 - Is the "100% prohibited patterns detected" criteria (SC-003) defined with pattern list? [Clarity, Spec SC-003] [M2-12]
- [ ] CHK032 - Are golden test expectations defined (what "pass validation" means)? [Measurability, Spec SC-004] [M5-04]

---

## Scenario Coverage

- [ ] CHK033 - Are requirements defined for empty manifest (zero frames)? [Edge Case, Gap] [M2-01]
- [ ] CHK034 - Are requirements defined for frame with zero hooks? [Edge Case, FRAME-001] [M2-01]
- [ ] CHK035 - Are requirements defined for frame with multiple primary hooks? [Edge Case, FRAME-003] [M2-01]
- [ ] CHK036 - Are requirements defined for circular hook references (concept A references concept B references A)? [Edge Case, Gap] [M2-02]
- [ ] CHK037 - Are requirements defined for maximum manifest size (number of frames, hooks, concepts)? [Non-Functional, Gap] [M7-06]
- [ ] CHK038 - Are requirements defined for Unicode in concept names, descriptions, examples? [Edge Case, Gap] [M1-08]
- [ ] CHK039 - Are requirements defined for duplicate concept names in concepts section? [Edge Case, CONCEPT-001] [M2-04]
- [ ] CHK040 - Are requirements defined for concept defined but never used in hooks? [Edge Case, CONCEPT-001] [M2-04]
- [ ] CHK041 - Are requirements defined for wizard cancellation mid-flow (Ctrl+C handling)? [Exception Flow, Spec Edge Cases] [M4-05]
- [ ] CHK042 - Are requirements defined for file permission errors during save? [Exception Flow, Gap] [M4-08]

---

## Non-Functional Requirements

- [ ] CHK043 - Are performance requirements specified for validation (SC-001)? [NFR, Spec SC-001] [M7-06]
- [ ] CHK044 - Are memory requirements specified for large manifests? [NFR, Gap] [M7-06]
- [ ] CHK045 - Are accessibility requirements defined for CLI output (screen reader compatibility)? [NFR, Gap] [M4-03]
- [ ] CHK046 - Are internationalization requirements defined (UTF-8 only, or multi-locale)? [NFR, Spec FR-085] [M4-03]
- [ ] CHK047 - Are error message localization requirements defined? [NFR, Gap] [M4-03]
- [ ] CHK048 - Are backwards compatibility requirements defined for schema_version changes? [NFR, Gap] [M2-05]

---

## Dependencies & Assumptions

- [ ] CHK049 - Is Python 3.10+ requirement documented in spec and pyproject.toml template? [Dependency, Spec Assumptions] [M1-01]
- [ ] CHK050 - Are Pydantic v2 frozen model requirements documented? [Dependency, data-model.md] [M1-02]
- [ ] CHK051 - Is the assumption "no database connectivity" validated against all features? [Assumption, Spec Assumptions] [M3-01]
- [ ] CHK052 - Is the assumption "YAML preferred over JSON" validated with user research? [Assumption, Spec Assumptions] [M3-01]
- [ ] CHK053 - Are ruamel.yaml version requirements specified for ordered key output? [Dependency, quickstart.md] [M3-02]

---

## Ambiguities & Gaps Identified

- [ ] CHK054 - Is the relationship between strong/weak hooks and key sets fully specified? [Ambiguity] [M2-02]
- [ ] CHK055 - Are requirements for hook name prefix validation (must match is_weak flag) specified? [Gap, HOOK-W01] [M2-06]
- [ ] CHK056 - Is fallback behavior specified when treatment parsing fails? [Gap] [M2-02]
- [ ] CHK057 - Are requirements for partial manifest recovery after parse error specified? [Gap] [M3-05]
- [ ] CHK058 - Is the "grain_hooks" field mentioned in spec Constitution Compliance Matrix but not in schema? [Conflict, Spec Appendix] [M1-03]
- [ ] CHK059 - Is "is_unique" mentioned in spec Constitution Compliance Matrix but not defined in models? [Conflict, Spec Appendix] [M1-03]
- [ ] CHK060 - Are requirements for concurrent wizard sessions (multiple terminals) specified? [Gap] [M4-05]

---

## Cross-Reference Traceability

- [ ] CHK061 - Does every plan task (M1-01 to M7-08) have a reference to spec or data-model section? [Traceability] [plan.md]
- [ ] CHK062 - Does every validation rule have a function name mapping in data-model.md §13? [Traceability] [M2-01 to M2-06]
- [ ] CHK063 - Does every model field have a corresponding JSON Schema definition? [Traceability] [contracts/manifest-schema.json]
- [ ] CHK064 - Are all FR-xxx requirements traceable to plan tasks? [Traceability] [plan.md]

---

## Summary

| Category | Items | Purpose |
|----------|-------|---------|
| Completeness | CHK001-CHK010 | Are all necessary requirements documented? |
| Clarity | CHK011-CHK020 | Are requirements unambiguous and specific? |
| Consistency | CHK021-CHK027 | Do requirements align without conflicts? |
| Acceptance Criteria | CHK028-CHK032 | Are success criteria measurable? |
| Scenario Coverage | CHK033-CHK042 | Are all flows and edge cases addressed? |
| Non-Functional | CHK043-CHK048 | Are performance, accessibility, i18n specified? |
| Dependencies | CHK049-CHK053 | Are assumptions and dependencies validated? |
| Ambiguities | CHK054-CHK060 | What needs clarification or resolution? |
| Traceability | CHK061-CHK064 | Can requirements be traced to implementation? |

**Total Items**: 64
