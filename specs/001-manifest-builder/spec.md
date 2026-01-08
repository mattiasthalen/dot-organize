# Feature Specification: Manifest Builder

**Feature Branch**: `001-manifest-builder`
**Created**: 2026-01-04
**Status**: Draft
**Input**: Build `dot` (Data Organize Tool) — a Python package (`dot-organize`) and CLI (`dot`) for guided manifest creation, validation, and output using the HOOK methodology

---

## Problem Statement

Data warehouse practitioners adopting the HOOK methodology need a reliable way to declare and validate their semantic model—business concepts, hooks, key sets, and frames—before generating any SQL, USS, or Qlik outputs. Currently, there is no tooling to:

1. Guide users through creating a constitution-compliant manifest
2. Validate manifests against HOOK semantic rules and prohibited patterns
3. Produce stable, versioned manifest files that can later be extended with generator overlays

Without such tooling, users risk creating invalid manifests that violate HOOK principles, leading to unsafe joins, grain amplification, and integration failures.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Existing Manifest (Priority: P1)

As a data engineer, I want to validate an existing manifest file so that I can ensure it complies with all HOOK constitutional constraints before using it for downstream generation.

**Why this priority**: Validation is the foundation—users need confidence their manifest is correct before any other operation. This also enables CI integration from day one.

**Independent Test**: Can be fully tested by running `dot validate path/to/manifest.yaml` against valid and invalid manifests and verifying correct exit codes and error messages.

**Acceptance Scenarios**:

1. **Given** a valid manifest file, **When** I run `dot validate manifest.yaml`, **Then** the tool exits with code 0 and prints "Manifest is valid."
2. **Given** a manifest with a hook missing required fields (name, role, concept, source, or expr), **When** I run `dot validate manifest.yaml`, **Then** the tool exits with code 1 and prints an ERROR referencing rule ID `HOOK-001` with the path to the invalid hook.
3. **Given** a manifest with duplicate hook names within the same frame, **When** I run `dot validate manifest.yaml`, **Then** the tool exits with code 1 and prints an ERROR referencing rule ID `HOOK-007`.
4. **Given** a manifest with a warning-level issue (e.g., >100 business concepts), **When** I run `dot validate manifest.yaml`, **Then** the tool exits with code 0 but prints a WARN message.
5. **Given** any manifest, **When** I run `dot validate manifest.yaml --json`, **Then** the tool outputs machine-readable JSON diagnostics.

---

### User Story 2 - Create Manifest via Interactive Wizard (Priority: P2)

As a new HOOK user, I want an interactive wizard that guides me through creating a valid manifest so that I don't have to memorize the schema or constitution rules.

**Why this priority**: After validation, guided creation is the primary user journey for new adopters. It lowers the barrier to entry significantly.

**Independent Test**: Can be fully tested by running `dot init` in interactive mode, providing inputs, and verifying the output file passes validation.

**Acceptance Scenarios**:

1. **Given** I run `dot init`, **When** the wizard prompts for business concepts, **Then** I can enter concept names, definitions, and examples with validation feedback.
2. **Given** I enter an invalid business concept name (e.g., containing spaces), **When** I submit, **Then** the wizard rejects it with an actionable error and re-prompts.
3. **Given** I complete the wizard, **When** I confirm the summary preview, **Then** the wizard writes a valid YAML manifest to the specified location.
4. **Given** the output file already exists, **When** the wizard attempts to write, **Then** it prompts for confirmation before overwriting (or offers a new filename).
5. **Given** I run `dot init --output manifest.json`, **When** I complete the wizard, **Then** the output is valid JSON instead of YAML.
6. **Given** I cancel the wizard mid-flow with Ctrl+C, **When** I have entered at least one complete frame, **Then** the wizard saves a `.dot-draft.yaml` file in the current directory with progress so far.

---

### User Story 3 - Create Manifest Non-Interactively (Priority: P3)

As a CI/CD pipeline, I want to generate a manifest from a config file or command flags so that manifest creation can be automated and reproducible.

**Why this priority**: Automation is essential for production workflows, but interactive mode serves the initial learning curve first.

