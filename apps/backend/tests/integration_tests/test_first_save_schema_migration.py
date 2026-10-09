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
    BASELINE,
    MOVED,
    finish_command,
    insert_event,
    insert_running_command,
    persist_sql_change,
    run_committed_scenario,
    run_scenario,
    seed_context,
    snapshot_context,
)
from tests.integration_tests.network_db_support import require_db_tests
from tests.integration_tests.first_save_catalog_support import assert_first_save_guards
from uuid import uuid4


PREVIOUS_REVISION = "f8a7b6c5d4e3"
APP_ROOT = Path(__file__).resolve().parents[2]


def test_first_save_populated_upgrade_downgrade_upgrade():
    require_db_tests()
    config = Config(str(APP_ROOT / "alembic.ini"))
    state = {}

    async def seed(engine):
        async with engine.begin() as connection:
            state["ids"] = await seed_context(connection, include_geometry_policy=False)
            state["original"] = await snapshot_context(
                connection,
                state["ids"]["edit_version_id"],
            )

    async def first_upgrade(engine):
        async with engine.begin() as connection:
            ids = state["ids"]
            assert (
                await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
                == state["original"]
            )
            assert (
                await connection.scalar(
                    text(
                        """
                         SELECT draft_revision
                         FROM work_order.edit_versions
                         WHERE id=:id
                         """
                    ),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                == 1
            )
            for table in ("edit_version_commands", "edit_version_change_events"):
                assert (
                    await connection.scalar(text(f"SELECT count(*) FROM work_order.{table}")) == 0
                )
            await persist_sql_change(
                connection,
                ids,
                uuid4(),
            )
            state["changed"] = await snapshot_context(
                connection,
                ids["edit_version_id"],
            )

    async def downgraded(engine):
        async with engine.connect() as connection:
            assert (
                await snapshot_context(
                    connection,
                    state["ids"]["edit_version_id"],
                )
                == state["changed"]
            )
            for table in ("edit_version_commands", "edit_version_change_events"):
                assert (
                    await connection.scalar(
                        text("SELECT to_regclass(:name)"),
                        {
                            "name": f"work_order.{table}",
                        },
                    )
                    is None
                )
            assert (
                await connection.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM information_schema.columns
                        WHERE table_schema='work_order'
                            AND table_name='edit_versions'
                            AND column_name='draft_revision'
                        """
                    )
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text(
                        """
                        SELECT count(*)
                        FROM pg_constraint
                        WHERE conrelid='work_order.edit_versions'::regclass
                            AND conname='ck_edit_versions_draft_revision_positive'
                        """
                    )
                )
                == 0
            )
            await assert_first_save_guards(
                connection,
                present=False,
            )

    async def second_upgrade(engine):
        ids = state["ids"]
        async with engine.begin() as connection:
            assert (
                await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
                == state["changed"]
            )
            assert (
                await connection.scalar(
                    text(
                        """
                         SELECT draft_revision
                         FROM work_order.edit_versions
                         WHERE id=:id
                         """
                    ),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                == 1
            )
            for table, count in (("edit_version_commands", 2), ("edit_version_change_events", 2)):
                assert (
                    await connection.scalar(text(f"SELECT count(*) FROM work_order.{table}")) == 0
                )
                assert (
                    await connection.scalar(
                        text(
                            """
                            SELECT count(*)
                            FROM pg_indexes
                            WHERE schemaname='work_order'
                                AND tablename=:table
                            """
                        ),
                        {
                            "table": table,
                        },
                    )
                    == count
                )
            await assert_first_save_guards(connection)

        with pytest.raises(DBAPIError) as error:
            async with engine.begin() as connection:
                await insert_running_command(
                    connection,
                    ids,
                    uuid4(),
                )
        assert error.value.orig.__cause__.constraint_name == "ck_ev_commands_terminal"

        with pytest.raises(DBAPIError) as error:
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        """
                        INSERT INTO work_order.edit_version_commands (
                            command_id,
                            edit_version_id,
                            feature_id,
                            actor_user_id,
                            request_fingerprint,
                            state
                        )
                        VALUES (
                            :command_id,
                            :edit_version_id,
                            :feature_id,
                            :actor_user_id,
                            'lifecycle',
                            'succeeded'
                        )
                        """
                    ),
                    {
                        **ids,
                        "command_id": uuid4(),
                    },
                )
        assert error.value.orig.__cause__.constraint_name == "ck_ev_commands_transition"

        command_id = uuid4()
        async with engine.begin() as connection:
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_versions
                    SET draft_revision=2
                    WHERE id=:edit_version_id
                    """
                ),
                ids,
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET
                        geometry=ST_GeomFromText(:baseline,4326),
                        operation='unchanged'
                    WHERE edit_version_id=:edit_version_id
                        AND feature_id=:feature_id
                    """
                ),
                {
                    **ids,
                    "baseline": BASELINE,
                },
            )
            await finish_command(
                connection,
                command_id,
                state="succeeded",
            )
            # A valid command and unoccupied revision ensure this tests context, not uniqueness.
            with pytest.raises(DBAPIError) as error:
                async with connection.begin_nested():
                    await insert_event(
                        connection,
                        ids,
                        command_id,
                        before_geometry=MOVED,
                        after_geometry=BASELINE,
                        event_type="change_set_cleared",
                        actor_user_id=uuid4(),
                    )
            assert error.value.orig.__cause__.constraint_name == "ck_ev_events_context"
            await insert_event(
                connection,
                ids,
                command_id,
                before_geometry=MOVED,
                after_geometry=BASELINE,
                event_type="change_set_cleared",
            )

        async with engine.connect() as connection:
            original = await connection.scalar(
                text(
                    """
                    SELECT to_jsonb(e)
                    FROM work_order.edit_version_change_events e
                    WHERE command_id=:id
                    """
                ),
                {
                    "id": command_id,
                },
            )
        for sql in (
            """
            UPDATE work_order.edit_version_change_events
            SET actor_user_id=actor_user_id
            WHERE command_id=:id
            """,
            """
            DELETE
            FROM work_order.edit_version_change_events
            WHERE command_id=:id
            """,
            "TRUNCATE work_order.edit_version_change_events",
        ):
            with pytest.raises(DBAPIError) as error:
                async with engine.begin() as connection:
                    await connection.execute(
                        text(sql),
                        {
                            "id": command_id,
                        },
                    )
            assert error.value.orig.sqlstate == "23514"
            assert error.value.orig.__cause__.constraint_name == "ck_ev_events_append_only"
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text(
                        """
                        SELECT to_jsonb(e)
                        FROM work_order.edit_version_change_events e
                        WHERE command_id=:id
                        """
                    ),
                    {
                        "id": command_id,
                    },
                )
                == original
            )

    try:
        command.downgrade(
            config,
            PREVIOUS_REVISION,
        )
        run_committed_scenario(seed)
        command.upgrade(
            config,
            "b7d2e9f4a6c8",
        )
        run_committed_scenario(first_upgrade)
        command.downgrade(
            config,
            PREVIOUS_REVISION,
        )
        run_committed_scenario(downgraded)
        command.upgrade(
            config,
            "b7d2e9f4a6c8",
        )
        run_committed_scenario(second_upgrade)
    finally:
        command.upgrade(
            config,
            "head",
        )


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
                            SELECT indexdef
                            FROM pg_indexes
                            WHERE schemaname='work_order'
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
                        SELECT count(*)
                        FROM pg_constraint
                        WHERE conrelid='work_order.edit_version_change_events'::regclass
                            AND contype='f'
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
                ids = await seed_context(connection, include_geometry_policy=False)
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
            "b7d2e9f4a6c8",
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
                    text(
                        """
                         SELECT draft_revision
                         FROM work_order.edit_versions
                         WHERE id=:id
                         """
                    ),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text(
                        """
                         SELECT count(*)
                         FROM work_order.edit_version_commands
                         """
                    )
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text(
                        """
                         SELECT count(*)
                         FROM work_order.edit_version_change_events
                         """
                    )
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
                text(
                    """
                     SELECT draft_revision
                     FROM work_order.edit_versions
                     WHERE id=:id
                     """
                ),
                {
                    "id": ids["edit_version_id"],
                },
            )
            == 1
        )
        await connection.execute(
            text(
                """
                 UPDATE work_order.edit_versions
                 SET last_opened_at=now()
                 WHERE id=:id
                 """
            ),
            {
                "id": ids["edit_version_id"],
            },
        )
        assert (
            await connection.scalar(
                text(
                    """
                     SELECT draft_revision
                     FROM work_order.edit_versions
                     WHERE id=:id
                     """
                ),
                {
                    "id": ids["edit_version_id"],
                },
            )
            == 1
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await connection.execute(
                    text(
                        """
                         UPDATE work_order.edit_versions
                         SET draft_revision=:value
                         WHERE id=:id
                         """
                    ),
                    {
                        "id": ids["edit_version_id"],
                        "value": value,
                    },
                )
        assert error.value.orig.sqlstate == sqlstate

    run_scenario(scenario)
