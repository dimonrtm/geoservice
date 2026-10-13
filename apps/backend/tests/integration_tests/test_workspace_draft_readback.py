from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.save_geometry_support import seed_save_context
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)


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
        async with AsyncSession(engine) as session:
            row = await WorkOrderRepository(session).get_workspace_aggregate(
                work_order_id=ids["work_order_id"],
                edit_version_id=ids["edit_version_id"],
            )
        assert row.edit_version.draft_revision == 1
        assert row.baseline_state.id == ids["default_state_id"]
        assert row.baseline_state.id != unrelated["default_state_id"]
        pairs = {pair.feature_id: pair for pair in row.draft_feature_pairs}
        assert set(pairs) == {ids["feature_id"], ids["junction_id"]}
        assert pairs[ids["junction_id"]].visible is False
        assert (
            pairs[ids["junction_id"]].current_geometry_ewkb
            != pairs[ids["junction_id"]].baseline_geometry_ewkb
        )
        assert (
            pairs[ids["feature_id"]].current_geometry_ewkb
            == pairs[ids["feature_id"]].baseline_geometry_ewkb
        )
        assert len(row.features_data) == 1
        assert row.associations_data == []

    run_committed_scenario(scenario)
