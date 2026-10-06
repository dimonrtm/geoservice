from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.integration_tests.first_save_schema_support import (
    BASELINE,
    MOVED,
    finish_command,
    insert_event,
    insert_running_command,
    persist_sql_change,
    run_scenario,
    seed_context,
    run_committed_scenario,
    snapshot_context,
)


def test_event_insert_matches_successful_command() -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await persist_sql_change(
            connection,
            ids,
            command_id,
        )
        await connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        row = (
            (
                await connection.execute(
                    text(
                        """
            SELECT
                *,
                ST_AsEWKB(before_geometry)=ST_AsEWKB(ST_GeomFromText(:before,4326)) AS before_ok,
                ST_AsEWKB(after_geometry)=ST_AsEWKB(ST_GeomFromText(:after,4326)) AS after_ok
            FROM work_order.edit_version_change_events
            WHERE command_id=:id
        """
                    ),
                    {
                        "id": command_id,
                        "before": BASELINE,
                        "after": MOVED,
                    },
                )
            )
            .mappings()
            .one()
        )
        for key in (
            "edit_version_id",
            "work_order_id",
            "default_state_id",
            "feature_id",
            "actor_user_id",
        ):
            assert row[key] == ids[key]
        assert row["draft_revision_before"] == 1
        assert row["draft_revision_after"] == 2
        assert row["base_network_revision"] == 1
        assert row["event_type"] == "change_set_persisted"
        assert row["before_ok"] and row["after_ok"]

    run_scenario(scenario)


def test_revert_event_preserves_previous_geometry() -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        await persist_sql_change(
            connection,
            ids,
            uuid4(),
        )
        revert_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            revert_id,
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
        await connection.execute(
            text("UPDATE work_order.edit_versions SET draft_revision=3 WHERE id=:edit_version_id"),
            ids,
        )
        await finish_command(
            connection,
            revert_id,
            state="succeeded",
        )
        await insert_event(
            connection,
            ids,
            revert_id,
            event_type="change_set_cleared",
            before_geometry=MOVED,
            after_geometry=BASELINE,
            draft_revision_before=2,
            draft_revision_after=3,
        )
        await connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        rows = (
            (
                await connection.execute(
                    text(
                        """
            SELECT
                event_type,
                draft_revision_before,
                draft_revision_after,
                ST_AsEWKB(after_geometry)=ST_AsEWKB(ST_GeomFromText(:baseline,4326)) AS at_baseline
            FROM work_order.edit_version_change_events
            WHERE edit_version_id=:edit_version_id
            ORDER BY draft_revision_after
        """
                    ),
                    {
                        **ids,
                        "baseline": BASELINE,
                    },
                )
            )
            .mappings()
            .all()
        )
        assert len(rows) == 2
        assert rows[1]["event_type"] == "change_set_cleared"
        assert rows[1]["draft_revision_before"] == 2
        assert rows[1]["draft_revision_after"] == 3
        assert rows[1]["at_baseline"] is True

    run_scenario(scenario)


@pytest.mark.parametrize(
    "field",
    [
        "edit_version_id",
        "command_id",
        "feature_id",
        "actor_user_id",
        "work_order_id",
        "default_state_id",
        "base_network_revision",
        "draft_revision_after",
        "after_geometry",
        "event_type",
    ],
)
def test_event_context_mismatch_is_rejected(field) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await persist_sql_change(
            connection,
            ids,
            command_id,
            emit_event=False,
        )
        overrides = {
            field: {
                "base_network_revision": 2,
                "draft_revision_after": 3,
                "after_geometry": BASELINE,
                "event_type": "change_set_cleared",
            }.get(
                field,
                uuid4(),
            ),
        }
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                event_command = overrides.pop(
                    "command_id",
                    command_id,
                )
                await insert_event(
                    connection,
                    ids,
                    event_command,
                    **overrides,
                )
        assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    ["running", "rejected"],
)
def test_event_requires_successful_command(state) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        await persist_sql_change(
            connection,
            ids,
            uuid4(),
            emit_event=False,
        )
        command_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            command_id,
        )
        if state == "rejected":
            await finish_command(
                connection,
                command_id,
                state="rejected",
            )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await insert_event(
                    connection,
                    ids,
                    command_id,
                )
        assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


