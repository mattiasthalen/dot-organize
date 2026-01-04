# Feature Specification: HOOK Manifest Builder

**Feature Branch**: `001-manifest-builder`  
**Created**: 2026-01-04  
**Status**: Draft  
**Input**: Build HOOK Manifest Builder Python package and CLI for guided manifest creation, validation, and output

---

## Problem Statement

Data warehouse practitioners adopting the HOOK methodology need a reliable way to declare and validate their semantic model—business concepts, hooks, key sets, and frames—before generating any SQL, USS, or Qlik outputs. Currently, there is no tooling to:

1. Guide users through creating a constitution-compliant HOOK manifest
2. Validate manifests against HOOK semantic rules and prohibited patterns
3. Produce stable, versioned manifest files that can later be extended with generator overlays

Without such tooling, users risk creating invalid manifests that violate HOOK principles, leading to unsafe joins, grain amplification, and integration failures.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Existing Manifest (Priority: P1)

As a data engineer, I want to validate an existing HOOK manifest file so that I can ensure it complies with all constitutional constraints before using it for downstream generation.

**Why this priority**: Validation is the foundation—users need confidence their manifest is correct before any other operation. This also enables CI integration from day one.

**Independent Test**: Can be fully tested by running `hook validate path/to/manifest.yaml` against valid and invalid manifests and verifying correct exit codes and error messages.

**Acceptance Scenarios**:

1. **Given** a valid manifest file, **When** I run `hook validate manifest.yaml`, **Then** the tool exits with code 0 and prints "Manifest is valid."
2. **Given** a manifest with a hook missing its key set, **When** I run `hook validate manifest.yaml`, **Then** the tool exits with code 1 and prints an ERROR referencing rule ID `HOOK-001` with the path to the invalid hook.
3. **Given** a manifest with duplicate key set values, **When** I run `hook validate manifest.yaml`, **Then** the tool exits with code 1 and prints an ERROR referencing rule ID `KEYSET-002`.
4. **Given** a manifest with a warning-level issue (e.g., >100 business concepts), **When** I run `hook validate manifest.yaml`, **Then** the tool exits with code 0 but prints a WARN message.
5. **Given** any manifest, **When** I run `hook validate manifest.yaml --json`, **Then** the tool outputs machine-readable JSON diagnostics.

---

### User Story 2 - Create Manifest via Interactive Wizard (Priority: P2)

As a new HOOK user, I want an interactive wizard that guides me through creating a valid manifest so that I don't have to memorize the schema or constitution rules.

**Why this priority**: After validation, guided creation is the primary user journey for new adopters. It lowers the barrier to entry significantly.

**Independent Test**: Can be fully tested by running `hook init` in interactive mode, providing inputs, and verifying the output file passes validation.

**Acceptance Scenarios**:

1. **Given** I run `hook init`, **When** the wizard prompts for business concepts, **Then** I can enter concept names, definitions, and examples with validation feedback.
2. **Given** I enter an invalid business concept name (e.g., containing spaces), **When** I submit, **Then** the wizard rejects it with an actionable error and re-prompts.
3. **Given** I complete the wizard, **When** I confirm the summary preview, **Then** the wizard writes a valid YAML manifest to the specified location.
4. **Given** the output file already exists, **When** the wizard attempts to write, **Then** it prompts for confirmation before overwriting (or offers a new filename).
5. **Given** I run `hook init --output manifest.json`, **When** I complete the wizard, **Then** the output is valid JSON instead of YAML.

---

### User Story 3 - Create Manifest Non-Interactively (Priority: P3)

As a CI/CD pipeline, I want to generate a manifest from a config file or command flags so that manifest creation can be automated and reproducible.

**Why this priority**: Automation is essential for production workflows, but interactive mode serves the initial learning curve first.

**Independent Test**: Can be fully tested by running `hook init --from-config seed.yaml --output manifest.yaml` and verifying the output matches expected structure.

