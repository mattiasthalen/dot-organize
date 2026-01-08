"""Unit tests for Pydantic models.

T015: Tests for all models (Settings, Diagnostic, Concept, Hook, Frame, Manifest)
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError


class TestSeverityEnum:
    """Tests for Severity enum."""

    def test_severity_error_value(self) -> None:
        """Severity.ERROR has value 'ERROR'."""
        from dot.models.diagnostic import Severity

        assert Severity.ERROR.value == "ERROR"

    def test_severity_warn_value(self) -> None:
        """Severity.WARN has value 'WARN'."""
        from dot.models.diagnostic import Severity

        assert Severity.WARN.value == "WARN"


class TestDiagnosticModel:
    """Tests for Diagnostic model."""

    def test_diagnostic_creation(self) -> None:
        """Diagnostic can be created with all required fields."""
        from dot.models.diagnostic import Diagnostic, Severity

        diagnostic = Diagnostic(
            rule_id="HOOK-001",
            severity=Severity.ERROR,
            message="Hook is missing required field",
            path="frames[0].hooks[0]",
            fix="Add the required 'name' field",
        )
        assert diagnostic.rule_id == "HOOK-001"
        assert diagnostic.severity == Severity.ERROR
        assert diagnostic.message == "Hook is missing required field"
        assert diagnostic.path == "frames[0].hooks[0]"
        assert diagnostic.fix == "Add the required 'name' field"

    def test_diagnostic_is_frozen(self) -> None:
        """Diagnostic is immutable (frozen)."""
        from dot.models.diagnostic import Diagnostic, Severity

        diagnostic = Diagnostic(
            rule_id="HOOK-001",
            severity=Severity.ERROR,
            message="Test",
            path="test",
            fix="Fix it",
        )
        with pytest.raises(ValidationError):
            diagnostic.rule_id = "HOOK-002"  # type: ignore[misc]


class TestSettingsModel:
    """Tests for Settings model."""

    def test_settings_defaults(self) -> None:
        """Settings use correct defaults."""
        from dot.models.settings import Settings

        settings = Settings()
        assert settings.hook_prefix == "_hk__"
        assert settings.weak_hook_prefix == "_wk__"
        assert settings.delimiter == "|"

    def test_settings_custom_values(self) -> None:
        """Settings accept custom values."""
        from dot.models.settings import Settings

        settings = Settings(
            hook_prefix="HK_",
            weak_hook_prefix="WK_",
            delimiter="~",
        )
        assert settings.hook_prefix == "HK_"
        assert settings.weak_hook_prefix == "WK_"
        assert settings.delimiter == "~"

    def test_settings_is_frozen(self) -> None:
        """Settings is immutable (frozen)."""
        from dot.models.settings import Settings

        settings = Settings()
        with pytest.raises(ValidationError):
            settings.hook_prefix = "changed"  # type: ignore[misc]


class TestConceptModel:
    """Tests for Concept model."""

    def test_concept_required_fields(self) -> None:
        """Concept requires name and description."""
        from dot.models.concept import Concept

        concept = Concept(
            name="customer",
            description="A person or organization that purchases goods or services.",
        )
        assert concept.name == "customer"
        assert concept.description == "A person or organization that purchases goods or services."

    def test_concept_defaults(self) -> None:
        """Concept has correct defaults for optional fields."""
        from dot.models.concept import Concept

        concept = Concept(
            name="customer",
            description="Test description",
        )
        assert concept.examples == ()
        assert concept.frames == ()
        assert concept.is_weak is False

    def test_concept_with_examples(self) -> None:
        """Concept accepts examples tuple."""
        from dot.models.concept import Concept

        concept = Concept(
            name="customer",
            description="Test description",
            examples=("John Doe", "ACME Corp"),
        )
        assert concept.examples == ("John Doe", "ACME Corp")

    def test_concept_is_weak(self) -> None:
        """Concept is_weak can be set to True."""
        from dot.models.concept import Concept

        concept = Concept(
            name="date",
            description="A calendar date reference",
            is_weak=True,
        )
        assert concept.is_weak is True

    def test_concept_is_frozen(self) -> None:
        """Concept is immutable (frozen)."""
        from dot.models.concept import Concept

        concept = Concept(name="customer", description="Test")
        with pytest.raises(ValidationError):
            concept.name = "changed"  # type: ignore[misc]


class TestHookRoleEnum:
    """Tests for HookRole enum."""

    def test_hook_role_primary(self) -> None:
        """HookRole.PRIMARY has value 'primary'."""
        from dot.models.frame import HookRole

        assert HookRole.PRIMARY.value == "primary"

    def test_hook_role_foreign(self) -> None:
        """HookRole.FOREIGN has value 'foreign'."""
        from dot.models.frame import HookRole

        assert HookRole.FOREIGN.value == "foreign"


class TestHookModel:
    """Tests for Hook model."""

    def test_hook_required_fields(self) -> None:
        """Hook requires name, role, concept, source, expr."""
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        assert hook.name == "_hk__customer"
        assert hook.role == HookRole.PRIMARY
        assert hook.concept == "customer"
        assert hook.source == "CRM"
        assert hook.expr == "customer_id"

    def test_hook_missing_required_field(self) -> None:
        """Hook raises error when required field is missing."""
        from dot.models.frame import Hook, HookRole

        with pytest.raises(ValidationError):
            Hook(
                name="_hk__customer",
                role=HookRole.PRIMARY,
                # Missing: concept, source, expr
            )

    def test_hook_optional_fields_default(self) -> None:
        """Hook optional fields have correct defaults."""
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        assert hook.qualifier is None
        assert hook.tenant is None

    def test_hook_with_qualifier(self) -> None:
        """Hook accepts qualifier."""
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__employee__manager",
            role=HookRole.FOREIGN,
            concept="employee",
            qualifier="manager",
            source="HR",
            expr="manager_id",
        )
        assert hook.qualifier == "manager"

    def test_hook_with_tenant(self) -> None:
        """Hook accepts tenant."""
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__order",
            role=HookRole.PRIMARY,
            concept="order",
            source="SAP",
            tenant="AU",
            expr="order_id",
        )
        assert hook.tenant == "AU"

    def test_hook_is_frozen(self) -> None:
        """Hook is immutable (frozen)."""
        from dot.models.frame import Hook, HookRole

        hook = Hook(
            name="_hk__customer",
            role=HookRole.PRIMARY,
            concept="customer",
            source="CRM",
            expr="customer_id",
        )
        with pytest.raises(ValidationError):
            hook.name = "changed"  # type: ignore[misc]


class TestSourceModel:
    """Tests for Source model."""

    def test_source_with_relation(self) -> None:
        """Source with relation only is valid."""
        from dot.models.frame import Source

        source = Source(relation="psa.customer")
        assert source.relation == "psa.customer"
        assert source.path is None

    def test_source_with_path(self) -> None:
        """Source with path only is valid."""
        from dot.models.frame import Source

        source = Source(path="//server/qvd/customer.qvd")
        assert source.path == "//server/qvd/customer.qvd"
        assert source.relation is None

    def test_source_both_relation_and_path_fails(self) -> None:
        """Source with both relation and path is invalid."""
        from dot.models.frame import Source

        with pytest.raises(ValidationError):
            Source(relation="psa.customer", path="//server/qvd/customer.qvd")

    def test_source_neither_relation_nor_path_fails(self) -> None:
        """Source with neither relation nor path is invalid."""
        from dot.models.frame import Source

        with pytest.raises(ValidationError):
            Source()

    def test_source_is_frozen(self) -> None:
        """Source is immutable (frozen)."""
        from dot.models.frame import Source

        source = Source(relation="psa.customer")
        with pytest.raises(ValidationError):
            source.relation = "changed"  # type: ignore[misc]


class TestFrameModel:
    """Tests for Frame model."""

    def test_frame_required_fields(self) -> None:
        """Frame requires name, source, hooks."""
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
        assert frame.name == "frame.customer"
        assert frame.source.relation == "psa.customer"
        assert len(frame.hooks) == 1

    def test_frame_optional_description(self) -> None:
        """Frame description is optional with default None."""
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
        assert frame.description is None

    def test_frame_with_description(self) -> None:
        """Frame accepts description."""
        from dot.models.frame import Frame, Hook, HookRole, Source

        frame = Frame(
            name="frame.customer",
            source=Source(relation="psa.customer"),
            description="Customer master data frame",
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
        assert frame.description == "Customer master data frame"

    def test_frame_is_frozen(self) -> None:
        """Frame is immutable (frozen)."""
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
        with pytest.raises(ValidationError):
            frame.name = "changed"  # type: ignore[misc]


class TestMetadataModel:
    """Tests for Metadata model."""

    def test_metadata_required_fields(self) -> None:
        """Metadata requires name, created_at, updated_at."""
        from dot.models.manifest import Metadata

        now = datetime.now(timezone.utc)
        metadata = Metadata(
            name="Test Manifest",
            created_at=now,
            updated_at=now,
        )
        assert metadata.name == "Test Manifest"
        assert metadata.created_at == now
        assert metadata.updated_at == now

    def test_metadata_optional_description(self) -> None:
        """Metadata description is optional with default None."""
        from dot.models.manifest import Metadata

        now = datetime.now(timezone.utc)
        metadata = Metadata(
            name="Test Manifest",
            created_at=now,
            updated_at=now,
        )
        assert metadata.description is None

    def test_metadata_with_description(self) -> None:
        """Metadata accepts description."""
        from dot.models.manifest import Metadata

        now = datetime.now(timezone.utc)
        metadata = Metadata(
            name="Test Manifest",
            description="A test manifest for validation",
            created_at=now,
            updated_at=now,
        )
        assert metadata.description == "A test manifest for validation"

    def test_metadata_is_frozen(self) -> None:
        """Metadata is immutable (frozen)."""
        from dot.models.manifest import Metadata

        now = datetime.now(timezone.utc)
        metadata = Metadata(
            name="Test Manifest",
            created_at=now,
            updated_at=now,
        )
        with pytest.raises(ValidationError):
            metadata.name = "changed"  # type: ignore[misc]


class TestManifestModel:
    """Tests for Manifest model."""

    def test_manifest_required_fields(self) -> None:
        """Manifest requires manifest_version, schema_version, metadata, settings, frames."""
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
        assert manifest.manifest_version == "1.0.0"
        assert manifest.schema_version == "1.0.0"
        assert manifest.metadata is not None
        assert manifest.metadata.name == "Test"
        assert manifest.settings.hook_prefix == "_hk__"
        assert len(manifest.frames) == 1

    def test_manifest_concepts_default(self) -> None:
        """Manifest concepts defaults to empty list."""
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
        assert manifest.concepts == []

    def test_manifest_with_concepts(self) -> None:
        """Manifest accepts concepts list."""
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
                Concept(
                    name="customer",
                    description="A person or organization that purchases goods",
                )
            ],
        )
        assert len(manifest.concepts) == 1
        assert manifest.concepts[0].name == "customer"

    def test_manifest_is_frozen(self) -> None:
        """Manifest is immutable (frozen)."""
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
        with pytest.raises(ValidationError):
            manifest.manifest_version = "2.0.0"  # type: ignore[misc]