**Independent Test**: Can be fully tested by running `dot init --from-config seed.yaml --output manifest.yaml` and verifying the output matches expected structure.

**Acceptance Scenarios**:

1. **Given** a seed config file with minimal inputs, **When** I run `dot init --from-config seed.yaml`, **Then** the tool produces a complete, valid manifest.
2. **Given** a seed config with invalid data, **When** I run `dot init --from-config seed.yaml`, **Then** the tool exits with code 1 and prints actionable errors.
3. **Given** command flags for a single business concept, **When** I run `dot init --concept "customer" --source "CRM"`, **Then** the tool produces a minimal valid manifest with auto-derived key set `CUSTOMER@CRM`.

---

### User Story 4 - View Example Manifests (Priority: P4)

As a learner, I want to view bundled example manifests so that I can understand the expected structure and patterns.

**Why this priority**: Examples accelerate learning but are not blocking for core functionality.

**Independent Test**: Can be fully tested by running `dot examples list` and `dot examples show minimal`.

**Acceptance Scenarios**:

1. **Given** I run `dot examples list`, **Then** the tool lists available examples (minimal, typical, complex).
2. **Given** I run `dot examples show typical`, **Then** the tool prints the typical example manifest to stdout.
3. **Given** I run `dot examples show typical --output ./my-manifest.yaml`, **Then** the tool writes the example to the specified path.

---

### Edge Cases

- What happens when the manifest file path doesn't exist? → ERROR with clear message: "File not found: {path}"
- What happens when the manifest is empty? → ERROR: "Manifest is empty or invalid YAML/JSON"
- What happens when YAML is malformed? → ERROR with line/column: "Parse error at line X, column Y: {details}"
- What happens when a user cancels the wizard mid-flow? → Graceful exit, saves `.dot-draft.yaml` if at least one frame completed (FR-084)
- What happens when stdin is not a TTY but interactive mode is requested? → ERROR: "Interactive mode requires a terminal. Use --from-config for non-interactive mode."
- What happens when manifest has zero frames? → ERROR [FRAME-001]: "Manifest must have at least one frame"
- What happens when YAML parse fails mid-file? → Fail fast with line/column error; no partial manifest recovery in v1 (v2 consideration: attempt to recover valid portions)
- What happens when a frame has multiple primary hooks? → Valid for composite grain (e.g., order_lines with `_hk__order` + `_hk__product`). Order of primary hooks defines grain order.
- What happens when concept in concepts section is never used in hooks? → ERROR [CONCEPT-001]: "Concept '{name}' defined but not used in any hook"
- What happens with duplicate concept names in concepts section? → ERROR: "Duplicate concept name: '{name}'"
- What happens when file save fails (permission denied)? → ERROR: "Cannot write to '{path}': {os_error}". Manifest not saved, user prompted to try different path.
- What happens with Unicode in concept names? → Allowed in descriptions/examples only. Concept names, hook names, sources MUST be ASCII (a-z, A-Z, 0-9, underscore).
- What happens with circular hook references? → Not validated in v1 (deferred to graph traversal feature). Circular references are semantically valid for M:M relationships.

---

### Limits and Constraints

- **Maximum frames per manifest**: No hard limit, but WARN if >50 frames (performance advisory)
- **Maximum hooks per frame**: No hard limit, but WARN if >20 hooks per frame
- **Maximum concepts**: WARN if >100 concepts (Dunbar guidance, CONCEPT-W01)
- **Concurrent wizard sessions**: Not supported. Wizard uses stdin/stdout; multiple terminals may conflict.

---

## Requirements *(mandatory)*

### Functional Requirements

#### CLI Commands

- **FR-001**: CLI MUST provide `dot validate <path>` command to validate a manifest file.
- **FR-002**: CLI MUST provide `dot init` command to start the interactive wizard.
- **FR-003**: CLI MUST provide `dot init --from-config <path>` for non-interactive manifest generation.
- **FR-004**: CLI MUST provide `dot examples list` to list bundled examples.
- **FR-005**: CLI MUST provide `dot examples show <name>` to display a specific example.

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
- **FR-026**: Wizard MUST auto-suggest valid names based on naming conventions:
  - Relation suggestion: Use table name from frame name (e.g., `frame.nw__customers` → `raw.nw__customers`)
  - Concept suggestion: Use last element after splitting table name by `__` (e.g., `nw__customers` → `customers`)
