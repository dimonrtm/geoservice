from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    WorkOrder,
)
from seeds.specs.seed_work_order_specs import SeedWorkOrderSpec


class SeedWorkOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_work_order_by_code(self, code: str) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.code == code))
        return result.scalars().one_or_none()

    async def create_work_order(
        self,
        spec: SeedWorkOrderSpec,
        *,
        assignee_id: UUID,
        feeder_id: UUID,
        aoi_id: UUID,
    ) -> WorkOrder:
        work_order = WorkOrder(
            id=spec.id,
            code=spec.code,
            title=spec.title,
            description=spec.description,
            status=spec.status,
            assignee_id=assignee_id,
            feeder_id=feeder_id,
            aoi_id=aoi_id,
        )
        self.session.add(work_order)
        await self.session.flush()
        return work_order
