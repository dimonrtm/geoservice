from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest
from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.contracts.demo_fixture_upgrade import (
    DemoFixtureGeometryUpdate,
    DemoFixtureHierarchy,
    DemoFixtureUpgradeError,
)
from seeds.repositories.demo_fixture_upgrade_repository import (
    DemoFixtureUpgradeRepository,
)
from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.services.demo_fixture_upgrade_service import DemoFixtureUpgradeService
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.services.seed_work_order_service import SeedWorkOrderService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_EDITABLE_LINE_ASSET_CODE,
    UTILITY_EDITABLE_LINE_SPEC,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_AOI_SPEC, SEED_WORK_ORDER_SPEC
from tests.integration_tests.network_db_support import run_in_rollback_transaction
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.models.utility_network import (
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
    NetworkState,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    AOI,
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    WorkOrder,
)
from utility_service.infrastructure.postgresql.models.work_order.edit_version_feature import (
    EditVersionOperationState,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService


OLD_TWO_VERTEX_WKT = "LINESTRING (65.520 44.820, 65.530 44.820)"


@dataclass(frozen=True)
class MaterializedOwnerIds:
    feeder_id: UUID
    default_state_id: UUID
    edit_version_id: UUID


class FailOnSecondUpdateRepository:
    def __init__(self, delegate: DemoFixtureUpgradeRepository) -> None:
        self._delegate = delegate
        self.update_attempts = 0

    async def load_hierarchy_for_update(self) -> DemoFixtureHierarchy:
        return await self._delegate.load_hierarchy_for_update()

    async def update_geometry(self, update_request: DemoFixtureGeometryUpdate) -> None:
        self.update_attempts += 1
        if self.update_attempts == 2:
            raise RuntimeError("synthetic write failure")
        await self._delegate.update_geometry(update_request)


async def remove_canonical_seed_chain(session: AsyncSession) -> None:
    await session.execute(
        delete(EditVersion).where(EditVersion.work_order_id == SEED_WORK_ORDER_SPEC.id)
    )
    await session.execute(
        delete(DefaultState).where(DefaultState.work_order_id == SEED_WORK_ORDER_SPEC.id)
    )
    await session.execute(delete(WorkOrder).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code))
    await session.execute(
        delete(NetworkAssociation).where(
            NetworkAssociation.feeder_id == UTILITY_DATASET_SPEC.feeder.id
        )
    )
    await session.execute(
        delete(NetworkFeature).where(NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id)
    )
    await session.execute(delete(Feeder).where(Feeder.id == UTILITY_DATASET_SPEC.feeder.id))
    await session.execute(delete(AOI).where(AOI.id == SEED_WORK_ORDER_AOI_SPEC.id))
    await session.execute(
        delete(User).where(User.email.in_([spec.email for spec in SEED_DEMO_USER_SPECS]))
    )
    await session.commit()


async def run_seed_chain(session: AsyncSession) -> None:
    await SeedDemoUserService(
        session,
        SeedUserRepository(session),
    ).ensure_demo_users()
    await SeedUtilityDatasetService(
        session,
        SeedUtilityDatasetRepository(session),
    ).ensure_utility_dataset()
    await SeedWorkOrderService(
        session,
        SeedWorkOrderRepository(session),
        SeedUserRepository(session),
        SeedUtilityDatasetRepository(session),
    ).ensure_work_order()


async def open_edit_version(session: AsyncSession) -> MaterializedOwnerIds:
    assignee_id = next(
        spec.id
        for spec in SEED_DEMO_USER_SPECS
        if spec.email == SEED_WORK_ORDER_SPEC.assignee_email
    )
    result = await EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        DefaultStateRepository(session),
    ).open_for_work_order(SEED_WORK_ORDER_SPEC.id, assignee_id)
    default_state_id = await session.scalar(
        select(DefaultState.id).where(DefaultState.work_order_id == SEED_WORK_ORDER_SPEC.id)
    )
    assert default_state_id is not None
    await session.commit()
    return MaterializedOwnerIds(
        feeder_id=UTILITY_DATASET_SPEC.feeder.id,
        default_state_id=default_state_id,
        edit_version_id=result.edit_version.id,
    )