def test_event_cannot_borrow_another_versions_command() -> None:
    async def scenario(connection):
        first = await seed_context(connection)
        second = await seed_context(
            connection,
            feature_id=first["feature_id"],
            actor_user_id=first["actor_user_id"],
        )
        command_id = uuid4()
        await persist_sql_change(
            connection,
            first,
            command_id,
            emit_event=False,
        )
        await persist_sql_change(
            connection,
            second,
            uuid4(),
            emit_event=False,
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await insert_event(
                    connection,
                    second,
                    command_id,
                )
        assert error.value.orig.sqlstate == "23514"

    run_scenario(scenario)


@pytest.mark.parametrize(
    "overrides",
    [
        {
            "draft_revision_before": 0,
        },
        {
            "draft_revision_before": -1,
        },
        {
            "draft_revision_before": 2,
        },
        {
            "draft_revision_before": 3,
        },
        {
            "before_geometry": MOVED,
        },
        {
            "before_geometry": "LINESTRING EMPTY",
        },
        {
            "before_geometry": "LINESTRING(0 0,1 1,0 1,1 0)",
        },
        {
            "before_geometry": "POINT(0 0)",
        },
        {
            "before_srid": 3857,
        },
    ],
)
def test_event_local_constraints(overrides) -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await persist_sql_change(
            connection,
            ids,
            command_id,
            emit_event=False,
        )
        with pytest.raises(DBAPIError) as error:
            async with connection.begin_nested():
                await insert_event(
                    connection,
                    ids,
                    command_id,
                    **overrides,
                )
        assert error.value.orig.sqlstate in {"23514", "22023"}

    run_scenario(scenario)


def test_event_command_and_revision_are_unique() -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await persist_sql_change(
            connection,
            ids,
            command_id,
        )
        second_id = uuid4()
        await insert_running_command(
            connection,
            ids,
            second_id,
        )
        await finish_command(
            connection,
            second_id,
            state="succeeded",
        )
        for duplicate_id in (command_id, second_id):
            with pytest.raises(DBAPIError) as error:
                async with connection.begin_nested():
                    await insert_event(
                        connection,
                        ids,
                        duplicate_id,
                    )
            assert error.value.orig.sqlstate == "23505"

    run_scenario(scenario)


def test_coordinate_change_is_not_topological_equality() -> None:
    async def scenario(connection):
        ids = await seed_context(connection)
        command_id = uuid4()
        await persist_sql_change(
            connection,
            ids,
            command_id,
            emit_event=False,
        )
        before = "LINESTRING(0 0,1 0,2 0)"
        after = "LINESTRING(0 0,1.5 0,2 0)"
        await connection.execute(
            text(
                """
            UPDATE work_order.edit_version_features SET geometry=ST_GeomFromText(:after,4326)
            WHERE edit_version_id=:edit_version_id AND feature_id=:feature_id
        """
            ),
            {
                **ids,
                "after": after,
            },
        )
        assert (
            await connection.scalar(
                text(
                    "SELECT ST_Equals(ST_GeomFromText(:before,4326),ST_GeomFromText(:after,4326))"
                ),
                {
                    "before": before,
                    "after": after,
                },
            )
            is True
        )
        await insert_event(
            connection,
            ids,
            command_id,
            before_geometry=before,
            after_geometry=after,
        )
        assert (
            await connection.scalar(
                text(
                    "SELECT count(*) FROM work_order.edit_version_change_events WHERE command_id=:id"
                ),
                {
                    "id": command_id,
                },
            )
            == 1
        )

    run_scenario(scenario)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE work_order.edit_version_change_events SET actor_user_id=gen_random_uuid() WHERE command_id=:id",
        "UPDATE work_order.edit_version_change_events SET actor_user_id=actor_user_id WHERE command_id=:id",
        "DELETE FROM work_order.edit_version_change_events WHERE command_id=:id",
        "TRUNCATE work_order.edit_version_change_events",
        """INSERT INTO work_order.edit_version_change_events
       SELECT * FROM work_order.edit_version_change_events WHERE command_id=:id
       ON CONFLICT (command_id) DO UPDATE SET occurred_at=excluded.occurred_at""",
    ],
)
def test_event_history_rejects_update_delete_truncate(statement) -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            await persist_sql_change(
                connection,
                ids,
                command_id,
            )
            original = await connection.scalar(
                text(
                    "SELECT to_jsonb(e) FROM work_order.edit_version_change_events e WHERE command_id=:id"
                ),
                {
                    "id": command_id,
                },
            )
        with pytest.raises(DBAPIError) as error:
            async with engine.begin() as connection:
                await connection.execute(
                    text(statement),
                    {
                        "id": command_id,
                    },
                )
        assert error.value.orig.sqlstate == "23514"
        async with engine.connect() as connection:
            after = await connection.scalar(
                text(
                    "SELECT to_jsonb(e) FROM work_order.edit_version_change_events e WHERE command_id=:id"
                ),
                {
                    "id": command_id,
                },
            )
            assert after == original

    run_committed_scenario(scenario)