**Acceptance Scenarios**:

1. **Given** a seed config file with minimal inputs, **When** I run `hook init --from-config seed.yaml`, **Then** the tool produces a complete, valid manifest.
2. **Given** a seed config with invalid data, **When** I run `hook init --from-config seed.yaml`, **Then** the tool exits with code 1 and prints actionable errors.
3. **Given** command flags for a single business concept, **When** I run `hook init --concept "customer" --source "CRM"`, **Then** the tool produces a minimal valid manifest with auto-derived key set `CUSTOMER@CRM`.

---

### User Story 4 - View Example Manifests (Priority: P4)

As a learner, I want to view bundled example manifests so that I can understand the expected structure and patterns.

**Why this priority**: Examples accelerate learning but are not blocking for core functionality.

**Independent Test**: Can be fully tested by running `hook examples list` and `hook examples show minimal`.

**Acceptance Scenarios**:

1. **Given** I run `hook examples list`, **Then** the tool lists available examples (minimal, typical, complex).
2. **Given** I run `hook examples show typical`, **Then** the tool prints the typical example manifest to stdout.
3. **Given** I run `hook examples show typical --output ./my-manifest.yaml`, **Then** the tool writes the example to the specified path.

---

### Edge Cases

- What happens when the manifest file path doesn't exist? → ERROR with clear message: "File not found: {path}"
- What happens when the manifest is empty? → ERROR: "Manifest is empty or invalid YAML/JSON"
- What happens when YAML is malformed? → ERROR with line/column: "Parse error at line X, column Y: {details}"
- What happens when a user cancels the wizard mid-flow? → Graceful exit, no partial files written
- What happens when stdin is not a TTY but interactive mode is requested? → ERROR: "Interactive mode requires a terminal. Use --from-config for non-interactive mode."
- What happens when a reserved extension key (targets.hook_sql) contains data in v1? → WARN: "Extension 'hook_sql' is reserved for future use; contents will be ignored in v1."

---

## Requirements *(mandatory)*

### Functional Requirements

#### CLI Commands

- **FR-001**: CLI MUST provide `hook validate <path>` command to validate a manifest file.
- **FR-002**: CLI MUST provide `hook init` command to start the interactive wizard.
- **FR-003**: CLI MUST provide `hook init --from-config <path>` for non-interactive manifest generation.
- **FR-004**: CLI MUST provide `hook examples list` to list bundled examples.
- **FR-005**: CLI MUST provide `hook examples show <name>` to display a specific example.

#### Validation

- **FR-010**: Validator MUST parse YAML and JSON manifest files.
- **FR-011**: Validator MUST validate against the manifest JSON schema (structural validation).
- **FR-012**: Validator MUST enforce all constitutional invariants (semantic validation).
- **FR-013**: Validator MUST categorize diagnostics as ERROR (exit 1) or WARN (exit 0).
- **FR-014**: Validator MUST output human-readable diagnostics by default.
- **FR-015**: Validator MUST output JSON diagnostics when `--json` flag is provided.
- **FR-016**: Each diagnostic MUST include: rule ID, severity, message, manifest path, and suggested fix.

#### Interactive Wizard

- **FR-020**: Wizard MUST follow a frame-first workflow: frames → hooks → key sets → business concepts (bottom-up discovery).
- **FR-021**: Wizard MUST validate each input before proceeding to the next step.
- **FR-022**: Wizard MUST prevent prohibited patterns by construction (e.g., hooks without key sets).
- **FR-023**: Wizard MUST display a summary preview before writing the manifest.
- **FR-024**: Wizard MUST support YAML (default) and JSON (`--format json`) output.
- **FR-025**: Wizard MUST prompt before overwriting existing files.
- **FR-026**: Wizard MUST auto-suggest valid names based on naming conventions.
- **FR-027**: Wizard MUST auto-generate key set values using the recipe: `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`.

#### Manifest Structure

