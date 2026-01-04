<!--
  SYNC IMPACT REPORT
  Version change: N/A → 1.0.0 (initial ratification)
  
  Added Sections:
  - Core Principles (10 principles)
  - HOOK Semantic Definitions
  - Prohibited Patterns
  - Relationship and Traversal Rules
  - Manifest and Governance Rules
  - Generator Constraints
  - Project-Level Constraints
  - Governance
  
  Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (no HOOK-specific updates required)
  - .specify/templates/spec-template.md ✅ (no HOOK-specific updates required)
  - .specify/templates/tasks-template.md ✅ (no HOOK-specific updates required)
  
  Follow-up TODOs: None
-->

# HOOK Python Library Constitution

This constitution governs the development of an open-source Python CLI and library that implements the HOOK methodology for data warehouse organisation. HOOK is an **organising discipline**, not a data modelling technique.

---

## Core Principles

### I. Organising Discipline, Not Modelling

HOOK is an **Extract–Load–Organise (ELO)** pattern. It MUST NOT be treated as ETL, ELT, or a data modelling methodology.

- The tool MUST organise data around business concepts without reshaping, transforming, or modelling the underlying data structures.
- Frames MUST wrap existing data warehouse tables; they MUST NOT restructure or denormalise them.
- HOOK concerns itself solely with organisation and integration via hooks, key sets, and frames—not with data acquisition, transformation, or analytics.

**Rationale**: Simplicity is the foundation of maintainability. The Second Law of Thermodynamics ensures that complexity leads to disorder; HOOK delays entropy by minimising moving parts.

### II. Hooks Represent Identity and Availability Only

A **hook** is a formalised business key that aligns a data warehouse asset (frame) with a business concept.

- Hooks MUST represent **identity** (what something is) and **availability** (whether it exists in a frame).
- Hooks MUST NOT encode business logic, process flow, temporal behaviour, calculations, measures, or analytics.
- Hooks MUST NOT represent derived or calculated values.
- A hook's value is the concatenation of a **key set** qualifier and a **business key**, separated by a delimiter (e.g., `CHNK.ALB|1234`).
- Null business key values MUST result in null hook values. Sentinel or default value substitution is FORBIDDEN.

**Rationale**: Hooks exist to integrate data across source system silos without imposing semantic interpretation. Identity is immutable context; behaviour is mutable logic.

### III. Business Concepts as the Organising Scheme

A **business concept** represents something an organisation interacts with during its operations (e.g., Customer, Employee, Order, Product).