def test_deleting_version_preserves_history() -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            await persist_sql_change(
                connection,
                ids,
                command_id,
            )
            original = await connection.scalar(
                text(
                    "SELECT to_jsonb(e) FROM work_order.edit_version_change_events e WHERE command_id=:id"
                ),
                {
                    "id": command_id,
                },
            )
            baseline = (
                await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
            )["baseline"]
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "DELETE FROM work_order.edit_version_associations WHERE edit_version_id=:edit_version_id"
                ),
                ids,
            )
            await connection.execute(
                text("DELETE FROM work_order.edit_versions WHERE id=:edit_version_id"),
                ids,
            )
        async with engine.connect() as connection:
            for table, column in (
                ("edit_versions", "id"),
                ("edit_version_commands", "edit_version_id"),
                ("edit_version_features", "edit_version_id"),
                ("edit_version_associations", "edit_version_id"),
            ):
                assert (
                    await connection.scalar(
                        text(
                            f"SELECT count(*) FROM work_order.{table} WHERE {column}=:edit_version_id"
                        ),
                        ids,
                    )
                    == 0
                )
            assert (
                await connection.scalar(
                    text(
                        "SELECT to_jsonb(e) FROM work_order.edit_version_change_events e WHERE command_id=:id"
                    ),
                    {
                        "id": command_id,
                    },
                )
                == original
            )
            assert (
                await connection.scalar(
                    text(
                        """
                SELECT jsonb_agg(to_jsonb(b) ORDER BY b.feature_id)
                FROM utility_network.default_state_features b WHERE default_state_id=:default_state_id
            """
                    ),
                    ids,
                )
                == baseline
            )
        # Surviving historical IDs do not permit a new insertion for deleted parents.
        with pytest.raises(DBAPIError) as error:
            async with engine.begin() as connection:
                await insert_event(
                    connection,
                    ids,
                    uuid4(),
                )
        assert error.value.orig.sqlstate == "23514"

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "event_failure",
    [True, False],
)
def test_change_transaction_rolls_back_snapshot_command_and_event(event_failure) -> None:
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            ids = await seed_context(connection)
            original = await snapshot_context(
                connection,
                ids["edit_version_id"],
            )
        if event_failure:
            with pytest.raises(DBAPIError) as error:
                async with engine.begin() as connection:
                    await persist_sql_change(
                        connection,
                        ids,
                        command_id,
                        emit_event=False,
                    )
                    await insert_event(
                        connection,
                        ids,
                        command_id,
                        draft_revision_after=3,
                    )
            assert error.value.orig.sqlstate == "23514"
        else:
            async with engine.begin() as connection:
                await persist_sql_change(
                    connection,
                    ids,
                    command_id,
                )
                await connection.rollback()
        async with engine.connect() as connection:
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
                        "SELECT draft_revision FROM work_order.edit_versions WHERE id=:edit_version_id"
                    ),
                    ids,
                )
                == 1
            )
            for table in ("edit_version_commands", "edit_version_change_events"):
                assert (
                    await connection.scalar(
                        text(f"SELECT count(*) FROM work_order.{table} WHERE command_id=:id"),
                        {
                            "id": command_id,
                        },
                    )
                    == 0
                )

    run_committed_scenario(scenario)
