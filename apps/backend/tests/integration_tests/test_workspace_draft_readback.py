from uuid import uuid4

import pytest
from sqlalchemy import text
from tests.integration_tests.workspace_api_support import (
    build_workspace_api,
    client_for,
    version_path,
)

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import seed_save_context


def test_readback_pairs_include_hidden_features_and_version_baseline():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            unrelated = await seed_save_context(connection)
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET geometry = ST_GeomFromText('POINT(0 0)', 4326)
                    WHERE edit_version_id = :edit_version_id AND feature_id = :junction_id
                """
                ),
                ids,
            )
        app = build_workspace_api(engine)
        async with client_for(app, ids) as reader:
            path = version_path(ids)
            response = await reader.get(path)
            assert response.status_code == 200, response.text
            version = response.json()["workOrder"]["editVersion"]
            assert version["draftVersionToken"] == "1"
            assert "changeSet" not in version
            assert len(version["features"]["features"]) == 1
            assert version["associations"] == []
            assert (await reader.get(f"{path}/change-set")).status_code == 422
            baseline = await reader.get(f"{path}/features/{ids['feature_id']}/baseline")
            assert baseline.status_code == 200
            assert baseline.json()["featureId"] == str(ids["feature_id"])
            foreign = await reader.get(f"{path}/features/{unrelated['feature_id']}/baseline")
            assert foreign.status_code == 404
            async with engine.begin() as connection:
                await connection.execute(
                    text(
                        """
                        UPDATE work_order.edit_version_features
                        SET geometry = ST_Translate(geometry, -50, 0)
                        WHERE edit_version_id = :edit_version_id AND feature_id = :feature_id
                    """
                    ),
                    ids,
                )
            hidden = await reader.get(f"{path}/features/{ids['feature_id']}/baseline")
            assert hidden.status_code == 404

    run_committed_scenario(scenario)


@pytest.mark.parametrize("baseline_source", ["missing", "foreign"])
def test_map_remains_available_when_pinned_baseline_is_invalid(baseline_source):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            unrelated = await seed_save_context(connection)
            await connection.execute(
                text(
                    "UPDATE work_order.edit_versions SET default_state_id = :baseline WHERE id = :version"
                ),
                {
                    "baseline": (
                        unrelated["default_state_id"] if baseline_source == "foreign" else uuid4()
                    ),
                    "version": ids["edit_version_id"],
                },
            )
        async with client_for(build_workspace_api(engine), ids) as reader:
            path = version_path(ids)
            version_map = await reader.get(path)
            assert version_map.status_code == 200
            assert version_map.json()["workOrder"]["editVersion"]["features"]["features"]
            for suffix in ("/change-set", f"/features/{ids['feature_id']}/baseline"):
                response = await reader.get(path + suffix)
                assert response.status_code == 422
                assert response.json()["code"] == "WORKSPACE_CONTEXT_INVALID"

    run_committed_scenario(scenario)
