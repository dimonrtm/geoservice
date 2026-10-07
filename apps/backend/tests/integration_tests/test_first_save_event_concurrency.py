"""The event trigger serializes insertion against deletion of its root."""

import asyncio
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection

from tests.integration_tests.first_save_schema_support import (
    insert_event,
    persist_sql_change,
    run_committed_scenario,
    seed_context,
    snapshot_context,
)


async def wait_until_blocked(
    observer: AsyncConnection,
    *,
    waiter_pid: int,
    blocker_pid: int,
    timeout: float = 5.0,
) -> None:
    async with asyncio.timeout(timeout):
        while True:
            blockers = await observer.scalar(
                text("SELECT pg_blocking_pids(:pid)"),
                {
                    "pid": waiter_pid,
                },
            )
            if blocker_pid in blockers:
                return
            await asyncio.sleep(0.02)


async def delete_version(
    connection: AsyncConnection,
    edit_version_id: UUID,
) -> None:
    params = {
        "id": edit_version_id,
    }
    await connection.execute(
        text(
            """
             SELECT id
             FROM work_order.edit_versions
             WHERE id=:id FOR UPDATE
             """
        ),
        params,
    )
    await connection.execute(
        text(
            """
             DELETE
             FROM work_order.edit_version_associations
             WHERE edit_version_id=:id
             """
        ),
        params,
    )
    await connection.execute(
        text(
            """
             DELETE
             FROM work_order.edit_versions
             WHERE id=:id
             """
        ),
        params,
    )


@pytest.mark.parametrize(
    "insert_first",
    [True, False],
    ids=["insert_blocks_delete", "delete_rejects_insert"],
)
def test_event_insert_and_root_deletion_are_serialized(insert_first):
    async def scenario(engine):
        async with asyncio.timeout(15):
            command_id = uuid4()
            async with engine.begin() as setup:
                ids = await seed_context(setup)
                await persist_sql_change(
                    setup,
                    ids,
                    command_id,
                    emit_event=False,
                )
                baseline = (
                    await snapshot_context(
                        setup,
                        ids["edit_version_id"],
                    )
                )["baseline"]
            async with (
                engine.connect() as first,
                engine.connect() as second,
                engine.connect() as observer,
            ):
                first_tx = await first.begin()
                second_tx = await second.begin()
                task = None
                original = None
                try:
                    first_pid = await first.scalar(text("SELECT pg_backend_pid()"))
                    second_pid = await second.scalar(text("SELECT pg_backend_pid()"))
                    if insert_first:
                        await insert_event(
                            first,
                            ids,
                            command_id,
                        )
                        original = await first.scalar(
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
                        task = asyncio.create_task(
                            delete_version(
                                second,
                                ids["edit_version_id"],
                            )
                        )
                    else:
                        await delete_version(
                            first,
                            ids["edit_version_id"],
                        )
                        task = asyncio.create_task(
                            insert_event(
                                second,
                                ids,
                                command_id,
                            )
                        )
                    await wait_until_blocked(
                        observer,
                        waiter_pid=second_pid,
                        blocker_pid=first_pid,
                    )
                    assert not task.done()
                    await first_tx.commit()
                    if insert_first:
                        await task
                        await second_tx.commit()
                    else:
                        with pytest.raises(DBAPIError) as error:
                            await task
                        assert error.value.orig.sqlstate == "23514"
                        assert error.value.orig.__cause__.constraint_name == "ck_ev_events_context"
                        await second_tx.rollback()
                finally:
                    if task is not None:
                        if not task.done():
                            task.cancel()
                        # Retrieve even an already failed task; normal-path errors are asserted above.
                        await asyncio.gather(
                            task,
                            return_exceptions=True,
                        )
                    if first_tx.is_active:
                        await first_tx.rollback()
                    if second_tx.is_active:
                        await second_tx.rollback()
            async with engine.connect() as connection:
                for table, column in (
                    ("edit_versions", "id"),
                    ("edit_version_commands", "edit_version_id"),
                    ("edit_version_features", "edit_version_id"),
                    ("edit_version_associations", "edit_version_id"),
                ):
                    assert (
                        await connection.scalar(
                            text(f"SELECT count(*) FROM work_order.{table} WHERE {column}=:id"),
                            {
                                "id": ids["edit_version_id"],
                            },
                        )
                        == 0
                    )
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
                assert (
                    await connection.scalar(
                        text(
                            """
                            SELECT jsonb_agg(to_jsonb(b) ORDER BY b.feature_id)
                            FROM utility_network.default_state_features b
                            WHERE default_state_id=:id
                            """
                        ),
                        {
                            "id": ids["default_state_id"],
                        },
                    )
                    == baseline
                )

    run_committed_scenario(scenario)
