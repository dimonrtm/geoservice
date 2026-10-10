from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    seed_repository_context,
)


def test_context_reads_linked_baseline_without_workspace_filter():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            await connection.execute(
                text(
                    """
                    UPDATE work_order.edit_version_features
                    SET geometry = ST_GeomFromText('LINESTRING(0 0,1 1,2 0)',4326)
                    WHERE edit_version_id = :id
                        AND feature_id = :feature
                    """
                ),
                {
                    "id": ids["edit_version_id"],
                    "feature": ids["feature_id"],
                },
            )
        async with AsyncSession(engine) as session, session.begin():
            repository, context = await read_context(
                session,
                ids,
            )
            assert context.root.default_state_id == ids["default_state_id"]
            assert context.current.feature_id == ids["feature_id"]
            assert context.current.geometry_ewkb != context.baseline.geometry_ewkb
            assert context.other_changed_feature_ids == ()
            assert session.in_transaction()
            assert (
                await repository.lock_version(
                    work_order_id=uuid4(),
                    edit_version_id=ids["edit_version_id"],
                )
                is None
            )
            assert (
                await repository.lock_version(
                    work_order_id=ids["work_order_id"],
                    edit_version_id=uuid4(),
                )
                is None
            )
            missing = await repository.read_context(
                context.root,
                feature_id=uuid4(),
            )
            assert missing.code == "EDIT_VERSION_NOT_FOUND"

    run_committed_scenario(scenario)


def test_missing_baseline_preserves_current_context():
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_repository_context(connection)
            await connection.execute(
                text("UPDATE work_order.edit_versions SET default_state_id=:missing WHERE id=:id"),
                {
                    "missing": uuid4(),
                    "id": ids["edit_version_id"],
                },
            )
        async with AsyncSession(engine) as session, session.begin():
            _, context = await read_context(
                session,
                ids,
            )
            assert context.current.feature_id == ids["feature_id"]
            assert context.baseline is None
            assert context.default_state is None

    run_committed_scenario(scenario)