- **FR-027**: Wizard MUST auto-generate key set values using the recipe: `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`.
- **FR-028**: Wizard MUST prompt for foreign hooks after primary hooks are complete, allowing users to define relationships to other concepts within the same frame.
- **FR-029**: Wizard MUST prompt for source system on EACH hook individually. Hooks within the same frame MAY reference different source systems.

#### Manifest Structure

- **FR-030**: Manifest MUST include `manifest_version` field (semver string).
- **FR-031**: Manifest MUST include `schema_version` field indicating manifest schema version.
- **FR-032**: Manifest MUST include `frames` array as the primary content.
- **FR-033**: Each frame MUST include `name`, `source` (object), and at least one hook.
- **FR-033a**: Frame `source` object MUST contain exactly one of: `relation` (string for relational sources like `db.schema.table`) or `path` (string for file sources like QVD paths).
- **FR-033b**: Frame `source.relation` and `source.path` MUST NOT both be present.
- **FR-033c**: Both `relation` and `path` values MUST be non-empty strings when present.
- **FR-034**: Each hook MUST include `name`, `role`, `concept`, `source`, and `expr`.
- **FR-034a**: Hook `expr` is a SQL expression (Manifest SQL subset) for Feature 001. Qlik expression support may be introduced in a later feature.
- **FR-035**: Hook `role` MUST be `primary` (defines frame grain, one or more per frame) or `foreign` (references other concept).
- **FR-036**: Key sets MUST be auto-derived from hook fields as `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]`.
- **FR-037**: Manifest MUST include `concepts` array with all distinct concepts from hooks. Each concept entry MUST include `name` and `frames` (list of frame names where this concept appears). Description, examples, and is_weak are optional enrichment fields.
- **FR-037a**: Wizard MUST auto-populate `concepts` array with: `name` (from hooks), `frames` (derived), `is_weak` (true if hook uses `_wk__` prefix), and empty `description`/`examples` for user enrichment.
- **FR-038**: Manifest MUST include `settings` object with hook_prefix, weak_hook_prefix, and delimiter.
- **FR-039**: Manifest MUST include `keysets` array with all auto-derived key sets. Each keyset entry MUST include `name` (the key set string), `concept` (the business concept), and `frames` (list of frame names where this key set is derived).
- **FR-039a**: Wizard MUST auto-populate `keysets` array from all hooks using the derivation pattern in FR-054.

#### Naming Conventions

- **FR-050**: Business concept names MUST be lower_snake_case.
- **FR-051**: Hook names MUST follow pattern: `<prefix><concept>[__<qualifier>]` where default prefix is `_hk__` (strong) or `_wk__` (weak). Examples: `_hk__customer`, `_hk__employee__manager`, `_wk__ref__genre`.
- **FR-052**: Frame names MUST follow pattern: `<schema>.<table>` in lower_snake_case.
- **FR-053**: Hook `source` field MUST be UPPER_SNAKE_CASE (e.g., `CRM`, `SAP`, `CHNK`).
- **FR-054**: Auto-derived key sets follow: `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]` (e.g., `CUSTOMER@CRM`, `ORDER@SAP~AU`, `EMPLOYEE~MANAGER@CRM`).
- **FR-055**: Key set parsing: split on `@` (concept-side vs source-side), then split each on `~` (primary vs variant).
- **FR-056**: Allowed characters: a-z, 0-9, underscore (for names/concepts), A-Z, `@`, `~` (for key sets).

#### Examples

- **FR-060**: Tool MUST ship with at least 4 example manifests: minimal (relation), file-based (path), typical, complex.
- **FR-061**: All bundled examples MUST pass `dot validate` (golden tests).
- **FR-062**: Examples MUST demonstrate different patterns: single concept, file vs relation source, header/line, multi-source.

#### Output Behavior

