from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
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


OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT = "uq_edit_versions_open_work_order"
POSTGRES_UNIQUE_VIOLATION = "23505"


class EditVersionService:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        work_order_repository: WorkOrderRepository,
        default_state_repository: DefaultStateRepository,
    ):
        self.session = session
        self.user_repository = user_repository
        self.work_order_repository = work_order_repository
        self.default_state_repository = default_state_repository

    async def open_for_work_order(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        try:
            return await self.open_for_work_order_locked(work_order_id, actor_id)
        except IntegrityError as exc:
            if not self.is_open_edit_version_unique_violation(exc):
                raise
            return await self.recover_existing_open_edit_version(work_order_id, actor_id)

    async def open_for_work_order_locked(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            return await self.open_visible_work_order(work_order, actor)

    async def open_visible_work_order(
        self,
        work_order: WorkOrder,
        actor: User,
    ) -> OpenEditVersionResult:
        existing = await self.work_order_repository.get_open_edit_version(work_order.id)

        if work_order.status is WorkOrderStatus.IN_PROGRESS:
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

        if work_order.status is not WorkOrderStatus.ASSIGNED:
            raise WorkOrderApiError(
                409,
                "WORK_ORDER_STATE_CONFLICT",
                "Состояние рабочей задачи не допускает операцию.",
            )

        if existing is not None:
            self.raise_context_invalid()

        default_state_aggregate = (
            await self.default_state_repository.get_active_aggregate_by_work_order_id(work_order.id)
        )
        if default_state_aggregate is None:
            self.raise_context_invalid()

        default_state = default_state_aggregate.state
        created = await self.work_order_repository.create_open_edit_version(
            work_order_id=work_order.id,
            default_state_id=default_state.id,
            base_network_revision=default_state.base_network_revision,
            default_features=default_state_aggregate.features,
            default_associations=default_state_aggregate.associations,
            owner_user_id=actor.id,
        )
        work_order.status = WorkOrderStatus.IN_PROGRESS
        await self.work_order_repository.save(work_order)
        return OpenEditVersionResult(created=True, edit_version=created)

    async def recover_existing_open_edit_version(
        self,
        work_order_id: UUID,
        actor_id: UUID,
    ) -> OpenEditVersionResult:
        async with self.session.begin():
            actor = await self.get_actor(actor_id)
            work_order = await self.get_visible_work_order(work_order_id, actor)
            existing = await self.work_order_repository.get_open_edit_version(work_order.id)
            if existing is None:
                self.raise_context_invalid()
            return await self.reopen_edit_version(existing)

    async def reopen_edit_version(self, edit_version: EditVersion) -> OpenEditVersionResult:
        await self.work_order_repository.touch_edit_version(edit_version)
        return OpenEditVersionResult(created=False, edit_version=edit_version)

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
        work_order = await self.work_order_repository.get_by_id_for_update(work_order_id)
        if work_order is None or work_order.assignee_user_id != actor.id:
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

    @staticmethod
    def is_open_edit_version_unique_violation(error: IntegrityError) -> bool:
        original = getattr(error, "orig", None)
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        diag = getattr(original, "diag", None)
        constraint_name = getattr(diag, "constraint_name", None) or getattr(
            original,
            "constraint_name",
            None,
        )
        return sqlstate == POSTGRES_UNIQUE_VIOLATION and (
            constraint_name == OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT
            or OPEN_EDIT_VERSION_UNIQUE_CONSTRAINT in str(error)
        )

    def raise_context_invalid(self) -> None:
        raise WorkOrderApiError(
            422,
            "WORK_ORDER_CONTEXT_INVALID",
            "Контекст рабочей задачи поврежден или неполон.",
        )
