"""Real ORM transactions against the schema created by Alembic."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import JSON, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import (
    BASELINE,
    MOVED,
    run_committed_scenario,
    seed_context,
    snapshot_context,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionCommand,
    EditVersionCommandState as State,
    EditVersionChangeEvent,
    EditVersionChangeEventType as EventType,
)


def running(
    ids,
    command_id,
):
    return EditVersionCommand(
        command_id=command_id,
        edit_version_id=ids["edit_version_id"],
        feature_id=ids["feature_id"],
        actor_user_id=ids["actor_user_id"],
        request_fingerprint="orm-fixture",
        state=State.RUNNING,
        response_payload=None,
    )


def reject(
    command,
    *,
    access=False,
):
    command.state = State.REJECTED
    command.response_status = 404 if access else 422
    command.rejection_code = "EDIT_VERSION_NOT_FOUND" if access else "GEOMETRY_INVALID"
    command.rejection_message = "Сохранение отклонено."
    command.response_payload = None
    command.retry_on_access_change = access
    command.completed_at = datetime.now(timezone.utc)


async def setup(engine):
    async with engine.begin() as connection:
        return await seed_context(connection)


def assert_check(
    error,
    name,
):
    assert error.value.orig.sqlstate == "23514"
    assert error.value.orig.__cause__.constraint_name == name


@pytest.mark.parametrize(
    "revision",
    [1, 2**31 + 7],
)
def test_orm_change_round_trip(revision):
    async def scenario(engine):
        from tests.integration_tests.first_save_orm_support import persist_orm_change

        ids = await setup(engine)
        command_id = uuid4()
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                     UPDATE work_order.edit_versions
                     SET draft_revision=:revision
                     WHERE id=:id
                     """
                ),
                {
                    "revision": revision,
                    "id": ids["edit_version_id"],
                },
            )
        async with AsyncSession(engine) as session:
            await persist_orm_change(
                session,
                ids,
                command_id,
                before_geometry=BASELINE,
                after_geometry=MOVED,
            )
            await session.commit()
        async with AsyncSession(engine) as session:
            command = await session.get(
                EditVersionCommand,
                command_id,
            )
            event = await session.get(
                EditVersionChangeEvent,
                command_id,
            )
            version = await session.get(
                EditVersion,
                ids["edit_version_id"],
            )
            assert command.state is State.SUCCEEDED
            assert command.response_payload["commandId"] == str(command_id)
            assert command.response_payload["draftVersionToken"] == str(revision + 1)
            assert command.actor_user_id == ids["actor_user_id"]
            assert command.created_at.utcoffset() is not None
            assert command.completed_at.utcoffset() is not None
            assert event.occurred_at.utcoffset() is not None
            assert event.event_type is EventType.CHANGE_SET_PERSISTED
            assert event.edit_version_id == ids["edit_version_id"]
            assert (
                event.draft_revision_before,
                event.draft_revision_after,
                version.draft_revision,
            ) == (revision, revision + 1, revision + 1)
            for field, wkt in (("before_geometry", BASELINE), ("after_geometry", MOVED)):
                geometry = getattr(
                    event,
                    field,
                )
                assert geometry.srid == 4326
                expected = await session.scalar(
                    text("SELECT ST_AsEWKB(ST_GeomFromText(:wkt,4326))"),
                    {
                        "wkt": wkt,
                    },
                )
                assert bytes(geometry.data) == expected

    run_committed_scenario(scenario)


