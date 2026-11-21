from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from utility_service.use_cases.services.open_edit_version_port import (
    OpenEditVersionOperations,
    OpenEditVersionTransactions,
    OpenVersionRecord,
    OpenWorkOrder,
)
from utility_service.use_cases.domain.exceptions.work_order_operation_error import (
    WorkOrderOperationCode,
    WorkOrderOperationError,
)


@dataclass(frozen=True)
class OpenEditVersionSnapshot:
    id: UUID
    work_order_id: UUID
    owner_user_id: UUID
    status: Literal["open"]
    base_network_revision: int
    created_at: datetime
    last_opened_at: datetime


@dataclass(frozen=True)
class OpenEditVersionResult:
    created: bool
    edit_version: OpenEditVersionSnapshot


def _snapshot(version: OpenVersionRecord) -> OpenEditVersionSnapshot:
    return OpenEditVersionSnapshot(
        id=version.id,
        work_order_id=version.work_order_id,
        owner_user_id=version.owner_user_id,
        status="open",
        base_network_revision=version.base_network_revision,
        created_at=version.created_at,
        last_opened_at=version.last_opened_at,
    )


def _invalid_context() -> WorkOrderOperationError:
    return WorkOrderOperationError(
        WorkOrderOperationCode.WORK_ORDER_CONTEXT_INVALID,
        "Контекст рабочей задачи поврежден или неполон.",
    )


async def _lock_visible_work_order(
    operations: OpenEditVersionOperations, work_order_id: UUID, actor_id: UUID
) -> OpenWorkOrder:
    actor = await operations.get_actor(actor_id)
    if actor is None:
        raise WorkOrderOperationError(
            WorkOrderOperationCode.WORK_ORDER_ACTOR_NOT_FOUND, "Пользователь не найден."
        )
    if actor.role != "editor" or not actor.is_active:
        raise WorkOrderOperationError(
            WorkOrderOperationCode.ROLE_NOT_ALLOWED, "Роль пользователя не допускает операцию."
        )
    order = await operations.lock_work_order(work_order_id)
    if order is None or order.assignee_user_id != actor_id:
        raise WorkOrderOperationError(
            WorkOrderOperationCode.WORK_ORDER_NOT_FOUND, "Рабочая задача не найдена."
        )
    return order


async def _reopen(
    operations: OpenEditVersionOperations, existing: UUID | None
) -> OpenEditVersionResult:
    if existing is None:
        raise _invalid_context()
    version = await operations.touch_open_version(existing)
    return OpenEditVersionResult(False, _snapshot(version))


class OpenEditVersionService:
    def __init__(self, transactions: OpenEditVersionTransactions):
        self.transactions = transactions

    async def open_for_work_order(
        self, work_order_id: UUID, actor_id: UUID
    ) -> OpenEditVersionResult:
        try:
            async with self.transactions.first_attempt() as operations:
                order = await _lock_visible_work_order(operations, work_order_id, actor_id)
                existing = await operations.find_open_version(work_order_id)
                if order.status == "in_progress":
                    return await _reopen(operations, existing)
                if order.status != "assigned":
                    raise WorkOrderOperationError(
                        WorkOrderOperationCode.WORK_ORDER_STATE_CONFLICT,
                        "Состояние рабочей задачи не допускает операцию.",
                    )
                if existing is not None:
                    raise _invalid_context()
                version = await operations.create_from_active_default(work_order_id, actor_id)
                if version is None:
                    raise _invalid_context()
                await operations.mark_in_progress(work_order_id)
                return OpenEditVersionResult(True, _snapshot(version))
        except self.transactions.open_version_conflict:
            pass

        async with self.transactions.recovery_attempt() as operations:
            await _lock_visible_work_order(operations, work_order_id, actor_id)
            return await _reopen(operations, await operations.find_open_version(work_order_id))
