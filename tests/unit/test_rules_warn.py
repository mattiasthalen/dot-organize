"""Unit tests for WARN validation rules.

T020: Tests for all WARN rules (CONCEPT-W01, HOOK-W01, FRAME-W01/W02/W03, MANIFEST-W01/W02)
"""

from datetime import datetime, timezone

from dot.models.diagnostic import Severity


class TestConceptWarnings:
    """Tests for CONCEPT warning rules."""

    def test_concept_w01_too_many_concepts(self) -> None:
        """CONCEPT-W01: Warn if more than 100 concepts."""
        from dot.core.rules import warn_concept_count
        from dot.models.concept import Concept
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        # Create 101 concepts
        concepts = [
            Concept(name=f"concept_{i}", description=f"Concept number {i} description here")
            for i in range(101)
        ]
        # Create hooks for all concepts to avoid CONCEPT-001 errors
        hooks = [
            Hook(
                name=f"_hk__concept_{i}",
                role=HookRole.PRIMARY if i == 0 else HookRole.FOREIGN,
                concept=f"concept_{i}",
                source="SRC",
                expr=f"id_{i}",
            )
            for i in range(101)
        ]
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=[
                Frame(
                    name="frame.test",
                    source=Source(relation="psa.test"),
                    hooks=hooks,
                )
            ],
            concepts=concepts,
        )
        diagnostics = warn_concept_count(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "CONCEPT-W01"
        assert diagnostics[0].severity == Severity.WARN

    def test_concept_w01_under_threshold_passes(self) -> None:
        """CONCEPT-W01: No warning if 100 or fewer concepts."""
        from dot.core.rules import warn_concept_count
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
                Concept(name="customer", description="A customer description"),
            ],
        )
        diagnostics = warn_concept_count(manifest)
        assert diagnostics == []


class TestHookWarnings:
    """Tests for HOOK warning rules."""

    def test_hook_w01_prefix_mismatch(self) -> None:
        """HOOK-W01: Warn if weak hook prefix but concept is_weak=False."""
        from dot.core.rules import warn_weak_hook_mismatch
        from dot.models.concept import Concept
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_wk__customer",  # Weak prefix
            role=HookRole.FOREIGN,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        # Concept with is_weak=False
        concepts = [Concept(name="customer", description="A customer", is_weak=False)]

        diagnostics = warn_weak_hook_mismatch(hook, "frames[0].hooks[0]", concepts)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "HOOK-W01"
        assert diagnostics[0].severity == Severity.WARN

    def test_hook_w01_matching_prefix_passes(self) -> None:
        """HOOK-W01: No warning if prefix matches is_weak flag."""
        from dot.core.rules import warn_weak_hook_mismatch
        from dot.models.concept import Concept
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_wk__date",  # Weak prefix
            role=HookRole.FOREIGN,
            concept="date",
            source="SYS",
            expr="date_id",
        )
        # Concept with is_weak=True
        concepts = [Concept(name="date", description="A calendar date", is_weak=True)]

        diagnostics = warn_weak_hook_mismatch(hook, "frames[0].hooks[0]", concepts)
        assert diagnostics == []


