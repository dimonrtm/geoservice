import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from seeds.repositories.seed_utility_dataset_repository import SeedUtilityDatasetRepository
from seeds.repositories.seed_user_repository import SeedUserRepository
from seeds.repositories.seed_work_order_repository import SeedWorkOrderRepository
from seeds.specs.seed_work_order_specs import SEED_WORK_ORDER_SPEC


logger = logging.getLogger(__name__)


class SeedWorkOrderDependencyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SeedWorkOrderResult:
    work_order_id: UUID
    created: bool


class SeedWorkOrderService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SeedWorkOrderRepository,
        user_repository: SeedUserRepository,
        utility_dataset_repository: SeedUtilityDatasetRepository,
    ):
        self.session = session
        self.repository = repository
        self.user_repository = user_repository
        self.utility_dataset_repository = utility_dataset_repository

    async def ensure_work_order(self) -> SeedWorkOrderResult:
        async with self.session.begin():
            existing = await self.repository.get_work_order_by_code(SEED_WORK_ORDER_SPEC.code)
            if existing is not None:
                logger.info(
                    "WorkOrder уже существует; startup seed не изменяет задачу.",
                    extra={
                        "work_order_id": str(existing.id),
                        "work_order_code": existing.code,
                    },
                )
                return SeedWorkOrderResult(
                    work_order_id=existing.id,
                    created=False,
                )

            assignee = await self.user_repository.get_by_email(SEED_WORK_ORDER_SPEC.assignee_email)
            if assignee is None:
                raise SeedWorkOrderDependencyError(
                    f"Не найден assignee для seed WorkOrder: "
                    f"{SEED_WORK_ORDER_SPEC.assignee_email}"
                )

            feeder = await self.utility_dataset_repository.get_feeder_by_code(
                SEED_WORK_ORDER_SPEC.feeder_code
            )
            if feeder is None:
                raise SeedWorkOrderDependencyError(
                    f"Не найден feeder для seed WorkOrder: {SEED_WORK_ORDER_SPEC.feeder_code}"
                )

            aoi = await self.utility_dataset_repository.get_first_aoi()
            if aoi is None:
                raise SeedWorkOrderDependencyError("Не найден AOI для seed WorkOrder.")

            work_order = await self.repository.create_work_order(
                SEED_WORK_ORDER_SPEC,
                assignee_id=assignee.id,
                feeder_id=feeder.id,
                aoi_id=aoi.id,
            )
            logger.info(
                "Seed WorkOrder создан.",
                extra={
                    "work_order_id": str(work_order.id),
                    "work_order_code": work_order.code,
                },
            )
            return SeedWorkOrderResult(work_order_id=work_order.id, created=True)


async def run_seed_work_orders() -> SeedWorkOrderResult:
    from utility_service.infrastructure.postgresql.session import SessionFactory

    async with SessionFactory() as session:
        service = SeedWorkOrderService(
            session,
            SeedWorkOrderRepository(session),
            SeedUserRepository(session),
            SeedUtilityDatasetRepository(session),
        )
        return await service.ensure_work_order()
