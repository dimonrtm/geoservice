import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import (
    run_committed_scenario,
    insert_running_command,
    finish_command,
    insert_event,
)
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    seed_repository_context,
    prepare_change,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.models.work_order import EditVersionFeature


async def wait_for_block(
    observer,
    waiter,
    blocker,
):
    async with asyncio.timeout(5):
        while blocker not in await observer.scalar(
            text("SELECT pg_blocking_pids(:pid)"),
            {"pid": waiter},
        ):
            await asyncio.sleep(0.02)


@pytest.mark.parametrize(
    "commit",
    [
        True,
        False,
    ],
)
def test_waiting_context_reads_fresh_state_despite_identity_map(commit):
    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_repository_context(setup)
        async with (
            AsyncSession(engine) as first,
            AsyncSession(engine) as second,
            engine.connect() as observer,
        ):
            async with asyncio.timeout(15):
                await first.begin()
                await second.begin()
                old = await second.get(
                    EditVersionFeature,
                    (
                        ids["edit_version_id"],
                        ids["feature_id"],
                    ),
                )
                assert old.operation.value == "unchanged"
                assert await second.scalar(text("SHOW transaction_isolation")) == "read committed"
                repository, context = await read_context(
                    first,
                    ids,
                )
                change = await prepare_change(
                    repository,
                    context,
                )
                await repository.write_current(change)
                await first.execute(
                    text("UPDATE work_order.edit_versions SET draft_revision=2 WHERE id=:id"),
                    {"id": ids["edit_version_id"]},
                )
                first_pid = await first.scalar(text("SELECT pg_backend_pid()"))
                second_pid = await second.scalar(text("SELECT pg_backend_pid()"))
                task = asyncio.create_task(
                    read_context(
                        second,
                        ids,
                    )
                )
                try:
                    await wait_for_block(
                        observer,
                        second_pid,
                        first_pid,
                    )
                    assert not task.done()
                    await (first.commit() if commit else first.rollback())
                    _, fresh = await task
                    assert fresh.current.geometry_ewkb == (
                        change.after_ewkb if commit else change.before_ewkb
                    )
                    assert fresh.root.draft_revision == (2 if commit else 1)
                    assert fresh.current.operation == ("updated" if commit else "unchanged")
                finally:
                    if not task.done():
                        task.cancel()
                    await asyncio.gather(
                        task,
                        return_exceptions=True,
                    )
                    await first.rollback()
                    await second.rollback()

    run_committed_scenario(scenario)


def test_other_version_is_not_blocked():
    async def scenario(engine):
        async with engine.begin() as setup:
            first_ids = await seed_repository_context(setup)
            second_ids = await seed_repository_context(setup)
        async with AsyncSession(engine) as first, first.begin():
            await read_context(
                first,
                first_ids,
            )
            async with asyncio.timeout(3), AsyncSession(engine) as second, second.begin():
                repository, context = await read_context(
                    second,
                    second_ids,
                )
                assert (
                    await repository.write_current(
                        await prepare_change(
                            repository,
                            context,
                        )
                    )
                ).changed

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "save_first",
    [
        True,
        False,
    ],
)
def test_reopen_and_repository_do_not_deadlock(save_first):
    from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
        WorkOrderRepository,
    )
    from utility_service.use_cases.services.edit_version_service import EditVersionService
    from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
    from decimal import Decimal

    async def reopen(
        session,
        ids,
    ):
        repository = WorkOrderRepository(session)
        await repository.get_by_id_for_update(ids["work_order_id"])
        version = await EditVersionRepository(session).get_open_edit_version(ids["work_order_id"])
        service = EditVersionService(
            session,
            None,
            repository,
            None,
            edit_version_repository=EditVersionRepository(session),
            geometry_policy=GeometryPolicy(Decimal("0.0000001")),
        )
        await service.reopen_edit_version(version)

    async def save(
        session,
        ids,
    ):
        repository, context = await read_context(
            session,
            ids,
        )
        await repository.write_current(
            await prepare_change(
                repository,
                context,
            )
        )

    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_repository_context(setup)
            await setup.execute(
                text(
                    "UPDATE work_order.edit_versions SET last_opened_at='2000-01-01' WHERE id=:edit_version_id"
                ),
                ids,
            )
        async with (
            AsyncSession(engine) as first,
            AsyncSession(engine) as second,
            engine.connect() as observer,
        ):
            async with asyncio.timeout(15):
                await first.begin()
                await second.begin()
                await (
                    save(
                        first,
                        ids,
                    )
                    if save_first
                    else reopen(
                        first,
                        ids,
                    )
                )
                first_pid = await first.scalar(text("SELECT pg_backend_pid()"))
                second_pid = await second.scalar(text("SELECT pg_backend_pid()"))
                task = asyncio.create_task(
                    reopen(
                        second,
                        ids,
                    )
                    if save_first
                    else save(
                        second,
                        ids,
                    )
                )
                try:
                    await wait_for_block(
                        observer,
                        second_pid,
                        first_pid,
                    )
                    await first.commit()
                    await task
                    await second.commit()
                finally:
                    if not task.done():
                        task.cancel()
                    await asyncio.gather(
                        task,
                        return_exceptions=True,
                    )
                    await first.rollback()
                    await second.rollback()
        async with engine.connect() as observer:
            assert await observer.scalar(
                text(
                    "SELECT last_opened_at > '2000-01-01' FROM work_order.edit_versions WHERE id=:edit_version_id"
                ),
                ids,
            )
            assert (
                await observer.scalar(
                    text(
                        """
                        SELECT operation
                        FROM work_order.edit_version_features
                        WHERE edit_version_id = :edit_version_id
                            AND feature_id = :feature_id
                        """
                    ),
                    ids,
                )
                == "updated"
            )

    run_committed_scenario(scenario)


def test_repository_write_is_compatible_with_history_trigger():
    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_repository_context(setup)
        command_id = uuid4()
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            connection = await session.connection()
            await insert_running_command(
                connection,
                ids,
                command_id,
            )
            # Existing event helper accepts explicit before/after geometry overrides.
            change = await prepare_change(
                repository,
                context,
            )
            await repository.write_current(change)
            await session.execute(
                text(
                    "UPDATE work_order.edit_versions SET draft_revision=draft_revision+1 WHERE id=:edit_version_id"
                ),
                ids,
            )
            await finish_command(
                connection,
                command_id,
                state="succeeded",
            )
            await insert_event(
                connection,
                ids,
                command_id,
                after_geometry="LINESTRING(65.520 44.820,65.526 44.821,65.530 44.820)",
            )
        async with engine.connect() as observer:
            row = (
                await observer.execute(
                    text(
                        """
                        SELECT
                            ST_AsEWKB(before_geometry),
                            ST_AsEWKB(after_geometry),
                            draft_revision_after
                        FROM work_order.edit_version_change_events
                        WHERE command_id = :id
                        """
                    ),
                    {"id": command_id},
                )
            ).one()
            assert row[0] == change.before_ewkb
            assert row[1] == change.after_ewkb
            assert row[2] == 2

    run_committed_scenario(scenario)
