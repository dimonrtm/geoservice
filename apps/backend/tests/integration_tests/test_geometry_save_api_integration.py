from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import (
    BASELINE,
    MOVED,
    seed_save_context,
    snapshot_save_state,
)
from tests.integration_tests.workspace_api_support import (
    assert_error,
    build_workspace_api,
    client_for,
    current_geometry,
    geometry_path,
    read_workspace,
    version_path,
)
from utility_service.infrastructure.postgresql.geometry_codec import geometry_to_geojson
from utility_service.use_cases.schemas.edit_version.geometry_contract import GeometrySaveResponseOut


def body(
    geometry=MOVED,
    token="1",
    command_id=None,
):
    return {
        "commandId": str(command_id or uuid4()),
        "draftVersionToken": token,
        "geometry": geometry_to_geojson(geometry),
    }


async def snapshot(
    engine,
    ids,
):
    async with engine.connect() as connection:
        return await snapshot_save_state(
            connection,
            ids,
        )


def test_http_open_save_readback_revert():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            # Удаляется только исходная тестовая версия без команд и истории.
            for table in ("edit_version_associations", "edit_version_features", "edit_versions"):
                column = "id" if table == "edit_versions" else "edit_version_id"
                await connection.execute(
                    text(
                        f"""
                        DELETE FROM work_order.{table}
                        WHERE {column} = :edit_version_id
                        """
                    ),
                    ids,
                )
            await connection.execute(
                text(
                    """
                    UPDATE work_order.work_orders
                    SET status = 'assigned'
                    WHERE id = :work_order_id
                    """
                ),
                ids,
            )
        app = build_workspace_api(engine)
        async with client_for(
            app,
            ids,
        ) as client:
            opened = await client.post(f"/api/v1/work-orders/{ids['work_order_id']}/edit-versions")
            assert opened.status_code == 201, opened.text
            ids["edit_version_id"] = opened.json()["editVersion"]["id"]
            initial = await read_workspace(
                client,
                ids,
            )
            assert (
                initial["draftVersionToken"],
                initial["hasPersistedChangeSet"],
                initial["basicValidation"],
                initial["changeSet"],
            ) == ("1", False, None, None)
            before = await snapshot(
                engine,
                ids,
            )
            saved = await client.put(
                geometry_path(ids),
                json=body(),
            )
            assert saved.status_code == 200, saved.text
            GeometrySaveResponseOut.model_validate(saved.json())
        async with client_for(
            build_workspace_api(engine),
            ids,
        ) as client:
            workspace = await read_workspace(
                client,
                ids,
            )
            assert workspace["draftVersionToken"] == saved.json()["draftVersionToken"] == "2"
            assert (
                current_geometry(
                    workspace,
                    ids,
                )
                == saved.json()["updatedFeature"]["geometry"]
            )
            assert workspace["basicValidation"] == saved.json()["basicValidation"]
            assert workspace["changeSet"] == {
                "featureId": str(ids["feature_id"]),
                "vertexIndex": 1,
                "baselineGeometry": geometry_to_geojson(BASELINE),
                "operation": "updated",
            }
            no_op = await client.put(
                geometry_path(ids),
                json=body(
                    MOVED,
                    "2",
                ),
            )
            assert no_op.status_code == 200, no_op.text
            assert no_op.json()["draftVersionToken"] == "2"
            assert (
                await read_workspace(
                    client,
                    ids,
                )
                == workspace
            )
            reverted = await client.put(
                geometry_path(ids),
                json=body(
                    BASELINE,
                    "2",
                ),
            )
            assert reverted.status_code == 200, reverted.text
            clean = await read_workspace(
                client,
                ids,
            )
            assert (
                clean["draftVersionToken"],
                clean["hasPersistedChangeSet"],
                clean["basicValidation"],
                clean["changeSet"],
            ) == ("3", False, None, None)
            assert current_geometry(
                clean,
                ids,
            ) == geometry_to_geojson(BASELINE)
        after = await snapshot(
            engine,
            ids,
        )
        assert len(after["events"]) == 2
        assert len(after["commands"]) == 3
        for key in ("baseline_root", "baseline", "baseline_associations"):
            assert after[key] == before[key]

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "invalid_geometry",
    [
        {
            "type": "LineString",
            "coordinates": [[1, 1]],
        },
        {
            "type": "MultiLineString",
            "coordinates": [[[1, 1], [2, 2]]],
        },
    ],
)
def test_http_format_failure_does_not_reserve_id(invalid_geometry):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        async with client_for(
            build_workspace_api(engine),
            ids,
        ) as client:
            request = body()
            invalid = await client.put(
                geometry_path(ids),
                json={
                    **request,
                    "geometry": invalid_geometry,
                },
            )
            assert_error(
                invalid,
                422,
                "REQUEST_VALIDATION_ERROR",
            )
            assert (
                await snapshot(
                    engine,
                    ids,
                )
            )["commands"] == []
            corrected = await client.put(
                geometry_path(ids),
                json=request,
            )
            assert corrected.status_code == 200, corrected.text
            short = body(
                replace(
                    BASELINE,
                    coordinates=(BASELINE.coordinates[0], BASELINE.coordinates[-1]),
                ),
                "2",
            )
            rejected = await client.put(
                geometry_path(ids),
                json=short,
            )
            assert_error(
                rejected,
                422,
                "GEOMETRY_STRUCTURE_CHANGED",
            )
            state = await snapshot(
                engine,
                ids,
            )
            assert len(state["commands"]) == 2
            assert len(state["events"]) == 1
            reused = await client.put(
                geometry_path(ids),
                json={
                    **short,
                    "geometry": geometry_to_geojson(MOVED),
                },
            )
            assert_error(
                reused,
                409,
                "COMMAND_ID_REUSED",
            )

    run_committed_scenario(scenario)