- **FR-080**: Validate command MUST collect all errors before reporting (no fail-fast).
- **FR-081**: Validate command MUST print error summary with rule ID, message, and location.
- **FR-082**: Validate command MUST exit 0 if valid, exit 1 if any errors.
- **FR-083**: Validate command MUST NOT discard user input on validation failure.
- **FR-084**: Init wizard MUST save partial progress if user cancels (Ctrl+C saves draft).
- **FR-085**: All CLI output MUST be UTF-8 encoded.
- **FR-086**: Default manifest filename MUST be `manifest.yaml` (or `manifest.json` with `--format json`). Draft files use `.manifest-draft.yaml`.

### Key Entities

- **Manifest**: The root document containing all HOOK semantic declarations.
- **Business Concept**: A named entity representing something the organization interacts with.
- **Key Set**: A qualifier that provides context and ensures uniqueness for business keys.
- **Hook**: A calculated column aligning a frame with a business concept.
- **Frame**: A wrapper combining a source table with one or more hooks.
- **Diagnostic**: A validation result with severity, rule ID, message, and path.

### Non-Functional Requirements

#### Performance

- **NFR-001**: Validation MUST complete in <1 second for manifests up to 1000 lines on standard hardware (4-core CPU, 8GB RAM).
- **NFR-002**: Validation MUST complete in <5 seconds for manifests up to 10,000 lines.
- **NFR-003**: Memory usage MUST stay under 100MB for manifests up to 1MB file size.

#### Accessibility

- **NFR-010**: CLI error output MUST be compatible with screen readers (no ANSI escape codes in error messages by default).
- **NFR-011**: CLI MUST support `--no-color` flag to disable colored output.
- **NFR-012**: Error messages MUST be self-contained (no reliance on color alone for meaning).

#### Internationalization

- **NFR-020**: All CLI output MUST be UTF-8 encoded (FR-085).
- **NFR-021**: Error messages are English-only in v1 (i18n deferred to future version).
- **NFR-022**: Manifest content (descriptions, examples) MAY contain any valid UTF-8 text.
- **NFR-023**: Identifiers (concept names, hook names, sources) MUST be ASCII-only (a-z, A-Z, 0-9, underscore).

#### Compatibility

- **NFR-030**: Schema version changes MUST follow semver: patch = backwards compatible fixes, minor = backwards compatible additions, major = breaking changes.
- **NFR-031**: Manifests with schema_version 1.x.x MUST remain valid with all 1.x.x validators.
- **NFR-032**: Unknown fields in manifest SHOULD be ignored with WARN (forward compatibility).

#### Implementation Standards

- **NFR-040**: All code MUST pass `ruff check` and `ruff format` (linting and formatting).
- **NFR-041**: All code MUST pass `mypy --strict` (static type checking).
- **NFR-042**: Pre-commit hooks MUST enforce ruff and mypy before commits.
- **NFR-043**: Tests MUST be written before implementation (TDD); tests MUST fail before implementation code is written.

#### Programming Paradigm (Constitution §Project-Level Constraints)

- **NFR-050**: All code MUST follow the **functional-first programming paradigm** per constitution v1.1.0.
- **NFR-051**: Data structures MUST be immutable. Use frozen Pydantic models (permitted as framework-mandated pattern), frozen dataclasses, NamedTuple, or TypedDict.
- **NFR-052**: Logic MUST be expressed as pure functions that take inputs and return outputs without side effects.
- **NFR-053**: State MUST NOT be encapsulated in objects. Stateful operations (I/O, configuration) MUST be isolated at application boundaries (io/, cli/ layers).
- **NFR-054**: Classes are PERMITTED only for: frozen data containers, Protocol/ABC type contracts, framework-mandated patterns (Typer commands, Pydantic models).
- **NFR-055**: Inheritance MUST NOT be used for code reuse; use composition or higher-order functions instead.
- **NFR-056**: Methods on data classes MUST be limited to `__str__`, `__repr__`, `__hash__`, `__eq__`, and property accessors. Business logic MUST NOT reside in methods.
- **NFR-057**: Wizard/CLI state containers MUST use frozen dataclasses. State transitions MUST return new instances rather than mutating existing ones. Helper functions (e.g., `has_meaningful_data`, `to_dict`) MUST be standalone pure functions, not methods on state classes.
- **NFR-058**: Exception classes are PERMITTED as a Python idiom but MUST NOT contain business logic beyond message formatting.

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
    source:                        # Source specification (exactly one of relation or path)
      relation: string             # Relational source (e.g., "db.schema.table") - exclusive with path
      path: string                 # File source (e.g., QVD path) - exclusive with relation
    description: string            # Optional description
    hooks:                         # Hooks defined inline within this frame
      - name: string               # Hook column name (e.g., "_hk__customer")
        role: enum                 # "primary" (defines grain) or "foreign" (references other concept)
        concept: string            # Business concept (e.g., "customer")
        qualifier: string          # Optional qualifier suffix (e.g., "manager")
        source: string             # Source system (e.g., "CRM") — key set uses @SOURCE
        tenant: string             # Optional tenant (e.g., "AU") — appended as @SOURCE~TENANT
        expr: string               # SQL expression for business key (Manifest SQL subset)