- **FR-030**: Manifest MUST include `manifest_version` field (semver string).
- **FR-031**: Manifest MUST include `schema_version` field indicating manifest schema version.
- **FR-032**: Manifest MUST include `frames` array as the primary content.
- **FR-033**: Each frame MUST include `name`, `source`, and at least one hook.
- **FR-034**: Each hook MUST include `name`, `role`, `concept`, `source`, and `expression`.
- **FR-035**: Hook `role` MUST be `primary` (defines frame grain) or `foreign` (references other concept).
- **FR-036**: Key sets MUST be auto-derived from hook fields as `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]`.
- **FR-037**: Manifest MAY include optional `concepts` array for definitions/examples (enrichment only).
- **FR-038**: Manifest MUST include `settings` object with hook_prefix, weak_hook_prefix, and delimiter.
- **FR-039**: Manifest MUST include `targets` object with optional `hook_sql`, `uss_sql`, `qlik` sub-objects.
- **FR-040**: Extension sub-objects (`targets.*`) MUST be allowed but MAY be empty in v1.

#### Naming Conventions

- **FR-050**: Business concept names MUST be lower_snake_case.
- **FR-051**: Hook names MUST follow pattern: `<prefix><concept>[__<qualifier>]` where default prefix is `_hk__` (strong) or `_wk__` (weak). Examples: `_hk__customer`, `_hk__employee__manager`, `_wk__ref__genre`.
- **FR-052**: Frame names MUST follow pattern: `<schema>.<table>` in lower_snake_case.
- **FR-053**: Hook `source` field MUST be UPPER_SNAKE_CASE (e.g., `CRM`, `SAP`, `CHNK`).
- **FR-054**: Auto-derived key sets follow: `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]` (e.g., `CUSTOMER@CRM`, `ORDER@SAP~AU`, `EMPLOYEE~MANAGER@CRM`).
- **FR-055**: Key set parsing: split on `@` (concept-side vs source-side), then split each on `~` (primary vs variant).
- **FR-056**: Allowed characters: a-z, 0-9, underscore (for names/concepts), A-Z, `@`, `~` (for key sets).

#### Examples

- **FR-060**: Tool MUST ship with at least 3 example manifests: minimal, typical, complex.
- **FR-061**: All bundled examples MUST pass `hook validate` (golden tests).
- **FR-062**: Examples MUST demonstrate different patterns: single concept, header/line, multi-source.

#### Treatment Syntax

- **FR-070**: Treatments MUST follow the syntax `<OPERATION>[:<arg1>[:<arg2>]]`.
- **FR-071**: v1 MUST support the following treatments:
  - `LPAD:<width>:<char>` — Left-pad to width with char (e.g., `LPAD:6:0` → `001234`)
  - `RPAD:<width>:<char>` — Right-pad to width with char
  - `UPPER` — Convert to uppercase
  - `LOWER` — Convert to lowercase
  - `TRIM` — Remove leading/trailing whitespace
- **FR-072**: Multiple treatments MAY be chained with `|` (e.g., `TRIM|UPPER|LPAD:6:0`).
- **FR-073**: Validator MUST reject unknown treatment operations.

#### Output Behavior

- **FR-080**: Validate command MUST collect all errors before reporting (no fail-fast).
- **FR-081**: Validate command MUST print error summary with rule ID, message, and location.
- **FR-082**: Validate command MUST exit 0 if valid, exit 1 if any errors.
- **FR-083**: Validate command MUST NOT discard user input on validation failure.
- **FR-084**: Init wizard MUST save partial progress if user cancels (Ctrl+C saves draft).
- **FR-085**: All CLI output MUST be UTF-8 encoded.

### Key Entities

- **Manifest**: The root document containing all HOOK semantic declarations.
- **Business Concept**: A named entity representing something the organization interacts with.
- **Key Set**: A qualifier that provides context and ensures uniqueness for business keys.
- **Hook**: A calculated column aligning a frame with a business concept.
- **Frame**: A wrapper combining a source table with one or more hooks.
- **Diagnostic**: A validation result with severity, rule ID, message, and path.

