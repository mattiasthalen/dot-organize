"""Unit tests for registry functions.

T017: Tests for key set derivation, concept registry, hook registry
"""

from datetime import datetime, timezone


class TestKeySetDerivation:
    """Tests for key set derivation functions."""

    def test_build_key_set_simple(self) -> None:
        """Key set for simple hook: CONCEPT@SOURCE."""
        from dot.core.registry import _build_key_set
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        key_set = _build_key_set(hook)
        assert key_set == "CUSTOMER@CRM"

    def test_build_key_set_with_qualifier(self) -> None:
        """Key set with qualifier: CONCEPT~QUALIFIER@SOURCE."""
        from dot.core.registry import _build_key_set
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__employee__manager",
            role=HookRole.FOREIGN,
            concept="employee",
            qualifier="manager",
            source="HR",
            expr="manager_id",
        )
        key_set = _build_key_set(hook)
        assert key_set == "EMPLOYEE~MANAGER@HR"

    def test_build_key_set_with_tenant(self) -> None:
        """Key set with tenant: CONCEPT@SOURCE~TENANT."""
        from dot.core.registry import _build_key_set
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__order",
            role=HookRole.PRIMARY,
            concept="order",
            source="SAP",
            tenant="AU",
            expr="order_id",
        )
        key_set = _build_key_set(hook)
        assert key_set == "ORDER@SAP~AU"

    def test_build_key_set_full(self) -> None:
        """Key set with qualifier and tenant: CONCEPT~QUALIFIER@SOURCE~TENANT."""
        from dot.core.registry import _build_key_set
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__order__billing",
            role=HookRole.FOREIGN,
            concept="order",
            qualifier="billing",
            source="SAP",
            tenant="EU",
            expr="billing_order_id",
        )
        key_set = _build_key_set(hook)
        assert key_set == "ORDER~BILLING@SAP~EU"

    def test_derive_key_sets_from_manifest(self) -> None:
        """Derive all unique key sets from manifest."""
        from dot.core.registry import derive_key_sets
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
                ),
            ],
        )
        key_sets = derive_key_sets(manifest)
        assert key_sets == {"CUSTOMER@CRM", "ORDER@ERP"}

    def test_derive_key_sets_with_aliases(self) -> None:
        """Derive key sets with key aliases (same concept, different qualifiers)."""
        from dot.core.registry import derive_key_sets
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
                    name="frame.order",
                    source=Source(relation="psa.order"),
                    hooks=[
                        Hook(
                            name="_hk__order__number",
                            role=HookRole.PRIMARY,
                            concept="order",
                            qualifier="number",
                            source="ERP",
                            expr="order_number",
                        ),
                        Hook(
                            name="_hk__order__id",
                            role=HookRole.FOREIGN,
                            concept="order",
                            qualifier="id",
                            source="ERP",
                            expr="order_id",
                        ),
                    ],
                ),
            ],
        )
        key_sets = derive_key_sets(manifest)
        assert key_sets == {"ORDER~NUMBER@ERP", "ORDER~ID@ERP"}


class TestConceptRegistry:
    """Tests for concept registry derivation."""

    def test_derive_concepts_from_hooks(self) -> None:
        """Derive unique concept names from all hooks."""
        from dot.core.registry import derive_concepts
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
                        Hook(
                            name="_hk__employee__manager",
                            role=HookRole.FOREIGN,
                            concept="employee",
                            qualifier="manager",
                            source="HR",
                            expr="manager_id",
                        ),
                    ],
                ),
            ],
        )
        concepts = derive_concepts(manifest)
        assert concepts == {"order", "customer", "employee"}


class TestHookRegistry:
    """Tests for hook registry derivation."""

    def test_derive_hook_registry(self) -> None:
        """Derive hook registry indexing hooks by name."""
        from dot.core.registry import derive_hook_registry
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
                ),
            ],
        )
        registry = derive_hook_registry(manifest)

        # _hk__customer appears in both frames
        assert "_hk__customer" in registry
        assert len(registry["_hk__customer"]) == 2
        frame_names = [frame_name for frame_name, _ in registry["_hk__customer"]]
        assert "frame.customer" in frame_names
        assert "frame.order" in frame_names

        # _hk__order appears in one frame
        assert "_hk__order" in registry
        assert len(registry["_hk__order"]) == 1
        assert registry["_hk__order"][0][0] == "frame.order"
