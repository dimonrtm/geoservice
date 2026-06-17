from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import WorkOrder


class WorkOrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, work_order_id: UUID) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.id == work_order_id))
        return result.scalars().one_or_none()

    async def get_by_code(self, code: str) -> WorkOrder | None:
        result = await self.session.execute(select(WorkOrder).where(WorkOrder.code == code))
        return result.scalars().one_or_none()

    async def list_assigned_to_user(self, user_id: UUID) -> list[WorkOrder]:
        result = await self.session.execute(
            select(WorkOrder)
            .where(WorkOrder.assignee_id == user_id)
            .order_by(WorkOrder.created_at, WorkOrder.code)
        )
        return list(result.scalars().all())

    async def save(self, work_order: WorkOrder) -> None:
        self.session.add(work_order)
        await self.session.flush()