---

## Manifest Schema (v1)

```yaml
# Root structure
manifest_version: "1.0.0"          # Version of this manifest (user-controlled)
schema_version: "1.0.0"            # Version of the manifest schema

metadata:
  name: string                     # Human-readable name
  description: string              # Optional description
  created_at: datetime             # ISO 8601 timestamp
  updated_at: datetime             # ISO 8601 timestamp

settings:                          # Manifest-wide settings
  hook_prefix: string              # Default: "_hk__" (strong hooks)
  weak_hook_prefix: string         # Default: "_wk__" (weak hooks)
  delimiter: string                # Default: "|" (separates key set from business key)

frames:
  - name: string                   # Frame name (e.g., "frame.customer")
    source: string                 # Source table reference (e.g., "psa.customer")
    description: string            # Optional description
    hooks:                         # Hooks defined inline within this frame
      - name: string               # Hook column name (e.g., "_hk__customer")
        role: enum                 # "primary" (defines grain) or "foreign" (references other concept)
        concept: string            # Business concept (e.g., "customer")
        qualifier: string          # Optional qualifier suffix (e.g., "manager")
        source: string             # Source system (e.g., "CRM") — key set uses @SOURCE
        tenant: string             # Optional tenant (e.g., "AU") — appended as @SOURCE~TENANT
        expression: string         # Column name or SQL expression (e.g., "customer_id", "order_id || '-' || line_no")
        treatment: string          # Optional transformation (e.g., "TRIM|UPPER|LPAD:6:0")

concepts:                          # Optional: definitions for auto-derived concepts
  - name: string                   # Concept name (must match a concept used in frames)
    description: string            # 1-2 sentence definition
    examples:                      # Real-world examples
      - string
    is_weak: boolean               # True for reference/time/system concepts (default: false)

targets:                           # Extension points for generators (v1: allowed but empty)
  hook_sql: {}                     # Reserved for HOOK SQL generator
  uss_sql: {}                      # Reserved for USS SQL generator  
  qlik: {}                         # Reserved for Qlik generator
```

### Auto-Derived Registries

The tool automatically derives from frames:

- **Key Sets**: `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]` (e.g., `CUSTOMER@CRM`, `ORDER@SAP~AU`, `EMPLOYEE~MANAGER@CRM~AU`)
- **Business Concepts**: Unique concept names across all hooks
- **Hook Registry**: All hooks indexed by name for relationship detection

---

## Validation Rules

### Constitutional Rules (ERROR severity)

| Rule ID | Description | Constitution Reference |
|---------|-------------|------------------------|
| FRAME-001 | Frame must have at least one hook | Principle V |
| FRAME-002 | Frame name must match naming convention (lower_snake_case) | Principle V |
| FRAME-003 | Frame must have exactly one hook with role=primary | Principle VI |
| FRAME-004 | Frame source must not be empty | Principle V |
| HOOK-001 | Hook must have name, role, concept, source, expression | Principle II |
| HOOK-002 | Hook name must match naming convention (prefix + concept + optional qualifier) | HOOK Semantic Definitions |
| HOOK-003 | Hook role must be "primary" or "foreign" | Principle VI |
| HOOK-004 | Hook concept must be lower_snake_case | Principle III |
| HOOK-005 | Hook source must be UPPER_SNAKE_CASE | Principle IV |
| HOOK-006 | Hook expression must not be empty | Principle II |
| HOOK-007 | Treatment must use valid syntax and known operations | Principle II |
| KEYSET-001 | Auto-derived key sets must be globally unique | Principle IV |
| CONCEPT-001 | Concept in `concepts` section must match a concept used in frames | Principle III |
| CONCEPT-002 | Concept description should be 1-2 sentences | Principle III |
| MANIFEST-001 | manifest_version must be valid semver | Principle VIII |
| MANIFEST-002 | schema_version must be valid semver | Principle VIII |

