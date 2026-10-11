from copy import deepcopy
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import (
    run_committed_scenario,
    persist_sql_change,
)
from tests.integration_tests.save_geometry_support import (
    BASELINE,
    request,
    call_save,
    seed_save_context,
    snapshot_save_state,
    build_save_service,
    save,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


def test_save_noop_revert_and_retry_committed_results():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            before = await snapshot_save_state(
                connection,
                ids,
            )
        baseline_noop = await call_save(
            engine,
            ids,
            request(BASELINE),
        )
        assert baseline_noop.payload["draftVersionToken"] == "1"
        assert baseline_noop.payload["basicValidation"] is None
        a = request()
        first = await call_save(
            engine,
            ids,
            a,
        )
        original = deepcopy(first.payload)
        assert original["draftVersionToken"] == "2"
        updated_noop = await call_save(
            engine,
            ids,
            request(token="2"),
        )
        assert updated_noop.payload["draftVersionToken"] == "2"
        assert updated_noop.payload["basicValidation"] == original["basicValidation"]
        reverted = await call_save(
            engine,
            ids,
            request(
                BASELINE,
                "2",
            ),
        )
        assert reverted.payload["draftVersionToken"] == "3"
        assert reverted.payload["basicValidation"] is None
        first.payload["updatedFeature"]["geometry"]["coordinates"][1][0] = 0
        replay = await call_save(
            engine,
            ids,
            a,
        )
        assert replay.payload == original
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert after["root"]["draft_revision"] == 3
        assert len(after["commands"]) == 4
        assert all(row["state"] == "succeeded" for row in after["commands"])
        assert (
            next(
                row["response_payload"]
                for row in after["commands"]
                if row["command_id"] == a.command_id
            )
            == original
        )
        assert len(after["events"]) == 2
        assert {row["event_type"] for row in after["events"]} == {
            "change_set_persisted",
            "change_set_cleared",
        }
        for key in before.keys() - {"root", "commands", "events"}:
            assert after[key] == before[key]

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "phase",
    [
        "write_current",
        "increment_revision",
        "complete_command",
        "append_change_event",
        "deferred_commit",
    ],
)
def test_save_failure_rolls_back_every_write(phase):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            before = await snapshot_save_state(
                connection,
                ids,
            )
        value = request()
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
                    # Event INSERT succeeded. A second unfinished command fails only at commit.
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
                        fingerprint="test-deferred-running",
                    )
                    return
                raise RuntimeError("test-only failure")

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
        successful_retry = await call_save(
            engine,
            ids,
            value,
        )
        assert successful_retry.payload["draftVersionToken"] == "2"

    run_committed_scenario(scenario)


def test_history_id_survives_registry_deletion():
    async def scenario(engine):
        command_id = uuid4()
        async with engine.begin() as connection:
            old = await seed_save_context(connection)
            await persist_sql_change(
                connection,
                old,
                command_id,
            )
            await connection.execute(
                text("DELETE FROM work_order.edit_versions WHERE id=:id"),
                {
                    "id": old["edit_version_id"],
                },
            )
            target = await seed_save_context(connection)
            before = await snapshot_save_state(
                connection,
                target,
            )
        with pytest.raises(WorkOrderApiError) as error:
            await call_save(
                engine,
                target,
                request(command_id=command_id),
            )
        assert error.value.code == "COMMAND_ID_REUSED"
        async with engine.connect() as connection:
            assert (
                await snapshot_save_state(
                    connection,
                    target,
                )
                == before
            )

    run_committed_scenario(scenario)


def test_invalid_geometry_leaves_rejected_command_without_mutation():
    from dataclasses import replace

    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            before = await snapshot_save_state(
                connection,
                ids,
            )
        collapsed = replace(
            BASELINE,
            coordinates=(BASELINE.coordinates[0], BASELINE.coordinates[0], BASELINE.coordinates[2]),
        )
        with pytest.raises(WorkOrderApiError) as error:
            await call_save(
                engine,
                ids,
                request(collapsed),
            )
        assert error.value.code == "GEOMETRY_INVALID"
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert len(after["commands"]) == 1
        assert after["commands"][0]["rejection_code"] == "GEOMETRY_INVALID"
        for key in before.keys() - {"commands"}:
            assert after[key] == before[key]

    run_committed_scenario(scenario)


