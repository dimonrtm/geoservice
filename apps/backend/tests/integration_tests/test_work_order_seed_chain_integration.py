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
    DefaultState,
    DefaultStateAssociation,
    DefaultStateFeature,
    Feeder,
    NetworkAssociation,
    NetworkFeature,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    EditVersionAssociation,
    EditVersionFeature,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService


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
        assignee = await session.get(User, work_order.assignee_user_id)
        feeder = await session.get(Feeder, UTILITY_DATASET_SPEC.feeder.id)
        aoi = await session.get(AOI, UTILITY_DATASET_SPEC.aoi.id)
        default_state = await session.scalar(
            select(DefaultState).where(DefaultState.work_order_id == work_order.id)
        )
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
        assert default_state is not None
        default_state_feature_count = await session.scalar(
            select(func.count(DefaultStateFeature.feature_id)).where(
                DefaultStateFeature.default_state_id == default_state.id
            )
        )
        default_state_association_count = await session.scalar(
            select(func.count(DefaultStateAssociation.association_id)).where(
                DefaultStateAssociation.default_state_id == default_state.id
            )
        )
        default_state_aggregate = await DefaultStateRepository(
            session
        ).get_active_aggregate_by_work_order_id(work_order.id)

        assert work_order_count == 1
        assert work_order.id == SEED_WORK_ORDER_SPEC.id
        assert work_order.status is WorkOrderStatus.ASSIGNED
        assert assignee is not None
        assert assignee.email == SEED_WORK_ORDER_SPEC.assignee_email
        assert assignee.role is UserRole.EDITOR
        assert assignee.is_active is True
        assert reviewer is not None
        assert reviewer.role is UserRole.REVIEWER
        assert reviewer.id != work_order.assignee_user_id
        assert feeder is not None
        assert feeder.code == UTILITY_FEEDER_CODE
        assert aoi is not None
        assert network_feature_count == 19
        assert default_state.base_network_revision == 1
        assert default_state_feature_count == 19
        assert default_state_association_count == 9
        assert default_state_aggregate is not None
        assert default_state_aggregate.state.id == default_state.id
        assert len(default_state_aggregate.features) == 19
        assert len(default_state_aggregate.associations) == 9

    run_in_rollback_transaction(scenario)


def test_repeated_seed_chain_preserves_existing_work_order_state() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

        work_order = await load_work_order(session)
        work_order.title = "Измененная задача интеграционного дня"
        work_order.status = WorkOrderStatus.IN_PROGRESS
        original_assignee_user_id = work_order.assignee_user_id
        await session.commit()

        await run_seed_chain(session)

        refreshed = await load_work_order(session)
        work_order_count = await session.scalar(
            select(func.count(WorkOrder.id)).where(WorkOrder.code == SEED_WORK_ORDER_SPEC.code)
        )

        assert work_order_count == 1
        assert refreshed.title == "Измененная задача интеграционного дня"
        assert refreshed.status is WorkOrderStatus.IN_PROGRESS
        assert refreshed.assignee_user_id == original_assignee_user_id

    run_in_rollback_transaction(scenario)


def test_seed_chain_opens_edit_version_with_full_default_state_slice() -> None:
    async def scenario(session: AsyncSession) -> None:
        await remove_canonical_seed_chain(session)
        await run_seed_chain(session)

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

        edit_feature_count = await session.scalar(
            select(func.count(EditVersionFeature.feature_id)).where(
                EditVersionFeature.edit_version_id == result.edit_version.id
            )
        )
        edit_association_count = await session.scalar(
            select(func.count(EditVersionAssociation.association_id)).where(
                EditVersionAssociation.edit_version_id == result.edit_version.id
            )
        )

        assert result.created is True
        assert edit_feature_count == 19
        assert edit_association_count == 9

    run_in_rollback_transaction(scenario)
