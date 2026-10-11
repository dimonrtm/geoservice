import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.test_edit_geometry_concurrency import wait_for_block
from tests.integration_tests.save_geometry_support import (
    seed_save_context,
    build_save_service,
    request,
    save,
    snapshot_save_state,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionFeature,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


async def race(
    engine,
    first_ids,
    second_ids,
    first_request,
    second_request,
    *,
    rollback=False,
    first_open=False,
    second_open=False,
    preload=False,
):
    entered, release, second_ready = asyncio.Event(), asyncio.Event(), asyncio.Event()
    pids = {}
    tasks = []
    async with (
        AsyncSession(engine) as first_session,
        AsyncSession(engine) as second_session,
        engine.connect() as observer,
    ):
        first = build_save_service(first_session)
        second = build_save_service(second_session)
        retained = []
        for name, service, session, ids in (
            ("first", first, first_session, first_ids),
            ("second", second, second_session, second_ids),
        ):
            original_actor = service.user_repository.get_by_id

            async def actor(
                actor_id,
                *,
                name=name,
                session=session,
                ids=ids,
                original=original_actor,
            ):
                pids[name] = await session.scalar(text("SELECT pg_backend_pid()"))
                if name == "second":
                    if preload:
                        retained.append(
                            await session.get(
                                EditVersion,
                                ids["edit_version_id"],
                            )
                        )
                        retained.append(
                            await session.get(
                                EditVersionFeature,
                                (ids["edit_version_id"], ids["feature_id"]),
                            )
                        )
                    second_ready.set()
                return await original(actor_id)

            service.user_repository.get_by_id = actor
        method = "touch_edit_version" if first_open else "reserve_command"
        original_method = getattr(
            first.edit_version_repository,
            method,
        )

        async def hold(
            *args,
            **kwargs,
        ):
            result = await original_method(
                *args,
                **kwargs,
            )
            entered.set()
            await release.wait()
            if rollback:
                raise RuntimeError("first rolled back")
            return result

        setattr(
            first.edit_version_repository,
            method,
            hold,
        )

        async def invoke(
            service,
            ids,
            value,
            is_open,
        ):
            if is_open:
                return await service.open_for_work_order(
                    ids["work_order_id"],
                    ids["actor_user_id"],
                )
            return await save(
                service,
                ids,
                value,
            )

        try:
            async with asyncio.timeout(15):
                tasks.append(
                    asyncio.create_task(
                        invoke(
                            first,
                            first_ids,
                            first_request,
                            first_open,
                        )
                    )
                )
                await entered.wait()
                tasks.append(
                    asyncio.create_task(
                        invoke(
                            second,
                            second_ids,
                            second_request,
                            second_open,
                        )
                    )
                )
                await second_ready.wait()
                await wait_for_block(
                    observer,
                    pids["second"],
                    pids["first"],
                )
                assert not tasks[1].done()
                release.set()
                return await asyncio.gather(
                    *tasks,
                    return_exceptions=True,
                )
        finally:
            release.set()
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )


@pytest.mark.parametrize(
    "same_command",
    [True, False],
)
def test_competing_same_version_requests(same_command):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        first = request()
        second = first if same_command else request()
        results = await race(
            engine,
            ids,
            ids,
            first,
            second,
            preload=True,
        )
        assert results[0].payload["draftVersionToken"] == "2"
        if same_command:
            assert results[1].payload == results[0].payload
        else:
            assert isinstance(
                results[1],
                WorkOrderApiError,
            )
            assert results[1].code == "DRAFT_VERSION_STALE"
        async with engine.connect() as connection:
            snapshot = await snapshot_save_state(
                connection,
                ids,
            )
        assert snapshot["root"]["draft_revision"] == 2
        assert len(snapshot["commands"]) == 1
        assert snapshot["commands"][0]["state"] == "succeeded"

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "rollback",
    [False, True],
)
def test_same_id_across_versions_has_one_committed_owner(rollback):
    async def scenario(engine):
        async with engine.begin() as connection:
            first = await seed_save_context(connection)
            second = await seed_save_context(connection)
        value = request(command_id=uuid4())
        results = await race(
            engine,
            first,
            second,
            value,
            value,
            rollback=rollback,
        )
        if rollback:
            assert isinstance(
                results[0],
                RuntimeError,
            )
            assert results[1].payload["draftVersionToken"] == "2"
        else:
            assert results[0].payload["draftVersionToken"] == "2"
            assert isinstance(
                results[1],
                WorkOrderApiError,
            )
            assert results[1].code == "COMMAND_ID_REUSED"
        async with engine.connect() as connection:
            a = await snapshot_save_state(
                connection,
                first,
            )
            b = await snapshot_save_state(
                connection,
                second,
            )
        assert (a["root"]["draft_revision"], b["root"]["draft_revision"]) == (
            (1, 2) if rollback else (2, 1)
        )
        assert len(a["commands"]) + len(b["commands"]) == 1
        assert (a["commands"] + b["commands"])[0]["state"] == "succeeded"

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "open_first",
    [True, False],
)
def test_save_and_open_do_not_deadlock(open_first):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        value = request()
        results = await race(
            engine,
            ids,
            ids,
            value,
            value,
            first_open=open_first,
            second_open=not open_first,
        )
        assert not any(
            isinstance(
                result,
                BaseException,
            )
            for result in results
        )
        async with engine.connect() as connection:
            snapshot = await snapshot_save_state(
                connection,
                ids,
            )
        assert snapshot["root"]["draft_revision"] == 2
        assert len(snapshot["commands"]) == 1

    run_committed_scenario(scenario)