### Advisory Rules (WARN severity)

| Rule ID | Description | Constitution Reference |
|---------|-------------|------------------------|
| CONCEPT-W01 | More than 100 business concepts defined | Principle III (Dunbar guidance) |
| HOOK-W01 | Hook references weak concept without WK_ prefix | HOOK Semantic Definitions |
| FRAME-W01 | Frame has no unique hooks (potential M:M risk) | Principle VI |
| FRAME-W02 | Multiple frames share same source_table | Principle V |
| TARGET-W01 | Reserved extension contains data (ignored in v1) | Principle VIII |

---

## Diagnostic Format

### Human-Readable (default)

```
ERROR [HOOK-001] Hook 'HK_CUSTOMER' is missing key set reference
  at: hooks[0].key_set_id
  fix: Add a valid key_set_id that references an existing key set

WARN [CONCEPT-W01] 142 business concepts defined; consider consolidating (target: ≤100)
  at: business_concepts
  fix: Review concepts for potential consolidation using key sets for sub-types
```

### JSON (--json flag)

```json
{
  "valid": false,
  "errors": [
    {
      "rule_id": "HOOK-001",
      "severity": "ERROR",
      "message": "Hook 'HK_CUSTOMER' is missing key set reference",
      "path": "hooks[0].key_set_id",
      "fix": "Add a valid key_set_id that references an existing key set"
    }
  ],
  "warnings": [
    {
      "rule_id": "CONCEPT-W01",
      "severity": "WARN",
      "message": "142 business concepts defined; consider consolidating (target: ≤100)",
      "path": "business_concepts",
      "fix": "Review concepts for potential consolidation using key sets for sub-types"
    }
  ]
}
```

---

## CLI Behavior Summary

| Command | Exit 0 | Exit 1 | Exit 2 |
|---------|--------|--------|--------|
| `validate` | Valid (may have WARNs) | Has ERRORs | Bad arguments/file not found |
| `init` | Manifest written successfully | Validation failed / user cancelled | Bad arguments |
| `examples list` | Examples listed | - | Bad arguments |
| `examples show` | Example displayed | Example not found | Bad arguments |

---

## Example Manifests

### Example A: Minimal

Single business concept, single hook, one frame. Demonstrates the absolute minimum viable manifest.

```yaml
manifest_version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Minimal Example"
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
    description: "Customer master data"
    hooks:
      - name: "_hk__customer"
        role: "primary"
        concept: "customer"
        source: "CRM"
        expression: "customer_id"

concepts:  # Optional enrichment
  - name: "customer"
    description: "A person or organization that purchases goods or services."
    examples: ["John Smith", "Acme Corporation"]

targets:
  hook_sql: {}
  uss_sql: {}
  qlik: {}
```

**Auto-derived key set**: `CUSTOMER@CRM`

### Example B: Typical (Header/Line)

Invoice header and line items with shared hooks. Demonstrates 1:M relationship pattern.

### Example C: Complex (Multi-Source Traversal)

Customer, Order, Product from multiple sources with region traversal capability. Demonstrates M:M acknowledgement and weak reference hooks.

*(Full YAML for Examples B and C to be included in the shipped examples directory)*

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can validate a manifest in under 1 second for files up to 1000 lines.
- **SC-002**: Users can complete the interactive wizard for a 5-concept manifest in under 5 minutes.
- **SC-003**: 100% of constitutional prohibited patterns are detected by validation.
- **SC-004**: All 3 bundled examples pass validation (golden tests).
- **SC-005**: Error messages include rule ID, path, and actionable fix in 100% of cases.
- **SC-006**: CLI provides correct exit codes for CI integration (0 = success, 1 = validation errors, 2 = usage errors).
- **SC-007**: Wizard-generated manifests pass validation 100% of the time (by construction).

