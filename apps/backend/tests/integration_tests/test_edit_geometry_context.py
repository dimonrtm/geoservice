from uuid import uuid4

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.edit_geometry_repository_support import (
    read_context,
    read_locked_context,
    seed_repository_context,
)
from tests.integration_tests.save_geometry_support import (
    call_save,
    request,
    seed_save_context,
    snapshot_save_state,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


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
            repository = EditVersionRepository(session)
            root = await repository.lock_version(
                work_order_id=ids["work_order_id"],
                edit_version_id=ids["edit_version_id"],
            )
            baseline = await DefaultStateRepository(session).read_geometry_baseline(
                default_state_id=root.default_state_id,
                feature_id=ids["feature_id"],
            )
            statements = []

            @event.listens_for(
                engine.sync_engine,
                "before_cursor_execute",
            )
            def record_query(
                connection,
                cursor,
                statement,
                parameters,
                context,
                executemany,
            ):
                statements.append(statement)

            context = await repository.read_context(
                root,
                feature_id=ids["feature_id"],
                baseline=baseline,
            )
            assert context.root.default_state_id == ids["default_state_id"]
            assert context.current.feature_id == ids["feature_id"]
            assert context.current.geometry_ewkb != context.baseline.geometry_ewkb
            assert statements and all("utility_network." not in query for query in statements)
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
            missing = await read_locked_context(
                repository,
                context.root,
                feature_id=uuid4(),
            )
            assert missing.code == "EDIT_VERSION_NOT_FOUND"

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "missing_feature",
    [True, False],
    ids=["missing", "wrong-revision"],
)
def test_invalid_pinned_baseline_prevents_save(missing_feature):
    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_save_context(connection)
            if missing_feature:
                await connection.execute(
                    text(
                        """
                        DELETE FROM utility_network.default_state_associations
                        WHERE default_state_id = :default_state_id
                        """
                    ),
                    ids,
                )
                damage_baseline = """
                    DELETE FROM utility_network.default_state_features
                    WHERE default_state_id = :default_state_id
                        AND feature_id = :feature_id
                """
            else:
                damage_baseline = """
                    UPDATE work_order.edit_versions
                    SET base_network_revision = base_network_revision + 1
                    WHERE id = :edit_version_id
                """
            await connection.execute(
                text(damage_baseline),
                ids,
            )
            before = await snapshot_save_state(
                connection,
                ids,
            )
        with pytest.raises(WorkOrderApiError) as error:
            await call_save(
                engine,
                ids,
                request(),
            )
        assert error.value.code == "WORK_ORDER_CONTEXT_INVALID"
        async with engine.connect() as connection:
            after = await snapshot_save_state(
                connection,
                ids,
            )
        assert after["commands"][0]["state"] == "rejected"
        for key in before.keys() - {"commands"}:
            assert after[key] == before[key]

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
