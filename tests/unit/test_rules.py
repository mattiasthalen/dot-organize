"""Unit tests for ERROR validation rules.

T019: Tests for all ERROR rules (FRAME-001 to 006, HOOK-001 to 007, CONCEPT-001/002/003, MANIFEST-001/002)
"""

from datetime import datetime, timezone

from dot.models.diagnostic import Severity


class TestFrameRules:
    """Tests for FRAME validation rules."""

    def test_frame_001_missing_hooks(self) -> None:
        """FRAME-001: Frame must have at least one hook."""
        from dot.core.rules import validate_frame_has_hooks
        from dot.models.frame import Frame, Source

        # Using model_construct to bypass validation
        frame = Frame.model_construct(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            hooks=[],
        )
        diagnostics = validate_frame_has_hooks(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-001"
        assert diagnostics[0].severity == Severity.ERROR
        assert "frames[0]" in diagnostics[0].path

    def test_frame_001_with_hooks_passes(self) -> None:
        """FRAME-001: Frame with hooks passes validation."""
        from dot.core.rules import validate_frame_has_hooks
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_has_hooks(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_002_invalid_name(self) -> None:
        """FRAME-002: Frame name must match <schema>.<table> lower_snake_case."""
        from dot.core.rules import validate_frame_name
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame.model_construct(
            name="InvalidFrameName",  # Invalid: not lower_snake_case with dot
            source=Source(relation="psa.customer"),
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_name(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-002"
        assert diagnostics[0].severity == Severity.ERROR

    def test_frame_002_valid_name_passes(self) -> None:
        """FRAME-002: Valid frame name passes validation."""
        from dot.core.rules import validate_frame_name
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_name(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_003_missing_primary_hook(self) -> None:
        """FRAME-003: Frame must have at least one primary hook."""
        from dot.core.rules import validate_frame_has_primary_hook
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.order_line",
            source=Source(relation="psa.order_line"),
            hooks=[
                Hook(
                    name="_hk__order",
                    role=HookRole.FOREIGN,  # Only foreign, no primary!
                    concept="order",
                    source="ERP",
                    expr="order_id",
                )
            ],
        )
        diagnostics = validate_frame_has_primary_hook(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-003"
        assert diagnostics[0].severity == Severity.ERROR

    def test_frame_003_with_primary_hook_passes(self) -> None:
        """FRAME-003: Frame with primary hook passes validation."""
        from dot.core.rules import validate_frame_has_primary_hook
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_has_primary_hook(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_003_composite_grain_passes(self) -> None:
        """FRAME-003: Frame with multiple primary hooks (composite grain) passes."""
        from dot.core.rules import validate_frame_has_primary_hook
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.order_line",
            source=Source(relation="psa.order_line"),
            hooks=[
                Hook(
                    name="_hk__order",
                    role=HookRole.PRIMARY,
                    concept="order",
                    source="ERP",
                    expr="order_id",
                ),
                Hook(
                    name="_hk__product",
                    role=HookRole.PRIMARY,
                    concept="product",
                    source="ERP",
                    expr="product_id",
                ),
            ],
        )
        diagnostics = validate_frame_has_primary_hook(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_004_missing_source(self) -> None:
        """FRAME-004: Frame must have source object."""
        from dot.core.rules import validate_frame_source_present
        from dot.models.frame import Frame, Hook, HookRole

        # Using model_construct to bypass validation
        frame = Frame.model_construct(
            name="frame.customer",
            source=None,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_present(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-004"
        assert diagnostics[0].severity == Severity.ERROR

    def test_frame_005_both_relation_and_path(self) -> None:
        """FRAME-005: Source must have exactly one of relation or path."""
        from dot.core.rules import validate_frame_source_exclusivity
        from dot.models.frame import Frame, Hook, HookRole, Source

        # Using model_construct to bypass Source validation
        source = Source.model_construct(
            relation="psa.customer",
            path="//server/qvd/customer.qvd",
        )
        frame = Frame.model_construct(
            name="frame.customer",
            source=source,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_exclusivity(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-005"
        assert diagnostics[0].severity == Severity.ERROR

    def test_frame_006_empty_relation(self) -> None:
        """FRAME-006: Source relation must be non-empty string."""
        from dot.core.rules import validate_frame_source_nonempty
        from dot.models.frame import Frame, Hook, HookRole, Source

        source = Source.model_construct(relation="", path=None)
        frame = Frame.model_construct(
            name="frame.customer",
            source=source,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_nonempty(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-006"
        assert diagnostics[0].severity == Severity.ERROR

    def test_frame_006_empty_path(self) -> None:
        """FRAME-006: Source path must be non-empty string."""
        from dot.core.rules import validate_frame_source_nonempty
        from dot.models.frame import Frame, Hook, HookRole, Source

        source = Source.model_construct(relation=None, path="")
        frame = Frame.model_construct(
            name="frame.customer",
            source=source,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_nonempty(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-006"
        assert diagnostics[0].severity == Severity.ERROR


class TestHookRules:
    """Tests for HOOK validation rules."""

    def test_hook_001_missing_fields(self) -> None:
        """HOOK-001: Hook must have required fields."""
        from dot.core.rules import validate_hook_required_fields
        from dot.models.frame import Hook

        # Using model_construct to bypass validation
        hook = Hook.model_construct(
            name="_hk__customer",
            role=None,
            concept=None,
            source=None,
            expr=None,
        )
        diagnostics = validate_hook_required_fields(hook, "frames[0].hooks[0]")

        # Should have errors for missing role, concept, source, expr
        assert len(diagnostics) >= 1
        assert diagnostics[0].rule_id == "HOOK-001"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_002_invalid_name(self) -> None:
        """HOOK-002: Hook name must match pattern."""
        from dot.core.rules import validate_hook_name
        from dot.models.frame import Hook, HookRole
        from dot.models.settings import Settings

        hook = Hook.model_construct(
            name="invalid_hook_name",  # Missing prefix
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        settings = Settings()
        diagnostics = validate_hook_name(hook, "frames[0].hooks[0]", settings)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-002"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_002_valid_name_passes(self) -> None:
        """HOOK-002: Valid hook name passes validation."""
        from dot.core.rules import validate_hook_name
        from dot.models.frame import Hook, HookRole
        from dot.models.settings import Settings

        hook = Hook(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        settings = Settings()
        diagnostics = validate_hook_name(hook, "frames[0].hooks[0]", settings)
        assert diagnostics == []

    def test_hook_003_invalid_role(self) -> None:
        """HOOK-003: Hook role must be 'primary' or 'foreign'."""
        from dot.core.rules import validate_hook_role
        from dot.models.frame import Hook

        hook = Hook.model_construct(
            name="_hk__customer",
            role="invalid",  # Not a valid role
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        diagnostics = validate_hook_role(hook, "frames[0].hooks[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-003"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_004_invalid_concept(self) -> None:
        """HOOK-004: Hook concept must be lower_snake_case."""
        from dot.core.rules import validate_hook_concept
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__Customer",
            role=HookRole.PRIMARY,
            concept="Customer",  # Invalid: not lower_snake_case
            source="CRM",
            expr="customer_id",
        )
        diagnostics = validate_hook_concept(hook, "frames[0].hooks[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-004"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_005_invalid_source(self) -> None:
        """HOOK-005: Hook source must be UPPER_SNAKE_CASE."""
        from dot.core.rules import validate_hook_source
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="crm",  # Invalid: not UPPER_SNAKE_CASE
            expr="customer_id",
        )
        diagnostics = validate_hook_source(hook, "frames[0].hooks[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-005"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_006_empty_expr(self) -> None:
        """HOOK-006: Hook expr must be non-empty."""
        from dot.core.rules import validate_hook_expr
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="",  # Empty expression
        )
        diagnostics = validate_hook_expr(hook, "frames[0].hooks[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-006"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_006_forbidden_pattern(self) -> None:
        """HOOK-006: Hook expr with forbidden pattern fails."""
        from dot.core.rules import validate_hook_expr
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="SELECT customer_id FROM customers",  # Forbidden pattern
        )
        diagnostics = validate_hook_expr(hook, "frames[0].hooks[0]")

        assert len(diagnostics) >= 1
        assert diagnostics[0].rule_id == "HOOK-006"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_007_duplicate_names_in_frame(self) -> None:
        """HOOK-007: Hook names must be unique within frame."""
        from dot.core.rules import validate_hook_name_uniqueness
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame.model_construct(
            name="frame.order",
            source=Source(relation="psa.order"),
            hooks=[
                Hook(
                    name="_hk__order",
                    role=HookRole.PRIMARY,
                    concept="order",
                    source="ERP",
                    expr="order_id",
                ),
                Hook(
                    name="_hk__order",  # Duplicate!
                    role=HookRole.FOREIGN,
                    concept="order",
                    source="ERP",
                    expr="parent_order_id",
                ),
            ],
        )
        diagnostics = validate_hook_name_uniqueness(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-007"
        assert diagnostics[0].severity == Severity.ERROR

    def test_hook_007_unique_names_passes(self) -> None:
        """HOOK-007: Unique hook names within frame pass validation."""
        from dot.core.rules import validate_hook_name_uniqueness
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.order",
            source=Source(relation="psa.order"),
            hooks=[
                Hook(
                    name="_hk__order",
                    role=HookRole.PRIMARY,
                    concept="order",
                    source="ERP",
                    expr="order_id",
                ),
                Hook(
                    name="_hk__customer",
                    role=HookRole.FOREIGN,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                ),
            ],
        )
        diagnostics = validate_hook_name_uniqueness(frame, "frames[0]")
        assert diagnostics == []


class TestConceptRules:
    """Tests for CONCEPT validation rules."""

    def test_concept_001_unused_concept(self) -> None:
        """CONCEPT-001: Concept must be used in at least one hook."""
        from dot.core.rules import validate_concept_in_frames
        from dot.models.concept import Concept
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
            concepts=[
                Concept(name="customer", description="A customer"),
                Concept(name="order", description="An unused concept"),  # Unused!
            ],
        )
        # Test the "order" concept which is not used in any hook
        diagnostics = validate_concept_in_frames(
            manifest.concepts[1], "concepts[1]", manifest
        )

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "CONCEPT-001"
        assert diagnostics[0].severity == Severity.ERROR

    def test_concept_001_used_concept_passes(self) -> None:
        """CONCEPT-001: Concept used in hooks passes validation."""
        from dot.core.rules import validate_concept_in_frames
        from dot.models.concept import Concept
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
            concepts=[
                Concept(name="customer", description="A customer"),
            ],
        )
        diagnostics = validate_concept_in_frames(
            manifest.concepts[0], "concepts[0]", manifest
        )
        assert diagnostics == []

    def test_concept_002_description_type_check_only(self) -> None:
        """CONCEPT-002: Concept description is type-checked (string, not nested)."""
        from dot.core.rules import validate_concept_description
        from dot.models.concept import Concept

        # Short descriptions are now valid (type check only, no length validation)
        concept = Concept.model_construct(
            name="customer",
            description="Short",  # Any string is valid
        )
        diagnostics = validate_concept_description(concept, "concepts[0]")
        assert diagnostics == []

    def test_concept_002_empty_description_passes(self) -> None:
        """CONCEPT-002: Empty description passes (type check only)."""
        from dot.core.rules import validate_concept_description
        from dot.models.concept import Concept

        concept = Concept.model_construct(
            name="customer",
            description="",  # Empty string is valid
        )
        diagnostics = validate_concept_description(concept, "concepts[0]")
        assert diagnostics == []

    def test_concept_002_long_description_passes(self) -> None:
        """CONCEPT-002: Long descriptions pass (no length validation)."""
        from dot.core.rules import validate_concept_description
        from dot.models.concept import Concept

        concept = Concept.model_construct(
            name="customer",
            description="x" * 500,  # Any length is valid
        )
        diagnostics = validate_concept_description(concept, "concepts[0]")
        assert diagnostics == []

    def test_concept_002_valid_description_passes(self) -> None:
        """CONCEPT-002: Any valid string description passes."""
        from dot.core.rules import validate_concept_description
        from dot.models.concept import Concept

        concept = Concept(
            name="customer",
            description="A person or organization that purchases goods.",
        )
        diagnostics = validate_concept_description(concept, "concepts[0]")
        assert diagnostics == []

    def test_concept_003_duplicate_names(self) -> None:
        """CONCEPT-003: No duplicate concept names in concepts section."""
        from dot.core.rules import validate_no_duplicate_concepts
        from dot.models.concept import Concept
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest.model_construct(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
            concepts=[
                Concept(name="customer", description="A customer definition"),
                Concept(name="customer", description="Duplicate!"),  # Duplicate!
            ],
        )
        diagnostics = validate_no_duplicate_concepts(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "CONCEPT-003"
        assert diagnostics[0].severity == Severity.ERROR


class TestManifestRules:
    """Tests for MANIFEST validation rules."""

    def test_manifest_001_invalid_version(self) -> None:
        """MANIFEST-001: manifest_version must be valid semver."""
        from dot.core.rules import validate_manifest_version
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest.model_construct(
            manifest_version="invalid",  # Not semver
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
        )
        diagnostics = validate_manifest_version(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "MANIFEST-001"
        assert diagnostics[0].severity == Severity.ERROR

    def test_manifest_001_valid_version_passes(self) -> None:
        """MANIFEST-001: Valid semver passes validation."""
        from dot.core.rules import validate_manifest_version
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
        )
        diagnostics = validate_manifest_version(manifest)
        assert diagnostics == []

    def test_manifest_002_invalid_schema_version(self) -> None:
        """MANIFEST-002: schema_version must be valid semver."""
        from dot.core.rules import validate_schema_version
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest.model_construct(
            manifest_version="1.0.0",
            schema_version="v1",  # Not semver
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
        )
        diagnostics = validate_schema_version(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "MANIFEST-002"
        assert diagnostics[0].severity == Severity.ERROR

    def test_manifest_002_valid_schema_version_passes(self) -> None:
        """MANIFEST-002: Valid schema semver passes validation."""
        from dot.core.rules import validate_schema_version
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.customer",
                    source=Source(relation="psa.customer"),
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                )
            ],
        )
        diagnostics = validate_schema_version(manifest)
        assert diagnostics == []


class TestEdgeCaseCoverage:
    """Additional edge case tests for 100% coverage."""

    def test_frame_005_source_is_none(self) -> None:
        """FRAME-005: Early return when source is None."""
        from dot.core.rules import validate_frame_source_exclusivity
        from dot.models.frame import Frame, Hook, HookRole

        frame = Frame.model_construct(
            name="frame.customer",
            source=None,  # Source is None - early return
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_exclusivity(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_005_neither_relation_nor_path(self) -> None:
        """FRAME-005: Source has neither relation nor path."""
        from dot.core.rules import validate_frame_source_exclusivity
        from dot.models.frame import Frame, Hook, HookRole, Source

        source = Source.model_construct(relation=None, path=None)
        frame = Frame.model_construct(
            name="frame.customer",
            source=source,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_exclusivity(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-005"
        assert "neither relation nor path" in diagnostics[0].message

    def test_frame_006_source_is_none(self) -> None:
        """FRAME-006: Early return when source is None."""
        from dot.core.rules import validate_frame_source_nonempty
        from dot.models.frame import Frame, Hook, HookRole

        frame = Frame.model_construct(
            name="frame.customer",
            source=None,
            hooks=[
                Hook(
                    name="_hk__customer",
                    role=HookRole.PRIMARY,
                    concept="customer",
                    source="CRM",
                    expr="customer_id",
                )
            ],
        )
        diagnostics = validate_frame_source_nonempty(frame, "frames[0]")
        assert diagnostics == []

    def test_hook_004_invalid_qualifier(self) -> None:
        """HOOK-004: Invalid qualifier format."""
        from dot.core.rules import validate_hook_concept
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
            qualifier="INVALID_QUALIFIER",  # Should be lower_snake_case
        )
        diagnostics = validate_hook_concept(hook, "frames[0].hooks[0]")

        # Should have error for invalid qualifier
        qualifier_error = [d for d in diagnostics if "qualifier" in d.message.lower()]
        assert len(qualifier_error) == 1
        assert "HOOK-004" in qualifier_error[0].rule_id

    def test_hook_005_invalid_tenant(self) -> None:
        """HOOK-005: Invalid tenant format."""
        from dot.core.rules import validate_hook_source
        from dot.models.frame import Hook, HookRole

        hook = Hook.model_construct(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
            tenant="invalid_tenant",  # Should be UPPER_SNAKE_CASE
        )
        diagnostics = validate_hook_source(hook, "frames[0].hooks[0]")

        # Should have error for invalid tenant
        tenant_error = [d for d in diagnostics if "tenant" in d.message.lower()]
        assert len(tenant_error) == 1
        assert "HOOK-005" in tenant_error[0].rule_id

    def test_concept_002_description_type_check_only(self) -> None:
        """CONCEPT-002: Description is type-check only (short/empty descriptions are valid)."""
        from dot.core.rules import validate_concept_description
        from dot.models.concept import Concept

        # Short description should be valid (no length check)
        concept = Concept.model_construct(
            name="customer",
            description="Short",  # Previously too short, now valid
        )
        diagnostics = validate_concept_description(concept, "concepts[0]")
        assert len(diagnostics) == 0  # No errors for short descriptions

        # Empty description should also be valid
        concept_empty = Concept.model_construct(
            name="customer",
            description="",
        )
        diagnostics_empty = validate_concept_description(concept_empty, "concepts[0]")
        assert len(diagnostics_empty) == 0  # No errors for empty descriptions

    def test_frame_w01_no_hooks_early_return(self) -> None:
        """FRAME-W01: Early return when frame has no hooks."""
        from dot.core.rules import warn_no_primary_only_foreign
        from dot.models.frame import Frame, Source

        frame = Frame.model_construct(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            hooks=None,  # No hooks - early return
        )
        diagnostics = warn_no_primary_only_foreign(frame, "frames[0]")
        assert diagnostics == []