concepts:                          # Auto-populated from hooks (FR-037)
  - name: string                   # Concept name (derived from hooks)
    frames:                        # Frames where this concept appears (auto-derived)
      - string
    description: string            # Optional: enrichment text (type check only)
    examples:                      # Optional: Real-world examples
      - string
    is_weak: boolean               # True if hook uses _wk__ prefix (default: false)

keysets:                           # Auto-populated from hooks (FR-039)
  - name: string                   # Key set string (e.g., "CUSTOMER@CRM")
    concept: string                # Business concept this key set belongs to
    frames:                        # Frames where this key set is derived
      - string
```

### Auto-Derived Registries

The tool automatically derives from frames and populates manifest sections:

- **Key Sets** (`keysets` section): `<CONCEPT>[~<QUALIFIER>]@<SOURCE>[~<TENANT>]` with frame references
- **Business Concepts** (`concepts` section): Unique concept names with frame references
- **Hook Registry**: All hooks indexed by name for relationship detection (runtime only, not persisted)

---

## Validation Rules

### Constitutional Rules (ERROR severity)

| Rule ID | Description | Constitution Reference |
|---------|-------------|------------------------|
| FRAME-001 | Frame must have at least one hook | Principle V |
| FRAME-002 | Frame name must match naming convention (lower_snake_case with dot separator) | Principle V |
| FRAME-003 | Frame must have at least one hook with role=primary (multiple allowed for composite grain) | Principle VI |
| FRAME-004 | Frame source object must be present | Principle V |
| FRAME-005 | Frame source must have exactly one of `relation` or `path` (exclusivity) | Principle V |
| FRAME-006 | Frame source.relation or source.path must be non-empty string | Principle V |
| HOOK-001 | Hook must have name, role, concept, source, expr | Principle II |
| HOOK-002 | Hook name must match naming convention (prefix + concept + optional qualifier) | HOOK Semantic Definitions |
| HOOK-003 | Hook role must be "primary" or "foreign" | Principle VI |
| HOOK-004 | Hook concept must be lower_snake_case | Principle III |
| HOOK-005 | Hook source must be UPPER_SNAKE_CASE | Principle IV |
| HOOK-006 | Hook expr must be non-empty and valid SQL expression (Manifest SQL subset; see [data-model.md §Expression Validation](data-model.md#expression-validation)) | Principle II |
| HOOK-007 | Hook names must be unique within the same frame | Principle V |
| CONCEPT-001 | Concept in `concepts` section must match a concept used in at least one hook | Principle III |
| CONCEPT-002 | Concept description must be a string (type validation only) | Principle III |
| CONCEPT-003 | Duplicate concept name in `concepts` section | Principle III |
| MANIFEST-001 | manifest_version must be valid semver (MAJOR.MINOR.PATCH, no pre-release) | Principle VIII |
| MANIFEST-002 | schema_version must be valid semver (MAJOR.MINOR.PATCH, no pre-release) | Principle VIII |

### Advisory Rules (WARN severity)

| Rule ID | Description | Constitution Reference |
|---------|-------------|------------------------|
| CONCEPT-W01 | More than 100 business concepts defined | Principle III (Dunbar guidance) |
| HOOK-W01 | Hook uses `_wk__` prefix but concept.is_weak is False (or vice versa) | HOOK Semantic Definitions |
| FRAME-W01 | Frame has only foreign hooks (no primary = undefined grain) | Principle VI |
| FRAME-W02 | Multiple frames share same source field value | Principle V |
| FRAME-W03 | Frame has more than 20 hooks (complexity advisory) | Principle X |
| MANIFEST-W01 | Manifest has more than 50 frames (performance advisory) | Principle X |
| MANIFEST-W02 | Unknown fields in manifest root (forward compatibility warning). Known fields: `manifest_version`, `schema_version`, `metadata`, `settings`, `frames`, `concepts`, `keysets` | Principle VIII |

---

## Diagnostic Format

### Human-Readable (default)

```
ERROR [HOOK-001] Hook '_hk__customer' is missing required field 'expr'
  at: frames[0].hooks[0].expr
  fix: Add expr with a valid SQL expression for the business key