- Business concepts MUST be documented with clear, concise, correct definitions and real-world examples.
- The number of business concepts SHOULD remain manageable (target ≤100–150 per organisation, per Dunbar's Number guidance).
- Business concepts MUST NOT be abstract IT constructs (e.g., "Party"); they MUST reflect language used in daily business operations.
- A single frame MAY align with multiple business concepts simultaneously (via multiple hooks).

**Rationale**: A shared conceptual vocabulary enables a common understanding of the data warehouse without requiring exhaustive data models.

### IV. Key Sets as Mandatory Qualifiers

A **key set** provides context for business keys and ensures global uniqueness of hook values.

- Every hook MUST be qualified with a key set; unqualified business keys MUST NOT be used for integration.
- Each key set MUST belong to exactly one business concept (though a business concept may have multiple key sets).
- Key set values MUST be globally unique across the entire data warehouse.
- Key set values SHOULD be human-readable (e.g., `SAP.FIN.ACC.NO` or `CHNK.ALB`).
- Key sets MAY be moved between business concepts during model refactoring, but their values MUST remain unchanged.

**Rationale**: Key sets prevent join collisions between unrelated business keys that happen to share the same raw values. They are the disambiguation layer that makes integration safe.

### V. Frames as Organisational Wrappers

A **frame** is a wrapper that combines a data warehouse table with one or more hooks, aligning the table with business concepts.

- Frames MUST NOT model, reshape, or transform the underlying data.
- Frames MAY be implemented as views (for agility) or physical tables (for performance).
- Frames MUST expose all original columns from the source table alongside calculated hooks.
- Frame naming MUST allow disambiguation of assets from multiple sources (e.g., `frame.Track__SystemA`).

**Rationale**: Frames provide the "warts and all" record of source data, organised by business concepts rather than source system silos.

### VI. Join Safety and Grain Preservation

**Join safety** is the guarantee that joining frames on hooks produces semantically correct results.

- Key set qualification MUST prevent false matches between hooks referencing different business concepts.
- Hook uniqueness within a frame determines cardinality:
  - Both hooks unique → 1:1
  - One hook unique, one non-unique → 1:M
  - Both hooks non-unique → M:M (exceptional; see below)
- Many-to-many joins MUST NOT be permitted except where explicitly acknowledged as exceptional and documented.
- Join paths MUST preserve grain unless explicitly and intentionally altered.
- Traversals across one-to-many paths MUST require explicit aggregation intent.
- Unsafe traversal paths MUST be detectable and rejectable by the tool.

**Rationale**: Grain amplification and fan traps produce incorrect analytical results. The tool must enforce safe defaults and surface unsafe paths.

### VII. Relationships Implied, Not Modelled

HOOK does not require explicit relationship definitions between frames.

- Relationships MUST be implied solely via shared hook names.
- If two frames contain hooks with the same business concept prefix (e.g., `HK_CUSTOMER`), they can be joined.
- Cardinality MUST be determined by hook uniqueness within each frame, not by predefined relationship metadata.

**Rationale**: Implied relationships eliminate redundant modelling while preserving navigability via the HOOK Matrix (a map of business concepts to frames).

### VIII. Manifest as Single Source of Truth

The **manifest** is the authoritative declaration of all HOOK semantic elements.

- The manifest MUST declare all business concepts, hooks, key sets, frames, and their relationships.
- The manifest MUST encode semantic truth, not physical implementation details.
- Manifest structure MUST evolve only via explicit versioning and migrations.
- Later features (HOOK SQL, USS SQL, Qlik generators) MAY extend the manifest only via versioned overlays.
- No extension MUST violate or reinterpret core HOOK semantics as defined in this constitution.

**Rationale**: A single source of truth prevents drift between documentation, code, and runtime behaviour.

### IX. Generators as Semantic Projections

SQL, USS SQL, Qlik, and other output generators are **projections** of the same HOOK semantic model.

- Generators MUST preserve availability, grain, and join safety as defined in the manifest.
- Generators MUST NOT redefine HOOK concepts (hooks, key sets, frames, business concepts).
- Generators MUST NOT introduce modelling semantics (dimensional models, star schemas, etc.) unless explicitly layered as consumption-layer extensions.
- Generated outputs MUST be traceable back to manifest declarations.

**Rationale**: Consistency across targets requires a single semantic model with faithful projections, not independent interpretations.

### X. Simplicity and Entropy Resistance

HOOK's design principle is to minimise complexity and delay entropy.

- Features MUST start simple; complexity MUST be justified and documented.
- YAGNI (You Aren't Gonna Need It) applies: do not build speculative features.
- Every addition to the manifest schema, CLI interface, or generator behaviour MUST be weighed against long-term maintenance cost.
- Code MUST be independently testable, well-documented, and replaceable.

**Rationale**: The Second Law of Thermodynamics guarantees that complexity degrades systems. Simplicity is the only defence.

---

## HOOK Semantic Definitions

### Business Concept

A **business concept** is something an organisation interacts with during its operations. It is identified by nouns used in daily business language (e.g., Customer, Order, Product, Employee).

- Business concepts MUST have definitions that are **clear** (plain language), **concise** (1–2 sentences), and **correct** (validated by examples).
- Business concepts MUST NOT be IT abstractions unless universally understood by the business.

### Hook

A **hook** is a calculated column that aligns a frame with one or more business concepts.

- Hook naming convention: `HK_<CONCEPT_NAME>[__<Qualifier>]` (e.g., `HK_CUSTOMER`, `HK_EMPLOYEE__Manager`).
- Weak hooks use: `WK_<CONCEPT_NAME>__<Qualifier>` (e.g., `WK_REF__Genre`, `WK_EPOCH__DoB`).
- Hook value format: `<KeySet>|<BusinessKey>` (e.g., `CHNK.ALB|1234`).
- Composite hooks concatenate multiple business key parts: `<KeySet>|<Part1>|<Part2>` (e.g., `INV.ITM|I8529|3`).
- Null business keys MUST produce null hooks.

### Availability

**Availability** indicates whether a hook value exists (is non-null) within a frame. If a frame contains `HK_CUSTOMER`, the Customer business concept is "available" in that frame.

### Grain

**Grain** is the level of detail represented by each row in a frame. It is determined by the combination of unique hooks within that frame.

- Grain MUST be preserved during joins unless explicitly altered with aggregation.
- Grain amplification (unintended row multiplication) MUST be detected as unsafe.

### Derivability

A value is **derivable** if it can be calculated from existing data without external input. Hooks MUST NOT represent derived or calculated values—they represent identity only.

### Join Safety

A join is **safe** if it:
1. Uses hooks qualified by key sets (preventing cross-concept collisions).
2. Preserves the intended grain of the result set.
3. Does not produce fan traps or grain amplification.

---

## Prohibited Patterns

The following patterns are FORBIDDEN and MUST be rejected by the tool:

1. **Treating HOOK as a data modelling methodology**: HOOK organises; it does not model.
2. **Encoding business logic into hooks**: Hooks represent identity, not rules or calculations.
3. **Encoding process flow into hooks**: Temporal sequences are not hook concerns.
4. **Encoding analytics or measures into hooks**: Aggregations belong in consumption layers.
5. **Representing derived or calculated values as hooks**: Hooks are identity anchors only.
6. **Implicit joins that amplify grain without explicit intent**: All M:M or 1:M traversals MUST require explicit acknowledgement.
7. **Substituting null business keys with sentinels or defaults**: Null MUST propagate as null. `-1`, `UNKNOWN`, or similar replacements are FORBIDDEN.
8. **Many-to-many joins without explicit acknowledgement**: M:M joins MUST be flagged and require documented justification.
9. **Hooks without key set qualification**: Every hook MUST include its key set prefix.
10. **Redefining HOOK concepts in generators**: Generators project; they do not reinterpret.

---

## Relationship and Traversal Rules

### Implied Relationships

- Two frames are related if they share a hook with the same business concept name.
- No explicit foreign key or relationship declaration is required or supported.
- The HOOK Matrix (business concepts × frames) serves as the navigational map.

### Cardinality Determination

| Hook A Uniqueness | Hook B Uniqueness | Cardinality |
|-------------------|-------------------|-------------|
| Unique            | Unique            | 1:1         |
| Unique            | Non-unique        | 1:M         |
| Non-unique        | Non-unique        | M:M (exceptional) |

### Traversal Requirements

- Traversals across 1:M boundaries MUST require explicit aggregation intent.
- Traversals that would amplify grain MUST be flagged as unsafe.
- The tool MUST detect and surface unsafe traversal paths before execution.
- Join paths MUST be traceable through the HOOK Matrix.

---

## Manifest and Governance Rules

### Manifest Structure

The manifest is a declarative file (YAML, JSON, or equivalent) that defines:

- **Business concepts**: name, definition, examples.
- **Key sets**: value, owning business concept.
- **Hooks**: name, business concept, key set, source column(s), treatment rules.
- **Frames**: name, source table, hooks, grain indicators.

### Manifest Evolution

- Manifest schema MUST be versioned using semantic versioning.
- Breaking changes (removing concepts, renaming hooks, changing key sets) require a MAJOR version bump.
- Additions (new concepts, hooks, frames) require a MINOR version bump.
- Clarifications and metadata-only changes require a PATCH version bump.
- Migrations MUST be explicit and auditable.

### Extension Rules

- Extensions (HOOK SQL, USS SQL, Qlik) MUST declare compatibility with specific manifest versions.
- Extensions MUST NOT override or reinterpret core HOOK semantics.
- Extensions MAY add consumption-layer constructs (e.g., star schemas, cubes) as overlays.
- Overlay declarations MUST be versioned independently.

---

## Generator Constraints

Generators produce output (SQL, USS SQL, Qlik scripts, etc.) from the manifest.

### Invariants

1. Generators MUST preserve **availability**: if a hook is declared, it MUST appear in output.
2. Generators MUST preserve **grain**: output row counts MUST match expected grain unless aggregation is explicit.
3. Generators MUST preserve **join safety**: only safe joins MUST be generated by default; unsafe joins MUST require explicit opt-in.
4. Generators MUST NOT introduce modelling constructs unless explicitly configured as consumption-layer extensions.

### Traceability

- Every generated artefact MUST reference its source manifest element(s).
- Generated SQL MUST include comments or metadata linking to hook/frame definitions.

---

## Project-Level Constraints

### Python CLI and Library

- The library MUST be usable as a Python import and as a standalone CLI.
- CLI MUST accept manifest files as input and produce validated outputs or generated artefacts.
- CLI MUST provide clear error messages for constitution violations.
- All public APIs MUST be typed and documented.

### Testing

- Every principle in this constitution MUST have corresponding tests.
- Prohibited patterns MUST have negative tests (tests that verify rejection).
- Integration tests MUST validate end-to-end flows: manifest → validation → generation.

### Versioning

- Project versioning MUST follow semantic versioning (MAJOR.MINOR.PATCH).
- MAJOR: breaking API or manifest schema changes.
- MINOR: new features, backward-compatible.
- PATCH: bug fixes, documentation, refactoring.

### Open Source

- All code MUST be licensed under an OSI-approved license.
- Contributions MUST comply with this constitution.
- Pull requests MUST pass constitution compliance checks.

---

## Governance

### Supremacy

This constitution supersedes all other practices, conventions, and informal agreements.

### Compliance

- All pull requests MUST verify compliance with this constitution.
- CI pipelines MUST include constitution validation checks.
- Complexity additions MUST be justified in PR descriptions.

### Amendment Process

1. Propose amendment via GitHub issue with rationale.
2. Draft amendment text with version bump justification.
3. Review period: minimum 7 days for community feedback.
4. Approval: maintainer consensus required.
5. Update constitution with new version, ratification date, and sync impact report.

### Version Scheme

- **MAJOR**: Backward-incompatible governance/principle removals or redefinitions.
- **MINOR**: New principle/section added or materially expanded guidance.
- **PATCH**: Clarifications, wording, typo fixes, non-semantic refinements.

---

**Version**: 1.0.0 | **Ratified**: 2026-01-04 | **Last Amended**: 2026-01-04