def test_http_stale_and_old_replay():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
        async with client_for(
            build_workspace_api(engine),
            ids,
        ) as client:
            request_a = body()
            saved_a = await client.put(
                geometry_path(ids),
                json=request_a,
            )
            assert saved_a.status_code == 200, saved_a.text
            moved_b = replace(
                MOVED,
                coordinates=(
                    MOVED.coordinates[0],
                    (Decimal("65.525"), Decimal("44.822")),
                    MOVED.coordinates[-1],
                ),
            )
            saved_b = await client.put(
                geometry_path(ids),
                json=body(
                    moved_b,
                    "2",
                ),
            )
            assert saved_b.status_code == 200, saved_b.text
            before = await snapshot(
                engine,
                ids,
            )
            replay = await client.put(
                geometry_path(ids),
                json=request_a,
            )
            assert replay.json() == saved_a.json()
            workspace = await read_workspace(
                client,
                ids,
            )
            assert workspace["draftVersionToken"] == "3"
            assert current_geometry(
                workspace,
                ids,
            ) == geometry_to_geojson(moved_b)
            stale_body = body(
                BASELINE,
                "1",
            )
            stale = await client.put(
                geometry_path(ids),
                json=stale_body,
            )
            assert_error(
                stale,
                409,
                "DRAFT_VERSION_STALE",
            )
            stale_retry = await client.put(
                geometry_path(ids),
                json=stale_body,
            )
            assert_error(
                stale_retry,
                409,
                "DRAFT_VERSION_STALE",
            )
            after = await snapshot(
                engine,
                ids,
            )
            for key in ("root", "features", "events", "baseline"):
                assert after[key] == before[key]
            assert len(after["commands"]) == 3

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "case,status,code",
    [
        ("anonymous", 401, "AUTH_REQUIRED"),
        ("reviewer", 403, "ROLE_NOT_ALLOWED"),
        ("inactive", 403, "USER_INACTIVE"),
        ("foreign", 404, "EDIT_VERSION_NOT_FOUND"),
        ("mismatch", 404, "EDIT_VERSION_NOT_FOUND"),
        ("closed", 409, "EDIT_VERSION_STATE_CONFLICT"),
    ],
)
def test_http_current_authorization(
    case,
    status,
    code,
):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            if case == "reviewer":
                await connection.execute(
                    text(
                        """
                        UPDATE "user".users
                        SET role = 'reviewer'
                        WHERE id = :actor_user_id
                        """
                    ),
                    ids,
                )
            elif case == "inactive":
                await connection.execute(
                    text(
                        """
                        UPDATE "user".users
                        SET is_active = false
                        WHERE id = :actor_user_id
                        """
                    ),
                    ids,
                )
            elif case == "foreign":
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
            elif case == "closed":
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.work_orders
                        SET status = 'assigned'
                        WHERE id = :work_order_id
                        """
                    ),
                    ids,
                )
        path_ids = (
            {
                **ids,
                "work_order_id": uuid4(),
            }
            if case == "mismatch"
            else ids
        )
        async with client_for(
            build_workspace_api(engine),
            ids,
            authenticated=case != "anonymous",
        ) as client:
            assert_error(
                await client.put(
                    geometry_path(path_ids),
                    json=body(),
                ),
                status,
                "SAVE_CONTEXT_CLOSED" if case == "closed" else code,
            )
            assert_error(
                await client.get(f"{version_path(path_ids)}/workspace"),
                status,
                code,
            )
        state = await snapshot(
            engine,
            ids,
        )
        assert state["events"] == []

    run_committed_scenario(scenario)
