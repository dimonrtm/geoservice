"""Policy persistence and migration checks against disposable PostgreSQL."""

import importlib
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import CheckConstraint, Column, MetaData, Table, text
from sqlalchemy.schema import CreateTable, DropTable
from sqlalchemy.exc import DBAPIError

from tests.integration_tests.first_save_schema_support import (
    run_scenario,
    run_committed_scenario,
    seed_context,
    snapshot_context,
    persist_sql_change,
)
from tests.integration_tests.network_db_support import require_db_tests
from tests.integration_tests.test_first_save_model_parity import columns, checks
from utility_service.infrastructure.postgresql.models.work_order import EditVersion
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy


REVISION = "c8e3f0a5b7d9"
PREVIOUS = "b7d2e9f4a6c8"
FIELDS = ("geometry_xy_resolution", "geometry_rounding_mode", "geometry_policy_version")


def test_policy_columns_are_required_without_defaults():
    for name in FIELDS:
        column = EditVersion.__table__.c[name]
        assert not column.nullable
        assert column.default is None
        assert column.server_default is None
    assert EditVersion.__table__.c.geometry_xy_resolution.type.scale is None


@pytest.mark.parametrize(
    "grid",
    [
        "0.0000001",
        "0.0000002500",
        "360",
        "NaN",
        "Infinity",
        "-Infinity",
        "0",
        "-1",
        "361",
        "1e-8",
        "0.0000001001",
    ],
)
def test_migration_validation_matches_runtime_without_jwt(
    monkeypatch,
    grid,
):
    monkeypatch.delenv(
        "JWT_SECRET",
        raising=False,
    )
    monkeypatch.setenv(
        "UTILITY_GEOMETRY_XY_RESOLUTION",
        grid,
    )
    module = importlib.import_module(
        "utility_service.infrastructure.postgresql.alembic.versions.c8e3f0a5b7d9_edit_version_geometry_policy"
    )
    try:
        expected = GeometryPolicy(Decimal(grid))
    except ValueError:
        with pytest.raises(ValueError):
            module.configured_policy()
    else:
        assert module.configured_policy() == (expected.xy_resolution, expected.rounding_mode, 1)


def test_policy_model_matches_postgres():
    async def scenario(connection):
        table = EditVersion.__table__
        probe = Table(
            "geometry_policy_probe",
            MetaData(),
            *(
                Column(
                    c.name,
                    c.type.copy(),
                    nullable=c.nullable,
                )
                for c in table.c
                if c.name in FIELDS
            ),
            *(
                CheckConstraint(
                    str(c.sqltext),
                    name=c.name,
                )
                for c in table.constraints
                if isinstance(
                    c,
                    CheckConstraint,
                )
                and c.name.startswith("ck_edit_versions_geometry_")
            ),
            prefixes=["TEMPORARY"],
        )
        await connection.execute(CreateTable(probe))
        try:
            assert [
                r
                for r in await columns(
                    connection,
                    table.fullname,
                )
                if r[0] in FIELDS
            ] == await columns(
                connection,
                probe.name,
            )
            assert {
                k: v
                for k, v in (
                    await checks(
                        connection,
                        table.fullname,
                    )
                ).items()
                if k.startswith("ck_edit_versions_geometry_")
            } == await checks(
                connection,
                probe.name,
            )
        finally:
            await connection.execute(DropTable(probe))

    run_scenario(scenario)


@pytest.mark.parametrize(
    "field,value",
    [(FIELDS[0], "0.00000025"), (FIELDS[1], "other"), (FIELDS[2], "2")],
)
def test_policy_update_is_immutable(
    field,
    value,
):
    async def scenario(connection):
        ids = await seed_context(connection)
        async with connection.begin_nested() as savepoint:
            with pytest.raises(DBAPIError) as error:
                await connection.execute(
                    text(f"UPDATE work_order.edit_versions SET {field}=:value WHERE id=:id"),
                    {
                        "value": (
                            Decimal(value)
                            if field == FIELDS[0]
                            else int(value) if field == FIELDS[2] else value
                        ),
                        "id": ids["edit_version_id"],
                    },
                )
            original = error.value.orig.__cause__
            assert original.constraint_name == "ck_edit_versions_geometry_policy_immutable"
            assert original.sqlstate == "23514"
            await savepoint.rollback()
        await connection.execute(
            text(
                "UPDATE work_order.edit_versions SET draft_revision=draft_revision+1, last_opened_at=now() WHERE id=:id"
            ),
            {
                "id": ids["edit_version_id"],
            },
        )

    run_scenario(scenario)


