from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_utility_dataset_repository import (
    SeedUtilityDatasetRepository,
)
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.services.seed_utility_dataset_service import SeedUtilityDatasetService
from seeds.services.seed_work_order_service import SeedWorkOrderService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS
from seeds.specs.seed_utility_dataset_specs import (
    UTILITY_DATASET_SPEC,
    UTILITY_FEEDER_CODE,
)
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC
from tests.integration_tests.network_db_support import run_in_rollback_transaction
from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    AOI,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
    WorkOrder,
    WorkOrderStatus,
)


async def remove_canonical_seed_chain(session: AsyncSession) -> None:
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
    await session.execute(delete(AOI).where(AOI.id == UTILITY_DATASET_SPEC.aoi.id))
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


async def load_work_order(session: AsyncSession) -> WorkOrder:
    work_order = await session.scalar(
        select(WorkOrder).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
    )
    assert work_order is not None
    return work_order


def test_seed_chain_creates_work_order_with_user_network_links() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)

        await run_seed_chain(session)

        work_order = await load_work_order(session)
        assignee = await session.get(User, work_order.assignee_id)
        feeder = await session.get(Feeder, work_order.feeder_id)
        aoi = await session.get(AOI, work_order.aoi_id)
        reviewer = await session.scalar(
            select(User).where(User.email == "marina.reviewer@example.local")
        )
        work_order_count = await session.scalar(
            select(func.count(WorkOrder.id)).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
        )
        network_feature_count = await session.scalar(
            select(func.count(NetworkFeature.id)).where(
                NetworkFeature.feeder_id == UTILITY_DATASET_SPEC.feeder.id
            )
        )

        assert work_order_count == 1
        assert work_order.id == SEED_WORK_ORDER_SPEC.id
        assert work_order.status is WorkOrderStatus.ASSIGNED
        assert assignee is not None
        assert assignee.email == SEED_WORK_ORDER_SPEC.assignee_email
        assert assignee.role is UserRole.EDITOR
        assert assignee.is_active is True
        assert reviewer is not None
        assert reviewer.role is UserRole.REVIEWER
        assert reviewer.id != work_order.assignee_id
        assert feeder is not None
        assert feeder.code == UTILITY_FEEDER_CODE
        assert aoi is not None
        assert network_feature_count == 19

    run_in_rollback_transaction(scenario)


def test_repeated_seed_chain_preserves_existing_work_order_state() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        work_order = await load_work_order(session)
        work_order.title = "Измененная задача интеграционного дня"
        work_order.status = WorkOrderStatus.IN_PROGRESS
        original_assignee_id = work_order.assignee_id
        original_aoi_id = work_order.aoi_id
        original_feeder_id = work_order.feeder_id
        await session.commit()

        await run_seed_chain(session)

        refreshed = await load_work_order(session)
        work_order_count = await session.scalar(
            select(func.count(WorkOrder.id)).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
        )

        assert work_order_count == 1
        assert refreshed.title == "Измененная задача интеграционного дня"
        assert refreshed.status is WorkOrderStatus.IN_PROGRESS
        assert refreshed.assignee_id == original_assignee_id
        assert refreshed.aoi_id == original_aoi_id
        assert refreshed.feeder_id == original_feeder_id

    run_in_rollback_transaction(scenario)