class TestFrameWarnings:
    """Tests for FRAME warning rules."""

    def test_frame_w01_no_primary_only_foreign(self) -> None:
        """FRAME-W01: Warn if frame has only foreign hooks (no primary)."""
        from dot.core.rules import warn_no_primary_only_foreign
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.lookup",
            source=Source(relation="psa.lookup"),
            hooks=[
                Hook(
                    name="_hk__ref",
                    role=HookRole.FOREIGN,  # Only foreign
                    concept="ref",
                    source="SYS",
                    expr="ref_id",
                )
            ],
        )
        diagnostics = warn_no_primary_only_foreign(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-W01"
        assert diagnostics[0].severity == Severity.WARN

    def test_frame_w01_with_primary_passes(self) -> None:
        """FRAME-W01: No warning if frame has primary hook."""
        from dot.core.rules import warn_no_primary_only_foreign
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
        diagnostics = warn_no_primary_only_foreign(frame, "frames[0]")
        assert diagnostics == []

    def test_frame_w02_duplicate_source(self) -> None:
        """FRAME-W02: Warn if multiple frames use same source."""
        from dot.core.rules import warn_duplicate_source
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
                    name="frame.customer_v1",
                    source=Source(relation="psa.customer"),  # Same source
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="customer_id",
                        )
                    ],
                ),
                Frame(
                    name="frame.customer_v2",
                    source=Source(relation="psa.customer"),  # Same source!
                    hooks=[
                        Hook(
                            name="_hk__customer",
                            role=HookRole.PRIMARY,
                            concept="customer",
                            source="CRM",
                            expr="cust_id",
                        )
                    ],
                ),
            ],
        )
        diagnostics = warn_duplicate_source(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-W02"
        assert diagnostics[0].severity == Severity.WARN

    def test_frame_w02_unique_sources_passes(self) -> None:
        """FRAME-W02: No warning if all sources are unique."""
        from dot.core.rules import warn_duplicate_source
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
                ),
                Frame(
                    name="frame.order",
                    source=Source(relation="psa.order"),  # Different source
                    hooks=[
                        Hook(
                            name="_hk__order",
                            role=HookRole.PRIMARY,
                            concept="order",
                            source="ERP",
                            expr="order_id",
                        )
                    ],
                ),
            ],
        )
        diagnostics = warn_duplicate_source(manifest)
        assert diagnostics == []

    def test_frame_w03_too_many_hooks(self) -> None:
        """FRAME-W03: Warn if frame has more than 20 hooks."""
        from dot.core.rules import warn_too_many_hooks
        from dot.models.frame import Frame, Hook, HookRole, Source

        hooks = [
            Hook(
                name=f"_hk__concept_{i}",
                role=HookRole.PRIMARY if i == 0 else HookRole.FOREIGN,
                concept=f"concept_{i}",
                source="SRC",
                expr=f"id_{i}",
            )
            for i in range(21)  # 21 hooks
        ]
        frame = Frame(
            name="frame.test",
            source=Source(relation="psa.test"),
            hooks=hooks,
        )
        diagnostics = warn_too_many_hooks(frame, "frames[0]")

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "FRAME-W03"
        assert diagnostics[0].severity == Severity.WARN

    def test_frame_w03_under_threshold_passes(self) -> None:
        """FRAME-W03: No warning if 20 or fewer hooks."""
        from dot.core.rules import warn_too_many_hooks
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
        diagnostics = warn_too_many_hooks(frame, "frames[0]")
        assert diagnostics == []


class TestManifestWarnings:
    """Tests for MANIFEST warning rules."""

    def test_manifest_w01_too_many_frames(self) -> None:
        """MANIFEST-W01: Warn if more than 50 frames."""
        from dot.core.rules import warn_too_many_frames
        from dot.models.frame import Frame, Hook, HookRole, Source
        from dot.models.manifest import Manifest, Metadata
        from dot.models.settings import Settings

        now = datetime.now(timezone.utc)
        frames = [
            Frame(
                name=f"frame.table_{i}",
                source=Source(relation=f"psa.table_{i}"),
                hooks=[
                    Hook(
                        name=f"_hk__entity_{i}",
                        role=HookRole.PRIMARY,
                        concept=f"entity_{i}",
                        source="SRC",
                        expr=f"id_{i}",
                    )
                ],
            )
            for i in range(51)  # 51 frames
        ]
        manifest = Manifest(
            manifest_version="1.0.0",
            schema_version="1.0.0",
            metadata=Metadata(name="Test", created_at=now, updated_at=now),
            settings=Settings(),
            frames=frames,
        )
        diagnostics = warn_too_many_frames(manifest)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "MANIFEST-W01"
        assert diagnostics[0].severity == Severity.WARN

    def test_manifest_w01_under_threshold_passes(self) -> None:
        """MANIFEST-W01: No warning if 50 or fewer frames."""
        from dot.core.rules import warn_too_many_frames
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
        diagnostics = warn_too_many_frames(manifest)
        assert diagnostics == []

    def test_manifest_w02_unknown_fields(self) -> None:
        """MANIFEST-W02: Warn on unknown fields for forward compatibility."""
        from dot.core.rules import warn_unknown_fields

        # Simulate raw data with unknown field
        raw_data = {
            "manifest_version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {"name": "Test"},
            "settings": {},
            "frames": [],
            "concepts": [],
            "unknown_field": "value",  # Unknown!
        }
        diagnostics = warn_unknown_fields(raw_data)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule_id == "MANIFEST-W02"
        assert diagnostics[0].severity == Severity.WARN

    def test_manifest_w02_no_unknown_fields_passes(self) -> None:
        """MANIFEST-W02: No warning if no unknown fields."""
        from dot.core.rules import warn_unknown_fields

        raw_data = {
            "manifest_version": "1.0.0",
            "schema_version": "1.0.0",
            "metadata": {"name": "Test"},
            "settings": {},
            "frames": [],
            "concepts": [],
        }
        diagnostics = warn_unknown_fields(raw_data)
        assert diagnostics == []