@pytest.mark.parametrize(
    "grid,mode,version,valid",
    [
        ("0.0000002500", "ROUND_HALF_AWAY_FROM_ZERO", 1, True),
        *[
            (grid, "ROUND_HALF_AWAY_FROM_ZERO", 1, False)
            for grid in ("NaN", "Infinity", "-Infinity", "0", "361", "1e-8", "0.0000001001")
        ],
        ("0.0000001", "other", 1, False),
        ("0.0000001", "ROUND_HALF_AWAY_FROM_ZERO", 2, False),
    ],
)
def test_policy_insert_constraints(
    grid,
    mode,
    version,
    valid,
):
    async def scenario(connection):
        ids = await seed_context(connection)
        for table in ("edit_version_associations", "edit_version_features", "edit_versions"):
            key = "id" if table == "edit_versions" else "edit_version_id"
            await connection.execute(
                text(f"DELETE FROM work_order.{table} WHERE {key}=:id"),
                {
                    "id": ids["edit_version_id"],
                },
            )
        sql = text(
            """
            INSERT INTO work_order.edit_versions (
                id,
                work_order_id,
                default_state_id,
                owner_user_id,
                geometry_xy_resolution,
                geometry_rounding_mode,
                geometry_policy_version
            )
            VALUES (
                :edit_version_id,
                :work_order_id,
                :default_state_id,
                :actor_user_id,
                CAST(:grid AS numeric),
                :mode,
                :version
            )
            """
        )
        params = {
            **ids,
            "grid": grid,
            "mode": mode,
            "version": version,
        }
        if valid:
            await connection.execute(
                sql,
                params,
            )
        else:
            async with connection.begin_nested() as savepoint:
                with pytest.raises(DBAPIError) as error:
                    await connection.execute(
                        sql,
                        params,
                    )
                assert error.value.orig.__cause__.constraint_name in {
                    "ck_edit_versions_geometry_grid",
                    "ck_edit_versions_geometry_rounding",
                    "ck_edit_versions_geometry_policy_version",
                }
                await savepoint.rollback()

    run_scenario(scenario)


def test_populated_policy_upgrade_and_invalid_config_are_atomic(monkeypatch):
    require_db_tests()
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    state = {}

    async def seed(engine):
        async with engine.begin() as connection:
            state["ids"] = await seed_context(
                connection,
                include_geometry_policy=False,
            )
            await persist_sql_change(
                connection,
                state["ids"],
                uuid4(),
            )
            state["snapshot"] = await snapshot_context(
                connection,
                state["ids"]["edit_version_id"],
            )
            state["history"] = await history(connection)

    async def history(connection):
        result = {}
        for table in ("edit_version_commands", "edit_version_change_events"):
            result[table] = await connection.scalar(
                text(
                    f"SELECT jsonb_agg(to_jsonb(t)) FROM work_order.{table} t WHERE edit_version_id=:id"
                ),
                {
                    "id": state["ids"]["edit_version_id"],
                },
            )
        result["revision"] = await connection.scalar(
            text("SELECT draft_revision FROM work_order.edit_versions WHERE id=:id"),
            {
                "id": state["ids"]["edit_version_id"],
            },
        )
        return result

    async def assert_previous(engine):
        async with engine.connect() as connection:
            assert (
                await connection.scalar(text("SELECT version_num FROM alembic_version")) == PREVIOUS
            )
            assert (
                await connection.scalar(
                    text(
                        "SELECT count(*) FROM information_schema.columns WHERE table_schema='work_order' AND table_name='edit_versions' AND column_name='geometry_xy_resolution'"
                    )
                )
                == 0
            )

    async def verify(engine):
        async with engine.connect() as connection:
            assert await connection.scalar(
                text("SELECT geometry_xy_resolution FROM work_order.edit_versions WHERE id=:id"),
                {
                    "id": state["ids"]["edit_version_id"],
                },
            ) == Decimal("0.00000025")
            snapshot = await snapshot_context(
                connection,
                state["ids"]["edit_version_id"],
            )
            for name in FIELDS:
                snapshot["version"].pop(name)
            assert snapshot == state["snapshot"]
            assert await history(connection) == state["history"]

    try:
        command.downgrade(
            config,
            PREVIOUS,
        )
        run_committed_scenario(seed)
        monkeypatch.setenv(
            "UTILITY_GEOMETRY_XY_RESOLUTION",
            "0.0000001001",
        )
        with pytest.raises(ValueError):
            command.upgrade(
                config,
                REVISION,
            )
        run_committed_scenario(assert_previous)
        monkeypatch.setenv(
            "UTILITY_GEOMETRY_XY_RESOLUTION",
            "0.00000025",
        )
        command.upgrade(
            config,
            REVISION,
        )
        run_committed_scenario(verify)
        command.upgrade(
            config,
            REVISION,
        )
        run_committed_scenario(verify)
        command.downgrade(
            config,
            PREVIOUS,
        )
        command.upgrade(
            config,
            REVISION,
        )
        run_committed_scenario(verify)
    finally:
        monkeypatch.setenv(
            "UTILITY_GEOMETRY_XY_RESOLUTION",
            "0.0000001",
        )
        command.upgrade(
            config,
            "head",
        )
