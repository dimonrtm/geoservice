"""Contract between first-save mappings and the independently migrated schema."""

import subprocess
import sys
import textwrap

import pytest
from sqlalchemy import BigInteger, CheckConstraint, UniqueConstraint, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers

from utility_service.infrastructure.postgresql.models import work_order


def check_definitions(model):
    return {
        c.name: " ".join(str(c.sqltext).split())
        for c in model.__table__.constraints
        if isinstance(
            c,
            CheckConstraint,
        )
    }


def test_command_check_definitions():
    assert check_definitions(work_order.EditVersionCommand) == {
        "ck_ev_commands_fingerprint": "btrim(request_fingerprint) <> ''",
        "ck_ev_commands_state": "state IN ('running','succeeded','rejected')",
        "ck_ev_commands_result": (
            "(state = 'running' AND response_status IS NULL AND response_payload IS NULL "
            "AND rejection_code IS NULL AND rejection_message IS NULL "
            "AND completed_at IS NULL AND NOT retry_on_access_change) OR "
            "(state = 'succeeded' AND response_status IS NOT NULL "
            "AND response_status BETWEEN 200 AND 299 AND response_payload IS NOT NULL "
            "AND jsonb_typeof(response_payload) = 'object' AND rejection_code IS NULL "
            "AND rejection_message IS NULL AND completed_at IS NOT NULL "
            "AND NOT retry_on_access_change) OR (state = 'rejected' "
            "AND response_status IS NOT NULL AND response_status BETWEEN 400 AND 499 "
            "AND response_payload IS NULL AND rejection_code IS NOT NULL "
            "AND btrim(rejection_code) <> '' AND rejection_message IS NOT NULL "
            "AND btrim(rejection_message) <> '' AND completed_at IS NOT NULL)"
        ),
        "ck_ev_commands_access_retry": (
            "NOT retry_on_access_change OR (state = 'rejected' "
            "AND response_status IS NOT NULL AND response_status = 404 "
            "AND rejection_code IS NOT NULL AND rejection_code = 'EDIT_VERSION_NOT_FOUND')"
        ),
    }


def test_event_check_definitions_and_revision_unique():
    assert check_definitions(work_order.EditVersionChangeEvent) == {
        "ck_ev_events_type": "event_type IN ('change_set_persisted','change_set_cleared')",
        "ck_ev_events_base_revision": "base_network_revision >= 1",
        "ck_ev_events_draft_revisions": (
            "draft_revision_before >= 1 AND draft_revision_after > draft_revision_before "
            "AND draft_revision_after - draft_revision_before = 1"
        ),
        "ck_ev_events_before_geometry": (
            "NOT ST_IsEmpty(before_geometry) AND ST_IsValid(before_geometry) "
            "AND ST_IsSimple(before_geometry)"
        ),
        "ck_ev_events_after_geometry": (
            "NOT ST_IsEmpty(after_geometry) AND ST_IsValid(after_geometry) "
            "AND ST_IsSimple(after_geometry)"
        ),
        "ck_ev_events_geometry_changed": "ST_AsEWKB(before_geometry) <> ST_AsEWKB(after_geometry)",
    }
    assert {
        (c.name, tuple(c.columns.keys()))
        for c in work_order.EditVersionChangeEvent.__table__.constraints
        if isinstance(
            c,
            UniqueConstraint,
        )
    } == {("uq_ev_events_version_revision", ("edit_version_id", "draft_revision_after"))}


@pytest.mark.parametrize(
    "name",
    ["EditVersionCommand", "EditVersionChangeEvent"],
)
def test_first_save_model_is_exported(name):
    assert hasattr(
        work_order,
        name,
    )
    assert name in work_order.__all__


def test_revision_metadata_contract():
    table = work_order.EditVersion.__table__
    assert "draft_revision" in table.c
    assert isinstance(
        table.c.draft_revision.type,
        BigInteger,
    )
    assert not table.c.draft_revision.nullable
    assert str(table.c.draft_revision.server_default.arg) == "1"
    checks = {
        c.name: str(c.sqltext)
        for c in table.constraints
        if isinstance(
            c,
            CheckConstraint,
        )
    }
    assert checks["ck_edit_versions_draft_revision_positive"] == "draft_revision >= 1"