---

## Clarifications

### Session 2026-01-04

- Q: What is the wizard step order and can users skip elements? → A: Frame-first workflow. User starts by defining frames (inspecting source tables), then sketches hooks needed, which surfaces business concepts and key sets naturally. This is bottom-up discovery.
- Q: Is there a recipe for key set values? → A: Yes. Key set values follow the pattern `SOURCE.CONCEPT[.QUALIFIER][~TENANT]`. Examples: `CHNK.ALB`, `SAP.FIN.ACC.NO`, `CRM.CUST~AU`. The wizard should auto-generate key set values based on this recipe.
- Q: Should hooks be global or frame-local? → A: Hooks are defined inline within frames. Each hook has a `role` field: `primary` (defines the frame's grain, e.g., `_hk__order` in order_headers) or `foreign` (references another concept, e.g., `_hk__order` in order_lines). The tool auto-derives a global hook registry for cross-frame relationship detection.
- Q: What is the default hook prefix? → A: Default prefix is `_hk__` (lowercase with trailing double underscore). Weak hooks use `_wk__`. Prefix is configurable in manifest settings.
- Q: What is the treatment syntax? → A: Treatments normalize business key values across systems. v1 supports: `LPAD:<width>:<char>`, `RPAD:<width>:<char>`, `UPPER`, `LOWER`, `TRIM`. Example: `LPAD:6:0` pads `1234` to `001234`.
- Q: How to simplify hook definitions to avoid ID cross-references? → A: Hooks declare `name`, `role`, `concept`, `qualifier`, `source`, `tenant`, `expression`. Key set is auto-derived as `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`. Business concepts and key sets registries are auto-derived by scanning all hooks. Optional `concepts` section for definitions/examples.
- Q: How to handle composite business keys (multiple columns)? → A: `expression` accepts SQL expression syntax (e.g., `order_id || '-' || line_number`). Dialect-specific syntax deferred to generators.
- Q: How should weak hooks be prefixed? → A: User explicitly names hook with `_wk__` prefix. Validator warns if mismatch with `is_weak` flag in concepts section.
- Q: Key set recipe order — concept-first or source-first? → A: Concept-first with `@` separator: `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`. Groups by meaning, unambiguous parsing.
- Q: Should validation block on error or report all errors? → A: Report mode. Collect all errors, print summary, exit 1 if errors but don't lose user work. User shouldn't lose extensive input over one typo.

---

## Assumptions

1. Python 3.10+ is the minimum supported version.
2. YAML is preferred over JSON for human-edited manifests.
3. The manifest schema may evolve, but v1 establishes the baseline.
4. Generator extensions (hook_sql, uss_sql, qlik) will be defined in future features.
5. No database connectivity is required—manifests are purely declarative files.

---

## Out of Scope

- SQL generation (HOOK SQL, USS SQL)
- Qlik script generation
- Graph traversal logic (networkx)
- GUI interface
- Database introspection / reverse engineering
- Manifest diff / merge tooling

---

## Appendix: Constitution Compliance Matrix

| Principle | How This Feature Complies |
|-----------|---------------------------|
| I. Organising Discipline | Manifest declares organization, not transformation logic |
| II. Hooks as Identity | Validation enforces hooks reference key sets, not derived values |
| III. Business Concepts | Schema requires definition + examples; wizard guides creation |
| IV. Key Sets Required | HOOK-001 rule ensures every hook has a key set |
| V. Frames as Wrappers | Frame schema references source_table without transformation |
| VI. Join Safety | grain_hooks + is_unique enable cardinality reasoning |
| VII. Implied Relationships | Relationships derived from shared business_concept_id |
| VIII. Manifest as SSOT | Versioned schema with extension points |
| IX. Generators | targets.* reserved but not implemented in v1 |
| X. Simplicity | Minimal viable schema; no speculative features |
