from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    seed_repository_context,
    read_context,
    prepare_change,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
)


async def reserve(
    repository,
    root,
    ids,
    command_id,
    fingerprint="original",
):
    return await repository.reserve_command(
        root,
        command_id=command_id,
        feature_id=ids["feature_id"],
        actor_id=ids["actor_user_id"],
        fingerprint=fingerprint,
    )


@pytest.mark.parametrize(
    "access",
    [False, True],
)
def test_rejection_transition_and_access_resume(access):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        command_id = uuid4()
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            await reserve(
                repository,
                context.root,
                ids,
                command_id,
            )
            await repository.reject_command(
                context.root,
                command_id=command_id,
                status_code=404 if access else 409,
                code="EDIT_VERSION_NOT_FOUND" if access else "DRAFT_VERSION_STALE",
                message="Исходный отказ.",
                retry_on_access_change=access,
            )
        async with AsyncSession(engine) as session:
            async with session.begin():
                repository, context = await read_context(
                    session,
                    ids,
                )
                original = await repository.get_command(
                    context.root,
                    command_id=command_id,
                )
                assert original.state == "rejected"
                assert original.response_payload is None
                assert original.rejection_message == "Исходный отказ."
                with pytest.raises(RepositoryProtocolError):
                    await repository.reject_command(
                        context.root,
                        command_id=command_id,
                        status_code=409,
                        code="DRAFT_VERSION_STALE",
                        message="Другой отказ.",
                    )
            if access:
                with pytest.raises(
                    RuntimeError,
                    match="rollback",
                ):
                    async with session.begin():
                        repository, context = await read_context(
                            session,
                            ids,
                        )
                        await repository.resume_access_command(
                            context.root,
                            command_id=command_id,
                        )
                        running = await repository.get_command(
                            context.root,
                            command_id=command_id,
                        )
                        assert running.state == "running"
                        assert running.response_status is None
                        assert running.rejection_code is None
                        assert not running.retry_on_access_change
                        assert running.request_fingerprint == original.request_fingerprint
                        raise RuntimeError("rollback")
                async with session.begin():
                    repository, context = await read_context(
                        session,
                        ids,
                    )
                    assert (
                        await repository.get_command(
                            context.root,
                            command_id=command_id,
                        )
                        == original
                    )
                    await repository.resume_access_command(
                        context.root,
                        command_id=command_id,
                    )
                    await repository.complete_command(
                        context.root,
                        command_id=command_id,
                        payload={"ok": True},
                    )
            else:
                async with session.begin():
                    repository, context = await read_context(
                        session,
                        ids,
                    )
                    with pytest.raises(RepositoryProtocolError):
                        await repository.resume_access_command(
                            context.root,
                            command_id=command_id,
                        )

    run_committed_scenario(scenario)


def test_reserve_conflict_and_global_lookup_preserve_success():
    async def scenario(engine):
        async with engine.begin() as connection:
            first = await seed_repository_context(connection)
            second = await seed_repository_context(connection)
        command_id = uuid4()
        payload = {
            "result": [
                1,
                {
                    "nested": True,
                },
            ],
            "token": "2",
        }
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                first,
            )
            assert await reserve(
                repository,
                context.root,
                first,
                command_id,
            )
            await repository.complete_command(
                context.root,
                command_id=command_id,
                payload=payload,
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                second,
            )
            assert not await reserve(
                repository,
                context.root,
                second,
                command_id,
                "other",
            )
            row = await repository.get_command(
                context.root,
                command_id=command_id,
            )
            assert row.edit_version_id == first["edit_version_id"]
            assert row.request_fingerprint == "original"
            assert row.response_payload == payload
            assert row.response_status == 200
            assert not await repository.command_has_history(
                context.root,
                command_id=command_id,
            )
            with pytest.raises(RepositoryProtocolError):
                await repository.complete_command(
                    context.root,
                    command_id=command_id,
                    payload={},
                )

    run_committed_scenario(scenario)


def test_revision_uses_live_root_after_geometry_write_and_rejects_repeat():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        async with AsyncSession(engine) as session:
            async with session.begin():
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
                assert await repository.increment_revision(context.root) == 2
                with pytest.raises(RepositoryProtocolError):
                    await repository.increment_revision(context.root)
            async with session.begin():
                with pytest.raises(RepositoryProtocolError):
                    await repository.increment_revision(context.root)
        async with AsyncSession(engine) as other, other.begin():
            with pytest.raises(RepositoryProtocolError):
                await EditVersionRepository(other).increment_revision(context.root)

    run_committed_scenario(scenario)


def test_running_cannot_commit_and_reservation_rolls_back():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
        command_id = uuid4()
        with pytest.raises(DBAPIError):
            async with AsyncSession(engine) as session, session.begin():
                repository, context = await read_context(
                    session,
                    ids,
                )
                assert await reserve(
                    repository,
                    context.root,
                    ids,
                    command_id,
                )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            assert (
                await repository.get_command(
                    context.root,
                    command_id=command_id,
                )
                is None
            )

    run_committed_scenario(scenario)


def test_revision_overflow_rolls_back():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            await connection.execute(
                text(
                    "UPDATE work_order.edit_versions SET draft_revision=9223372036854775807 WHERE id=:id"
                ),
                {
                    "id": ids["edit_version_id"],
                },
            )
        with pytest.raises(DBAPIError):
            async with AsyncSession(engine) as session, session.begin():
                repository, context = await read_context(
                    session,
                    ids,
                )
                await repository.increment_revision(context.root)

    run_committed_scenario(scenario)