WARN [CONCEPT-W01] 142 business concepts defined; consider consolidating (target: ≤100)
  at: concepts
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
      "message": "Hook '_hk__customer' is missing required field 'expr'",
      "path": "frames[0].hooks[0].expr",
      "fix": "Add expr with a valid SQL expression for the business key"
    }
  ],
  "warnings": [
    {
      "rule_id": "CONCEPT-W01",
      "severity": "WARN",
      "message": "142 business concepts defined; consider consolidating (target: ≤100)",
      "path": "concepts",
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
    source:
      relation: "psa.customer"     # Relational source
    description: "Customer master data"
    hooks:
      - name: "_hk__customer"
        role: "primary"
        concept: "customer"
        source: "CRM"
        expr: "customer_id"

concepts:  # Optional enrichment
  - name: "customer"
    description: "A person or organization that purchases goods or services."
    examples: ["John Smith", "Acme Corporation"]
```

**Auto-derived key set**: `CUSTOMER@CRM`

### Example B: File-Based Source (QVD)

Demonstrates a frame with a file-based source (path) instead of relational source.

```yaml
frames:
  - name: "frame.product"
    source:
      path: "//server/qvd/product_master.qvd"  # File source (QVD)
    description: "Product master from QVD extract"
    hooks:
      - name: "_hk__product"
        role: "primary"
        concept: "product"
        source: "ERP"
        expr: "product_code"
```

**Auto-derived key set**: `PRODUCT@ERP`

### Example C: Typical (Header/Line)

Invoice header and line items with shared hooks. Demonstrates 1:M relationship pattern.

### Example D: Complex (Multi-Source Traversal)

Customer, Order, Product from multiple sources with region traversal capability. Demonstrates M:M acknowledgement and weak reference hooks.

*(Full YAML for Examples C and D to be included in the shipped examples directory)*

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can validate a manifest in under 1 second for files up to 1000 lines.
- **SC-002**: Users can complete the interactive wizard for a 5-concept manifest in under 5 minutes.
- **SC-003**: 100% of constitutional prohibited patterns are detected by validation.
- **SC-004**: All 4 bundled examples pass validation (golden tests).
- **SC-005**: Error messages include rule ID, path, and actionable fix in 100% of cases.
- **SC-006**: CLI provides correct exit codes for CI integration (0 = success, 1 = validation errors, 2 = usage errors).
- **SC-007**: Wizard-generated manifests pass validation 100% of the time (by construction).

---

## Clarifications

### Session 2026-01-04

- Q: What is the wizard step order and can users skip elements? → A: Frame-first workflow. User starts by defining frames (inspecting source tables), then sketches hooks needed, which surfaces business concepts and key sets naturally. This is bottom-up discovery. **Wizard flow**: 1) Enter frame name → 2) Enter source (relation or path) → 3) Define hooks (name, role, concept, qualifier, source, tenant, expr) → 4) Wizard displays auto-derived key set after each hook → 5) Add more hooks or finish frame → 6) Add more frames or preview → 7) Review summary → 8) Save manifest. Wizard auto-generates `created_at` and `updated_at` timestamps.
- Q: Is there a recipe for key set values? → A: Yes. Key set values follow the pattern `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`. Examples: `CUSTOMER@CRM`, `ORDER@SAP~AU`, `EMPLOYEE~MANAGER@CRM`. The wizard auto-generates and displays key set values after each hook definition.
- Q: Should hooks be global or frame-local? → A: Hooks are defined inline within frames. Each hook has a `role` field: `primary` (defines the frame's grain, e.g., `_hk__order` in order_headers) or `foreign` (references another concept, e.g., `_hk__order` in order_lines). The tool auto-derives a global hook registry for cross-frame relationship detection.
- Q: What is the default hook prefix? → A: Default prefix is `_hk__` (lowercase with trailing double underscore). Weak hooks use `_wk__`. Prefix is configurable in manifest settings.
- Q: How to simplify hook definitions to avoid ID cross-references? → A: Hooks declare `name`, `role`, `concept`, `qualifier`, `source`, `tenant`, `expr`. Key set is auto-derived as `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`. Business concepts and key sets registries are auto-derived by scanning all hooks. Optional `concepts` section for definitions/examples.
- Q: How to handle composite business keys (multiple columns)? → A: `expr` accepts SQL expression syntax (e.g., `order_id || '-' || line_number`). Dialect-specific syntax deferred to generators.
- Q: How should weak hooks be prefixed? → A: User explicitly names hook with `_wk__` prefix. Validator warns if mismatch with `is_weak` flag in concepts section.
- Q: Key set recipe order — concept-first or source-first? → A: Concept-first with `@` separator: `CONCEPT[~QUALIFIER]@SOURCE[~TENANT]`. Groups by meaning, unambiguous parsing.
- Q: Should validation block on error or report all errors? → A: Report mode. Collect all errors, print summary, exit 1 if errors but don't lose user work. User shouldn't lose extensive input over one typo.
- Q: Should the expression field be named `expr` or `expression`? → A: Use `expr` for v1 (concise, matches schema). Future versions may add `expr_qlik` for Qlik expressions.

### Session 2026-01-06

- Q: Can a frame have multiple primary hooks for composite grain? → A: Yes. Allow multiple hooks with role="primary" where the combination defines frame grain. Example: `order_lines` has grain = (`_hk__order`, `_hk__product`). Order of primary hooks matters for grain definition. FRAME-003 rule changed from "exactly one" to "at least one" primary hook.
- Q: How to handle primary key aliases (same concept, different source columns)? → A: Use qualifiers to distinguish aliases. Example: `_hk__order__number` (concept=`order`, qualifier=`number`) and `_hk__order__id` (concept=`order`, qualifier=`id`) produce different key sets: `ORDER~NUMBER@SOURCE` and `ORDER~ID@SOURCE`. They represent the same business concept via different source columns. No schema change needed; qualifiers already support this pattern.

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
- Qlik expression support in `expr` field (Feature 001 is SQL-only)
- Graph traversal logic (networkx)
- GUI interface (including marimo UI)
- Database introspection / reverse engineering
- Manifest diff / merge tooling

---

## Appendix: Constitution Compliance Matrix

| Principle | How This Feature Complies |
|-----------|---------------------------|
| I. Organising Discipline | Manifest declares organization, not transformation logic |
| II. Hooks as Identity | Validation enforces hooks use expr (source expression), not derived values |
| III. Business Concepts | Schema requires definition + examples; wizard guides creation |
| IV. Key Sets Required | Key sets auto-derived from hook fields (CONCEPT@SOURCE pattern) |
| V. Frames as Wrappers | Frame schema references source without transformation |
| VI. Join Safety | Hook role (primary/foreign) enables grain and cardinality reasoning |
| VII. Implied Relationships | Relationships derived from shared concept names across hooks |
| VIII. Manifest as SSOT | Versioned schema with extension points |
| X. Simplicity | Minimal viable schema; no speculative features |
| Functional Paradigm | Pure functions in core/, frozen Pydantic models, frozen dataclasses for CLI state, no mutable stateful classes, composition over inheritance (NFR-050 to NFR-058) |
