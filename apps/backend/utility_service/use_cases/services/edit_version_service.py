from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError


@dataclass(frozen=True)
class OpenEditVersionResult:
    created: bool
    edit_version: EditVersion


class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        edit_version_repository: EditVersionRepository,
        default_state_repository: DefaultStateRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.edit_version_repository = edit_version_repository
        self.default_state_repository = default_state_repository

    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            existing = await self.edit_version_repository.get_open_by_work_order_id(work_order.id)

            if work_order.status is WorkOrderStatus.IN_PROGRESS:
                if existing is None:
                    self.raise_context_invalid()
                await self.edit_version_repository.touch_last_opened(existing)
                return OpenEditVersionResult(created=False, edit_version=existing)

            if work_order.status is not WorkOrderStatus.ASSIGNED:
                raise WorkOrderApiError(
                    409,
                    "WORK_ORDER_STATE_CONFLICT",
                    "Состояние рабочей задачи не допускает операцию.",
                )

            if existing is not None:
                self.raise_context_invalid()

            default_state = await self.default_state_repository.get_default()
            if default_state is None:
                self.raise_context_invalid()

            created = await self.edit_version_repository.create_open(
                work_order_id=work_order.id,
                owner_id=actor.id,
                base_revision=default_state.current_revision,
            )
            work_order.status = WorkOrderStatus.IN_PROGRESS
            await self.work_order_repository.save(work_order)
            return OpenEditVersionResult(created=True, edit_version=created)

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

    async def get_visible_work_order(self, work_order_id: UUID, actor: User) -> WorkOrder:
        work_order = await self.work_order_repository.get_by_id(work_order_id)
        if work_order is None or work_order.assignee_id != actor.id:
            raise WorkOrderApiError(
                404,
                "WORK_ORDER_NOT_FOUND",
                "Рабочая задача не найдена.",
            )
        return work_order

    def require_active_editor(self, actor: User) -> None:
        if actor.role is not UserRole.EDITOR or not actor.is_active:
            raise WorkOrderApiError(
                403,
                "ROLE_NOT_ALLOWED",
                "Роль пользователя не допускает операцию.",
            )

    def raise_context_invalid(self) -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )
