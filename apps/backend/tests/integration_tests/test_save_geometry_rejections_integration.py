from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DBAPIError

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import (
    BASELINE,
    MOVED,
    request,
    call_save,
    seed_save_context,
    snapshot_save_state,
    build_save_service,
    save,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.infrastructure.postgresql.models.user import User


@pytest.mark.parametrize(
    "kind,code,status",
    [
        ("stale", "DRAFT_VERSION_STALE", 409),
        ("structure", "GEOMETRY_STRUCTURE_CHANGED", 422),
        ("count", "GEOMETRY_STRUCTURE_CHANGED", 422),
        ("invalid", "GEOMETRY_INVALID", 422),
        ("outside", "GEOMETRY_OUTSIDE_AOI", 422),
        ("context", "WORK_ORDER_CONTEXT_INVALID", 422),
        ("eligible", "FEATURE_NOT_EDITABLE", 422),
        ("closed", "SAVE_CONTEXT_CLOSED", 409),
        ("role", "ROLE_NOT_ALLOWED", 403),
        ("multiple", "MULTIPLE_FEATURE_CHANGE_NOT_ALLOWED", 409),
    ],
)
def test_domain_rejections_are_durable_without_mutation(
    kind,
    code,
    status,
):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            updates = {
                "multiple": """
                UPDATE work_order.edit_version_features
                SET operation = 'updated'
                WHERE edit_version_id = :edit_version_id
                    AND feature_id <> :feature_id
                """,
                "context": """
                UPDATE work_order.edit_version_features
                SET operation = 'updated'
                WHERE edit_version_id = :edit_version_id
                """,
                "eligible": """
                UPDATE work_order.edit_version_features
                SET operation = 'created'
                WHERE edit_version_id = :edit_version_id
                """,
                "closed": """
                UPDATE work_order.work_orders
                SET status = 'assigned'
                WHERE id = :work_order_id
                """,
            }
            if kind in updates:
                await connection.execute(
                    text(updates[kind]),
                    ids,
                )
            if kind == "role":
                await connection.execute(
                    User.__table__.update()
                    .where(User.id == ids["actor_user_id"])
                    .values(is_active=False)
                )
            before = await snapshot_save_state(
                connection,
                ids,
            )
        geometry = MOVED
        if kind == "structure":
            geometry = replace(
                MOVED,
                coordinates=((Decimal("65.521"), Decimal("44.82")), *MOVED.coordinates[1:]),
            )
        elif kind == "count":
            geometry = replace(
                MOVED,
                coordinates=MOVED.coordinates[:2],
            )
        elif kind == "invalid":
            geometry = replace(
                BASELINE,
                coordinates=(
                    BASELINE.coordinates[0],
                    BASELINE.coordinates[0],
                    BASELINE.coordinates[2],
                ),
            )
        elif kind == "outside":
            geometry = replace(
                MOVED,
                coordinates=(
                    MOVED.coordinates[0],
                    (Decimal("65.525"), Decimal("44.86")),
                    MOVED.coordinates[2],
                ),
            )
        value = request(
            geometry,
            "old" if kind == "stale" else "1",
        )
        for _ in range(2):
            with pytest.raises(WorkOrderApiError) as error:
                await call_save(
                    engine,
                    ids,
                    value,
                )
            assert (error.value.code, error.value.status_code) == (code, status)
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert len(after["commands"]) == 1
        row = after["commands"][0]
        assert row["state"] == "rejected"
        assert (row["rejection_code"], row["response_status"]) == (code, status)
        assert row["completed_at"] is not None
        for key in before.keys() - {"commands"}:
            assert after[key] == before[key]

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "phase",
    ["complete_command", "append_change_event", "deferred_commit"],
)
def test_successful_access_resume_rolls_back_to_original_rejection(phase):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            await connection.execute(
                text(
                    """
                    UPDATE work_order.work_orders
                    SET assignee_user_id = :other
                    WHERE id = :work_order_id
                    """
                ),
                {
                    **ids,
                    "other": uuid4(),
                },
            )
        value = request()
        with pytest.raises(WorkOrderApiError) as initial:
            await call_save(
                engine,
                ids,
                value,
            )
        assert initial.value.code == "EDIT_VERSION_NOT_FOUND"
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    UPDATE work_order.work_orders
                    SET assignee_user_id = :actor_user_id
                    WHERE id = :work_order_id
                    """
                ),
                ids,
            )
            before = await snapshot_save_state(
                connection,
                ids,
            )
        async with AsyncSession(engine) as session:
            service = build_save_service(session)
            repository = service.edit_version_repository
            method = "append_change_event" if phase == "deferred_commit" else phase
            original = getattr(
                repository,
                method,
            )

            async def fail(
                *args,
                **kwargs,
            ):
                await original(
                    *args,
                    **kwargs,
                )
                if phase == "deferred_commit":
                    assert (
                        await session.scalar(
                            text(
                                """
                                SELECT count(*)
                                FROM work_order.edit_version_change_events
                                WHERE command_id = :id
                                """
                            ),
                            {"id": value.command_id},
                        )
                        == 1
                    )
                    await repository.reserve_command(
                        args[0],
                        command_id=uuid4(),
                        feature_id=ids["feature_id"],
                        actor_id=ids["actor_user_id"],
                        fingerprint="unfinished",
                    )
                    return
                raise RuntimeError("resume failed")

            setattr(
                repository,
                method,
                fail,
            )
            with pytest.raises(DBAPIError if phase == "deferred_commit" else RuntimeError):
                await save(
                    service,
                    ids,
                    value,
                )
        async with engine.connect() as connection:
            assert (
                await snapshot_save_state(
                    connection,
                    ids,
                )
                == before
            )
        assert (
            await call_save(
                engine,
                ids,
                value,
            )
        ).payload["draftVersionToken"] == "2"
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert len(after["commands"]) == len(after["events"]) == 1
        assert after["commands"][0]["state"] == "succeeded"
        assert after["commands"][0]["created_at"] == before["commands"][0]["created_at"]
        assert (
            after["commands"][0]["request_fingerprint"]
            == before["commands"][0]["request_fingerprint"]
        )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "access",
    [False, True],
)
@pytest.mark.parametrize(
    "stale",
    [False, True],
)
def test_baseline_repair_and_access_recovery(
    access,
    stale,
):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            # Existing DB constraints permit inconsistent revision provenance, not wrong geometry types.
            await connection.execute(
                text(
                    """
                    UPDATE utility_network.default_states
                    SET base_network_revision = 2
                    WHERE id = :default_state_id
                    """
                ),
                ids,
            )
            if access:
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.work_orders
                        SET assignee_user_id = :other
                        WHERE id = :work_order_id
                        """
                    ),
                    {
                        **ids,
                        "other": uuid4(),
                    },
                )
        value = request(token="old" if stale else "1")
        with pytest.raises(WorkOrderApiError) as first:
            await call_save(
                engine,
                ids,
                value,
            )
        assert first.value.code == (
            "EDIT_VERSION_NOT_FOUND" if access else "WORK_ORDER_CONTEXT_INVALID"
        )
        async with engine.begin() as connection:
            before = await snapshot_save_state(
                connection,
                ids,
            )
            original = before["commands"][0]
            assert original["request_fingerprint"].startswith("geom-contextless-v1:")
            await connection.execute(
                text(
                    """
                    UPDATE utility_network.default_states
                    SET base_network_revision = 1
                    WHERE id = :default_state_id
                    """
                ),
                ids,
            )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.work_orders
                    SET assignee_user_id = :actor_user_id
                    WHERE id = :work_order_id
                    """
                ),
                ids,
            )
        equivalent = replace(
            value,
            geometry=replace(
                MOVED,
                coordinates=(
                    MOVED.coordinates[0],
                    (Decimal("65.52500001"), Decimal("44.8215")),
                    MOVED.coordinates[2],
                ),
            ),
        )
        if access and not stale:
            assert (
                await call_save(
                    engine,
                    ids,
                    equivalent,
                )
            ).status_code == 200
        else:
            with pytest.raises(WorkOrderApiError) as retry:
                await call_save(
                    engine,
                    ids,
                    equivalent,
                )
            assert retry.value.code == ("DRAFT_VERSION_STALE" if access else first.value.code)
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert after["commands"][0]["request_fingerprint"] == original["request_fingerprint"]
        assert len(after["events"]) == int(access and not stale)
        if not access:
            assert after["commands"] == before["commands"]
            with pytest.raises(WorkOrderApiError) as reused:
                await call_save(
                    engine,
                    ids,
                    replace(
                        value,
                        draft_version_token="new",
                    ),
                )
            assert reused.value.code == "COMMAND_ID_REUSED"

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "resume",
    [False, True],
)
def test_rejection_commit_failure_and_resume_rollback(resume):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            if resume:
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.work_orders
                        SET assignee_user_id = :other
                        WHERE id = :work_order_id
                        """
                    ),
                    {
                        **ids,
                        "other": uuid4(),
                    },
                )
        value = request(token="old")
        if resume:
            with pytest.raises(WorkOrderApiError):
                await call_save(
                    engine,
                    ids,
                    value,
                )
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.work_orders
                        SET assignee_user_id = :actor_user_id
                        WHERE id = :work_order_id
                        """
                    ),
                    ids,
                )
        async with engine.connect() as connection:
            before = await snapshot_save_state(
                connection,
                ids,
            )
        async with AsyncSession(engine) as session:
            service = build_save_service(session)

            async def leave_running(
                *args,
                **kwargs,
            ):
                pass

            service.edit_version_repository.reject_command = leave_running
            with pytest.raises(DBAPIError):
                await save(
                    service,
                    ids,
                    value,
                )
        async with engine.connect() as connection:
            assert (
                await snapshot_save_state(
                    connection,
                    ids,
                )
                == before
            )
        with pytest.raises(WorkOrderApiError) as result:
            await call_save(
                engine,
                ids,
                value,
            )
        assert result.value.code == "DRAFT_VERSION_STALE"

    run_committed_scenario(scenario)