def test_orm_revision_server_default_and_reopen():
    async def scenario(engine):
        ids = await setup(engine)
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                     DELETE
                     FROM work_order.edit_version_associations
                     WHERE edit_version_id=:id
                     """
                ),
                {
                    "id": ids["edit_version_id"],
                },
            )
            await connection.execute(
                text(
                    """
                     DELETE
                     FROM work_order.edit_versions
                     WHERE id=:id
                     """
                ),
                {
                    "id": ids["edit_version_id"],
                },
            )
        async with AsyncSession(engine) as session:
            version = EditVersion(
                geometry_xy_resolution=Decimal("0.0000001"),
                geometry_rounding_mode="ROUND_HALF_AWAY_FROM_ZERO",
                geometry_policy_version=1,
                id=ids["edit_version_id"],
                work_order_id=ids["work_order_id"],
                default_state_id=ids["default_state_id"],
                owner_user_id=ids["actor_user_id"],
            )
            session.add(version)
            await session.flush()
            assert version.draft_revision == 1
            version.last_opened_at = datetime.now(timezone.utc)
            await session.commit()
        async with AsyncSession(engine) as session:
            assert (
                await session.get(
                    EditVersion,
                    ids["edit_version_id"],
                )
            ).draft_revision == 1

    run_committed_scenario(scenario)


def test_orm_rejection_uses_sql_null():
    async def scenario(engine):
        ids = await setup(engine)
        command_id = uuid4()
        async with AsyncSession(engine) as session:
            command = running(
                ids,
                command_id,
            )
            session.add(command)
            await session.flush()
            reject(command)
            await session.commit()
        async with AsyncSession(engine) as session:
            command = await session.get(
                EditVersionCommand,
                command_id,
            )
            assert (command.state, command.response_status, command.rejection_code) == (
                State.REJECTED,
                422,
                "GEOMETRY_INVALID",
            )
            assert await session.scalar(
                select(EditVersionCommand.response_payload.is_(None)).where(
                    EditVersionCommand.command_id == command_id
                )
            )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "state",
    [State.RUNNING, State.REJECTED],
)
def test_orm_json_null_is_rejected(state):
    async def scenario(engine):
        ids = await setup(engine)
        async with AsyncSession(engine) as session:
            command = running(
                ids,
                uuid4(),
            )
            session.add(command)
            if state is State.REJECTED:
                await session.flush()
                reject(command)
            command.response_payload = JSON.NULL
            with pytest.raises(DBAPIError) as error:
                await session.flush()
            assert_check(
                error,
                "ck_ev_commands_result",
            )
            await session.rollback()

    run_committed_scenario(scenario)


def test_orm_access_retry():
    async def scenario(engine):
        ids = await setup(engine)
        command_id = uuid4()
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            command = running(
                ids,
                command_id,
            )
            session.add(command)
            await session.flush()
            reject(
                command,
                access=True,
            )
            await session.commit()
            created_at = command.created_at
        async with AsyncSession(engine) as session:
            command = await session.get(
                EditVersionCommand,
                command_id,
            )
            command.state = State.RUNNING
            command.response_status = command.response_payload = None
            command.rejection_code = command.rejection_message = command.completed_at = None
            command.retry_on_access_change = False
            await session.flush()
            reject(command)
            await session.commit()
        async with AsyncSession(engine) as session:
            command = await session.get(
                EditVersionCommand,
                command_id,
            )
            assert command.state is State.REJECTED
            assert command.response_status == 422
            assert not command.retry_on_access_change
            assert command.created_at == created_at
            assert command.request_fingerprint == "orm-fixture"
            assert await session.scalar(
                select(EditVersionCommand.response_payload.is_(None)).where(
                    EditVersionCommand.command_id == command_id
                )
            )

    run_committed_scenario(scenario)


def test_orm_running_commit_is_rejected():
    async def scenario(engine):
        ids = await setup(engine)
        command_id = uuid4()
        async with AsyncSession(engine) as session:
            session.add(
                running(
                    ids,
                    command_id,
                )
            )
            await session.flush()
            with pytest.raises(DBAPIError) as error:
                await session.commit()
            assert_check(
                error,
                "ck_ev_commands_terminal",
            )
            await session.rollback()
        async with AsyncSession(engine) as session:
            assert (
                await session.get(
                    EditVersionCommand,
                    command_id,
                )
                is None
            )

    run_committed_scenario(scenario)


def test_orm_event_failure_rolls_back_change():
    async def scenario(engine):
        from tests.integration_tests.first_save_orm_support import persist_orm_change

        ids = await setup(engine)
        command_id = uuid4()
        async with engine.connect() as connection:
            original = await snapshot_context(
                connection,
                ids["edit_version_id"],
            )
        async with AsyncSession(engine) as session:
            with pytest.raises(DBAPIError) as error:
                await persist_orm_change(
                    session,
                    ids,
                    command_id,
                    before_geometry=MOVED,
                    after_geometry=MOVED,
                )
            assert_check(
                error,
                "ck_ev_events_geometry_changed",
            )
            await session.rollback()
        async with engine.connect() as connection:
            assert (
                await snapshot_context(
                    connection,
                    ids["edit_version_id"],
                )
                == original
            )
        async with AsyncSession(engine) as session:
            assert (
                await session.get(
                    EditVersion,
                    ids["edit_version_id"],
                )
            ).draft_revision == 1
            assert (
                await session.get(
                    EditVersionCommand,
                    command_id,
                )
                is None
            )
            assert (
                await session.get(
                    EditVersionChangeEvent,
                    command_id,
                )
                is None
            )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "operation",
    ["update", "delete", "delete_parents"],
)
def test_orm_history_is_independent_and_immutable(operation):
    async def scenario(engine):
        from tests.integration_tests.first_save_orm_support import persist_orm_change

        ids = await setup(engine)
        command_id = uuid4()
        async with AsyncSession(engine) as session:
            await persist_orm_change(
                session,
                ids,
                command_id,
                before_geometry=BASELINE,
                after_geometry=MOVED,
            )
            await session.commit()
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
        async with AsyncSession(engine) as session:
            event = await session.get(
                EditVersionChangeEvent,
                command_id,
            )
            if operation == "delete_parents":
                await session.execute(
                    text(
                        """
                        DELETE
                        FROM work_order.edit_version_associations
                        WHERE edit_version_id=:id
                        """
                    ),
                    {
                        "id": ids["edit_version_id"],
                    },
                )
                await session.delete(
                    await session.get(
                        EditVersion,
                        ids["edit_version_id"],
                    )
                )
                await session.commit()
            else:
                if operation == "delete":
                    await session.delete(event)
                else:
                    event.actor_user_id = uuid4()
                with pytest.raises(DBAPIError) as error:
                    await session.flush()
                assert_check(
                    error,
                    "ck_ev_events_append_only",
                )
                await session.rollback()
        async with AsyncSession(engine) as session:
            event = await session.get(
                EditVersionChangeEvent,
                command_id,
            )
            assert event.actor_user_id == ids["actor_user_id"]
            if operation == "delete_parents":
                assert (
                    await session.get(
                        EditVersion,
                        ids["edit_version_id"],
                    )
                    is None
                )
                assert (
                    await session.get(
                        EditVersionCommand,
                        command_id,
                    )
                    is None
                )
            assert (
                await session.scalar(
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

    run_committed_scenario(scenario)
