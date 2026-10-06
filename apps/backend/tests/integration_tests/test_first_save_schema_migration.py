import asyncio
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.integration_tests.first_save_schema_support import (
    run_scenario,
    seed_context,
    snapshot_context,
)
from tests.integration_tests.network_db_support import require_db_tests


PREVIOUS_REVISION = "f8a7b6c5d4e3"
APP_ROOT = Path(__file__).resolve().parents[2]


def test_fresh_upgrade_creates_first_save_objects() -> None:
    require_db_tests()
    config = Config(str(APP_ROOT / "alembic.ini"))
    try:
        command.downgrade(
            config,
            "base",
        )
        command.upgrade(
            config,
            "head",
        )

        async def scenario(connection):
            assert (
                await connection.scalar(
                    text("SELECT to_regclass('work_order.edit_version_commands')::text")
                )
                == "work_order.edit_version_commands"
            )
            row = (
                (
                    await connection.execute(
                        text(
                            """
                SELECT
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema='work_order'
                    AND table_name='edit_versions'
                    AND column_name='draft_revision'
            """
                        )
                    )
                )
                .mappings()
                .one()
            )
            assert row["data_type"] == "bigint"
            assert row["is_nullable"] == "NO"
            # PostgreSQL may render this as '1'::bigint; the inserted value is
            # asserted separately, rather than binding to catalog SQL formatting.
            assert row["column_default"] is not None
            assert (
                await connection.scalar(
                    text("SELECT to_regclass('work_order.edit_version_change_events')::text")
                )
                == "work_order.edit_version_change_events"
            )
            indexes = (
                (
                    await connection.execute(
                        text(
                            """
                SELECT indexdef FROM pg_indexes WHERE schemaname='work_order'
                AND tablename='edit_version_change_events'
            """
                        )
                    )
                )
                .scalars()
                .all()
            )
            assert len(indexes) == 2
            assert all("USING btree" in definition for definition in indexes)
            assert (
                await connection.scalar(
                    text(
                        """
                SELECT count(*) FROM pg_constraint
                WHERE conrelid='work_order.edit_version_change_events'::regclass AND contype='f'
            """
                    )
                )
                == 0
            )

        run_scenario(scenario)
    finally:
        command.upgrade(
            config,
            "head",
        )


def test_populated_upgrade_preserves_snapshot() -> None:
    require_db_tests()
    config = Config(str(APP_ROOT / "alembic.ini"))

    async def before():
        engine = create_async_engine(os.environ["DATABASE_URL"])
        try:
            async with engine.begin() as connection:
                ids = await seed_context(connection)
                return ids, await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
        finally:
            await engine.dispose()

    try:
        command.downgrade(
            config,
            PREVIOUS_REVISION,
        )
        ids, original = asyncio.run(before())
        command.upgrade(
            config,
            "head",
        )

        async def after(connection):
            assert (
                await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
                == original
            )
            assert (
                await connection.scalar(
                    text("SELECT draft_revision FROM work_order.edit_versions WHERE id=:id"),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM work_order.edit_version_commands")
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM work_order.edit_version_change_events")
                )
                == 0
            )

        run_scenario(after)
    finally:
        command.upgrade(
            config,
            "head",
        )


@pytest.mark.parametrize(
    "value,sqlstate",
    [(None, "23502"), (0, "23514"), (-1, "23514")],
)
def test_draft_revision_default_and_positive_check(
    value,
    sqlstate,
) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        assert (
            await connection.scalar(
                text("SELECT draft_revision FROM work_order.edit_versions WHERE id=:id"),
                {
                    "id": ids["edit_version_id"],
                },
            )
            == 1
        )
        await connection.execute(
            text("UPDATE work_order.edit_versions SET last_opened_at=now() WHERE id=:id"),
            {
                "id": ids["edit_version_id"],
            },
        )
        assert (
            await connection.scalar(
                text("SELECT draft_revision FROM work_order.edit_versions WHERE id=:id"),
                {
                    "id": ids["edit_version_id"],
                },
            )
            == 1
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await connection.execute(
                    text("UPDATE work_order.edit_versions SET draft_revision=:value WHERE id=:id"),
                    {
                        "id": ids["edit_version_id"],
                        "value": value,
                    },
                )
        assert error.value.orig.sqlstate == sqlstate

    run_scenario(scenario)
