from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


class WorkOrderService:
    def __init__(
        self,
        session: AsyncSession,
        repository: WorkOrderRepository,
        user_repository: UserRepository,
    ):
        self.session = session
        self.repository = repository
        self.user_repository = user_repository

    async def list_assigned_to_editor(self, actor_id: UUID) -> list[WorkOrder]:
        actor = await self.get_actor(actor_id)
        return await self.repository.list_assigned_to_user(actor.id)

    async def get_assigned_work_order(self, work_order_id: UUID, actor_id: UUID) -> WorkOrder:
        actor = await self.get_actor(actor_id)
        work_order = await self.repository.get_by_id(work_order_id)
        if work_order is None:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        self.require_assigned(work_order, actor)
        return work_order

    async def start_work_order(self, work_order_id: UUID, actor_id: UUID) -> WorkOrder:
        async with self.session.begin():
            work_order = await self.get_assigned_work_order(work_order_id, actor_id)
            if work_order.status is not WorkOrderStatus.ASSIGNED:
                raise WorkOrderApiError(
                    409,
                    "WORK_ORDER_STATE_CONFLICT",
                    "Состояние рабочей задачи не допускает операцию.",
                )
            work_order.status = WorkOrderStatus.IN_PROGRESS
            await self.repository.save(work_order)
            return work_order

    async def get_actor(self, actor_id: UUID) -> User:
        actor = await self.user_repository.get_by_id(actor_id)
        if actor is None:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_ACTOR_NOT_FOUND",
                "Пользователь не найден.",
            )
        self.require_active_editor(actor)
        return actor

    def require_active_editor(self, actor: User) -> None:
        if actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    def require_assigned(self, work_order: WorkOrder, actor: User) -> None:
        if work_order.assignee_user_id != actor.id:
            raise WorkOrderApiError(
                403,
                "WORK_ORDER_NOT_ASSIGNED",
                "Рабочая задача не назначена текущему пользователю.",
            )