async def set_all_l003_geometries(
    session: AsyncSession,
    owners: MaterializedOwnerIds,
    *,
    edit_operation: EditVersionOperationState = EditVersionOperationState.UNCHANGED,
) -> None:
    geometry = WKTElement(OLD_TWO_VERTEX_WKT, srid=4326)
    await session.execute(
        update(NetworkFeature)
        .where(
            NetworkFeature.feeder_id == owners.feeder_id,
            NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
        .values(geometry=geometry)
    )
    await session.execute(
        update(DefaultStateFeature)
        .where(
            DefaultStateFeature.default_state_id == owners.default_state_id,
            DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
        .values(geometry=geometry)
    )
    await session.execute(
        update(EditVersionFeature)
        .where(
            EditVersionFeature.edit_version_id == owners.edit_version_id,
            EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
        .values(geometry=geometry, operation=edit_operation)
    )
    await session.commit()


async def vertex_counts(
    session: AsyncSession,
    owners: MaterializedOwnerIds,
) -> tuple[int, int, int]:
    network_count = await session.scalar(
        select(func.ST_NPoints(NetworkFeature.geometry)).where(
            NetworkFeature.feeder_id == owners.feeder_id,
            NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    default_count = await session.scalar(
        select(func.ST_NPoints(DefaultStateFeature.geometry)).where(
            DefaultStateFeature.default_state_id == owners.default_state_id,
            DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    edit_count = await session.scalar(
        select(func.ST_NPoints(EditVersionFeature.geometry)).where(
            EditVersionFeature.edit_version_id == owners.edit_version_id,
            EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    assert network_count is not None
    assert default_count is not None
    assert edit_count is not None
    return network_count, default_count, edit_count


async def metadata_snapshot(
    session: AsyncSession,
    owners: MaterializedOwnerIds,
) -> dict[str, Any]:
    network = (
        await session.execute(
            select(
                NetworkFeature.id,
                NetworkFeature.properties,
                NetworkFeature.version,
            ).where(
                NetworkFeature.feeder_id == owners.feeder_id,
                NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
    ).one()
    default = (
        await session.execute(
            select(
                DefaultStateFeature.feature_id,
                DefaultStateFeature.properties,
                DefaultStateFeature.network_version,
            ).where(
                DefaultStateFeature.default_state_id == owners.default_state_id,
                DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
    ).one()
    edit = (
        await session.execute(
            select(
                EditVersionFeature.feature_id,
                EditVersionFeature.properties,
                EditVersionFeature.network_version,
                EditVersionFeature.operation,
            ).where(
                EditVersionFeature.edit_version_id == owners.edit_version_id,
                EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
    ).one()
    network_state_id = await session.scalar(
        select(DefaultState.network_state_id).where(DefaultState.id == owners.default_state_id)
    )
    current_revision = await session.scalar(
        select(NetworkState.current_revision).where(NetworkState.id == network_state_id)
    )
    return {
        "network": tuple(network),
        "default": tuple(default),
        "edit": tuple(edit),
        "current_revision": current_revision,
    }


async def assert_geometry_matches_seed(
    session: AsyncSession,
    owners: MaterializedOwnerIds,
) -> None:
    expected = WKTElement(UTILITY_EDITABLE_LINE_SPEC.geometry_wkt, srid=4326)
    network_matches = await session.scalar(
        select(func.ST_Equals(NetworkFeature.geometry, expected)).where(
            NetworkFeature.feeder_id == owners.feeder_id,
            NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    default_matches = await session.scalar(
        select(func.ST_Equals(DefaultStateFeature.geometry, expected)).where(
            DefaultStateFeature.default_state_id == owners.default_state_id,
            DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    edit_matches = await session.scalar(
        select(func.ST_Equals(EditVersionFeature.geometry, expected)).where(
            EditVersionFeature.edit_version_id == owners.edit_version_id,
            EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
        )
    )
    assert (network_matches, default_matches, edit_matches) == (True, True, True)


async def assert_materialized_counts(
    session: AsyncSession,
    owners: MaterializedOwnerIds,
) -> None:
    counts = (
        await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == owners.feeder_id
            )
        ),
        await session.scalar(
            select(func.count(NetworkAssociation.id)).where(
                NetworkAssociation.feeder_id == owners.feeder_id
            )
        ),
        await session.scalar(
            select(func.count(DefaultStateFeature.feature_id)).where(
                DefaultStateFeature.default_state_id == owners.default_state_id
            )
        ),
        await session.scalar(
            select(func.count(DefaultStateAssociation.association_id)).where(
                DefaultStateAssociation.default_state_id == owners.default_state_id
            )
        ),
        await session.scalar(
            select(func.count(EditVersionFeature.feature_id)).where(
                EditVersionFeature.edit_version_id == owners.edit_version_id
            )
        ),
        await session.scalar(
            select(func.count(EditVersionAssociation.association_id)).where(
                EditVersionAssociation.edit_version_id == owners.edit_version_id
            )
        ),
    )
    assert counts == (19, 9, 19, 9, 19, 9)


def test_fresh_seed_chain_is_valid_no_op_without_edit_version() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        result = await DemoFixtureUpgradeService(
            session,
            DemoFixtureUpgradeRepository(session),
        ).upgrade_demo_fixture()

        default_state_id = await session.scalar(
            select(DefaultState.id).where(DefaultState.work_order_id == SEED_WORK_ORDER_SPEC.id)
        )
        assert default_state_id is not None
        feeder_vertices = await session.scalar(
            select(func.ST_NPoints(NetworkFeature.geometry)).where(
                NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id,
                NetworkFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
        default_vertices = await session.scalar(
            select(func.ST_NPoints(DefaultStateFeature.geometry)).where(
                DefaultStateFeature.default_state_id == default_state_id,
                DefaultStateFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
        assert result.updated_copy_count == 0
        assert (feeder_vertices, default_vertices) == (3, 3)

    run_in_rollback_transaction(scenario)


def test_upgrades_three_materialized_copies_and_is_idempotent() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)
        owners = await open_edit_version(session)
        await set_all_l003_geometries(session, owners)
        before = await metadata_snapshot(session, owners)
        await session.commit()

        service = DemoFixtureUpgradeService(
            session,
            DemoFixtureUpgradeRepository(session),
        )
        first = await service.upgrade_demo_fixture()
        second = await service.upgrade_demo_fixture()

        after = await metadata_snapshot(session, owners)
        assert first.updated_copy_count == 3
        assert second.updated_copy_count == 0
        assert await vertex_counts(session, owners) == (3, 3, 3)
        await assert_geometry_matches_seed(session, owners)
        await assert_materialized_counts(session, owners)
        assert after == before

    run_in_rollback_transaction(scenario)


def test_changed_two_vertex_edit_rejects_before_any_write() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)
        owners = await open_edit_version(session)
        await set_all_l003_geometries(
            session,
            owners,
            edit_operation=EditVersionOperationState.UPDATED,
        )

        with pytest.raises(DemoFixtureUpgradeError, match="operation"):
            await DemoFixtureUpgradeService(
                session,
                DemoFixtureUpgradeRepository(session),
            ).upgrade_demo_fixture()

        assert await vertex_counts(session, owners) == (2, 2, 2)
        operation = await session.scalar(
            select(EditVersionFeature.operation).where(
                EditVersionFeature.edit_version_id == owners.edit_version_id,
                EditVersionFeature.asset_code == UTILITY_EDITABLE_LINE_ASSET_CODE,
            )
        )
        assert operation is EditVersionOperationState.UPDATED
        await assert_materialized_counts(session, owners)

    run_in_rollback_transaction(scenario)


def test_rolls_back_first_database_write_when_second_write_fails() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)
        owners = await open_edit_version(session)
        await set_all_l003_geometries(session, owners)
        repository = FailOnSecondUpdateRepository(DemoFixtureUpgradeRepository(session))

        with pytest.raises(RuntimeError, match="synthetic write failure"):
            await DemoFixtureUpgradeService(session, repository).upgrade_demo_fixture()

        assert repository.update_attempts == 2
        assert await vertex_counts(session, owners) == (2, 2, 2)

    run_in_rollback_transaction(scenario)