@pytest.mark.parametrize(
    "model_name,expected,nullable,defaults",
    [
        (
            "EditVersionCommand",
            {
                "command_id": "UUID",
                "edit_version_id": "UUID",
                "feature_id": "UUID",
                "actor_user_id": "UUID",
                "request_fingerprint": "TEXT",
                "state": "VARCHAR(16)",
                "retry_on_access_change": "BOOLEAN",
                "response_status": "SMALLINT",
                "response_payload": "JSONB",
                "rejection_code": "TEXT",
                "rejection_message": "TEXT",
                "created_at": "TIMESTAMP WITH TIME ZONE",
                "completed_at": "TIMESTAMP WITH TIME ZONE",
            },
            {
                "response_status",
                "response_payload",
                "rejection_code",
                "rejection_message",
                "completed_at",
            },
            {
                "retry_on_access_change": "false",
                "created_at": "now()",
            },
        ),
        (
            "EditVersionChangeEvent",
            {
                "command_id": "UUID",
                "edit_version_id": "UUID",
                "work_order_id": "UUID",
                "default_state_id": "UUID",
                "feature_id": "UUID",
                "actor_user_id": "UUID",
                "event_type": "VARCHAR(32)",
                "before_geometry": "geometry(LINESTRING,4326)",
                "after_geometry": "geometry(LINESTRING,4326)",
                "base_network_revision": "INTEGER",
                "draft_revision_before": "BIGINT",
                "draft_revision_after": "BIGINT",
                "occurred_at": "TIMESTAMP WITH TIME ZONE",
            },
            set(),
            {
                "occurred_at": "now()",
            },
        ),
    ],
)
def test_column_contract(
    model_name,
    expected,
    nullable,
    defaults,
):
    assert hasattr(
        work_order,
        model_name,
    )
    table = getattr(
        work_order,
        model_name,
    ).__table__
    dialect = postgresql.dialect()
    assert table.schema == "work_order"
    assert {c.name: str(c.type.compile(dialect=dialect)) for c in table.c} == expected
    assert {c.name for c in table.c if c.nullable} == nullable
    assert {
        c.name: (
            str(c.server_default.arg.compile(dialect=dialect))
            if hasattr(
                c.server_default.arg,
                "compile",
            )
            else str(c.server_default.arg)
        )
        for c in table.c
        if c.server_default is not None
    } == defaults
    assert all(c.default is None for c in table.c)
    assert list(table.primary_key.columns.keys()) == ["command_id"]
    configure_mappers()
    assert not inspect(
        getattr(
            work_order,
            model_name,
        )
    ).relationships


def test_command_metadata_contract():
    assert hasattr(
        work_order,
        "EditVersionCommand",
    )
    table = work_order.EditVersionCommand.__table__
    assert table.primary_key.name == "pk_edit_version_commands"
    assert table.c.response_payload.type.none_as_null is True
    assert {
        (fk.name, tuple(fk.column_keys), tuple(e.target_fullname for e in fk.elements), fk.ondelete)
        for fk in table.foreign_key_constraints
    } == {
        (
            "fk_ev_commands_edit_version",
            ("edit_version_id",),
            ("work_order.edit_versions.id",),
            "CASCADE",
        ),
        (
            "fk_ev_commands_feature",
            ("edit_version_id", "feature_id"),
            (
                "work_order.edit_version_features.edit_version_id",
                "work_order.edit_version_features.feature_id",
            ),
            "NO ACTION",
        ),
    }
    assert {(i.name, tuple(i.columns.keys()), i.unique) for i in table.indexes} == {
        ("ix_ev_commands_version_feature", ("edit_version_id", "feature_id"), False)
    }
    assert {
        c.name
        for c in table.constraints
        if isinstance(
            c,
            CheckConstraint,
        )
    } == {
        "ck_ev_commands_fingerprint",
        "ck_ev_commands_state",
        "ck_ev_commands_result",
        "ck_ev_commands_access_retry",
    }
    assert table.c.state.type.enums == ["running", "succeeded", "rejected"]
    assert not table.c.state.type.native_enum
    assert not table.c.state.type.create_constraint


def test_event_metadata_contract():
    assert hasattr(
        work_order,
        "EditVersionChangeEvent",
    )
    table = work_order.EditVersionChangeEvent.__table__
    assert table.primary_key.name == "pk_edit_version_change_events"
    assert not table.foreign_key_constraints
    assert not table.indexes
    assert {
        c.name
        for c in table.constraints
        if isinstance(
            c,
            CheckConstraint,
        )
    } == {
        "ck_ev_events_type",
        "ck_ev_events_base_revision",
        "ck_ev_events_draft_revisions",
        "ck_ev_events_before_geometry",
        "ck_ev_events_after_geometry",
        "ck_ev_events_geometry_changed",
    }
    for name in ("before_geometry", "after_geometry"):
        geometry = table.c[name].type
        assert (
            geometry.geometry_type,
            geometry.srid,
            geometry.dimension,
            geometry.spatial_index,
        ) == ("LINESTRING", 4326, 2, False)
    assert table.c.event_type.type.enums == ["change_set_persisted", "change_set_cleared"]
    assert not table.c.event_type.type.native_enum
    assert not table.c.event_type.type.create_constraint


def test_alembic_registers_first_save_models_in_fresh_process():
    script = textwrap.dedent(
        """
        from contextlib import nullcontext
        import runpy
        from alembic import context
        from alembic.config import Config
        captured = {}
        context.config = Config()
        context.is_offline_mode = lambda: True
        context.configure = lambda **kwargs: captured.update(kwargs)
        context.begin_transaction = nullcontext
        context.run_migrations = lambda: None
        runpy.run_path("utility_service/infrastructure/postgresql/alembic/env.py")
        tables = captured["target_metadata"].tables
        assert "work_order.edit_version_commands" in tables
        assert "work_order.edit_version_change_events" in tables
        assert "draft_revision" in tables["work_order.edit_versions"].c
    """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