def test_off_grid_baseline_roundtrip_and_revert_preserve_storage():
    from dataclasses import replace
    from decimal import Decimal
    from utility_service.domain_services.edit_geometry.types import GeometryValue
    from utility_service.infrastructure.postgresql.geometry_codec import encode_geometry

    async def scenario(engine):
        baseline = GeometryValue(
            "LineString",
            tuple(
                tuple(Decimal(value) for value in point)
                for point in (
                    ("65.5200000499", "44.8200000501"),
                    ("65.5250000499", "44.8205000501"),
                    ("65.5300000501", "44.8200000499"),
                )
            ),
        )
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            for table, key in (
                ("utility_network.default_state_features", "default_state_id"),
                ("work_order.edit_version_features", "edit_version_id"),
            ):
                await connection.execute(
                    text(
                        f"""
                        UPDATE {table}
                        SET geometry = ST_GeomFromEWKB(:geometry)
                        WHERE {key} = :{key} AND feature_id = :feature_id
                        """
                    ),
                    {
                        **ids,
                        "geometry": encode_geometry(baseline),
                    },
                )
            before = await snapshot_save_state(
                connection,
                ids,
            )
        moved = replace(
            baseline,
            coordinates=(
                baseline.coordinates[0],
                (Decimal("65.525"), Decimal("44.8215")),
                baseline.coordinates[2],
            ),
        )
        changed = await call_save(
            engine,
            ids,
            request(moved),
        )
        coordinates = changed.payload["updatedFeature"]["geometry"]["coordinates"]
        assert tuple(Decimal(str(value)) for value in coordinates[0]) == baseline.coordinates[0]
        assert tuple(Decimal(str(value)) for value in coordinates[2]) == baseline.coordinates[2]
        await call_save(
            engine,
            ids,
            request(
                baseline,
                "2",
            ),
        )
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert after["features"] == before["features"]
        assert after["baseline"] == before["baseline"]

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "access_retry",
    [False, True],
)
def test_stored_rejection_resumes_only_access_retry(access_retry):
    from tests.integration_tests.first_save_schema_support import finish_command
    from tests.integration_tests.edit_geometry_repository_support import read_context
    from utility_service.domain_services.edit_geometry.fingerprint import command_fingerprint
    from utility_service.domain_services.edit_geometry.types import FingerprintContext
    from utility_service.infrastructure.postgresql.geometry_codec import decode_geometry

    async def scenario(engine):
        value = request()
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            prepared = repository.prepare_candidate(
                context,
                value.geometry,
            )
            fingerprint = command_fingerprint(
                FingerprintContext(
                    ids["work_order_id"],
                    ids["edit_version_id"],
                    ids["feature_id"],
                    ids["actor_user_id"],
                    ids["default_state_id"],
                    context.root.base_network_revision,
                    value.draft_version_token,
                ),
                decode_geometry(context.baseline.geometry_ewkb),
                context.root.policy,
                prepared.prepared,
            )
            await repository.reserve_command(
                context.root,
                command_id=value.command_id,
                feature_id=ids["feature_id"],
                actor_id=ids["actor_user_id"],
                fingerprint=fingerprint,
            )
            await finish_command(
                await session.connection(),
                value.command_id,
                state="rejected",
                retry_on_access_change=access_retry,
            )
        async with engine.connect() as connection:
            before = await snapshot_save_state(
                connection,
                ids,
            )
        if access_retry:
            result = await call_save(
                engine,
                ids,
                value,
            )
            assert result.payload["draftVersionToken"] == "2"
            async with engine.connect() as connection:
                after = await snapshot_save_state(
                    connection,
                    ids,
                )
            assert len(after["events"]) == 1
            assert after["commands"][0]["state"] == "succeeded"
            assert (
                after["commands"][0]["request_fingerprint"]
                == before["commands"][0]["request_fingerprint"]
            )
        else:
            with pytest.raises(WorkOrderApiError) as error:
                await call_save(
                    engine,
                    ids,
                    value,
                )
            assert error.value.code == "GEOMETRY_INVALID"
            async with engine.connect() as connection:
                assert (
                    await snapshot_save_state(
                        connection,
                        ids,
                    )
                    == before
                )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "replay",
    [False, True],
)
@pytest.mark.parametrize(
    "revocation",
    ["inactive", "reviewer"],
)
def test_retained_actor_cannot_save_or_replay_after_access_revoked(
    replay,
    revocation,
):
    from sqlalchemy import update
    from utility_service.infrastructure.postgresql.models.user import User, UserRole

    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        value = request()
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            async with session.begin():
                retained = await session.get(
                    User,
                    ids["actor_user_id"],
                )
            assert retained.is_active and retained.role is UserRole.EDITOR
            service = build_save_service(session)
            if replay:
                await save(
                    service,
                    ids,
                    value,
                )
            async with engine.begin() as connection:
                await connection.execute(
                    update(User)
                    .where(User.id == ids["actor_user_id"])
                    .values(
                        **(
                            {"is_active": False}
                            if revocation == "inactive"
                            else {"role": UserRole.REVIEWER}
                        )
                    )
                )
                before = await snapshot_save_state(
                    connection,
                    ids,
                )
            with pytest.raises(WorkOrderApiError) as error:
                await save(
                    service,
                    ids,
                    value,
                )
            assert error.value.code == "ROLE_NOT_ALLOWED"
            async with engine.connect() as connection:
                after = await snapshot_save_state(
                    connection,
                    ids,
                )
            if replay:
                assert after == before
            else:
                assert len(after["commands"]) == 1
                assert after["commands"][0]["rejection_code"] == "ROLE_NOT_ALLOWED"
                for key in before.keys() - {"commands"}:
                    assert after[key] == before[key]

    run_committed_scenario(scenario)
