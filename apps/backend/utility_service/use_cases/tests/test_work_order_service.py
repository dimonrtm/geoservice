import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import WorkOrderStatus
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.schemas.work_order import AssignedWorkOrdersOut
from utility_service.use_cases.services.work_order_service import WorkOrderService


def user(role: UserRole = UserRole.EDITOR, *, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), role=role, is_active=is_active)


def work_order(
    assignee_user_id,
    *,
    status: WorkOrderStatus = WorkOrderStatus.ASSIGNED,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        code="WO-001",
        title="Проверка участка",
        description="Описание наряда",
        assignee_user_id=assignee_user_id,
        status=status,
    )


class FakeSession:
    def __init__(self) -> None:
        self.begin_calls = 0
        self.in_transaction = False

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        self.in_transaction = True
        try:
            yield self
        finally:
            self.in_transaction = False


def test_get_assigned_work_order_allows_active_assigned_editor() -> None:
    actor = user()
    assigned = work_order(actor.id)
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    result = asyncio.run(service.get_assigned_work_order(assigned.id, actor.id))

    assert result is assigned
    user_repository.get_by_id.assert_awaited_once_with(actor.id)
    work_order_repository.get_by_id.assert_awaited_once_with(assigned.id)


def test_list_assigned_to_editor_loads_actor_and_returns_assigned_work_orders_out() -> None:
    actor = user()
    assigned = [
        work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS),
        work_order(actor.id, status=WorkOrderStatus.ASSIGNED),
    ]
    work_order_repository = AsyncMock()
    work_order_repository.list_assigned_to_user.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    result = asyncio.run(service.list_assigned_to_editor(actor.id))

    assert isinstance(result, AssignedWorkOrdersOut)
    assert [item.id for item in result.work_orders] == [item.id for item in assigned]
    assert [item.code for item in result.work_orders] == ["WO-001", "WO-001"]
    assert [item.title for item in result.work_orders] == [
        "Проверка участка",
        "Проверка участка",
    ]
    assert [item.description for item in result.work_orders] == [
        "Описание наряда",
        "Описание наряда",
    ]
    assert [item.status for item in result.work_orders] == ["in_progress", "assigned"]
    user_repository.get_by_id.assert_awaited_once_with(actor.id)
    work_order_repository.list_assigned_to_user.assert_awaited_once_with(actor.id)


def test_list_assigned_to_editor_rejects_reviewer() -> None:
    actor = user(UserRole.REVIEWER)
    work_order_repository = AsyncMock()
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.list_assigned_to_editor(actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    work_order_repository.list_assigned_to_user.assert_not_awaited()


@pytest.mark.parametrize(
    "actor",
    [
        user(UserRole.REVIEWER),
        user(UserRole.EDITOR, is_active=False),
    ],
)
def test_get_assigned_work_order_rejects_non_active_editor(actor: SimpleNamespace) -> None:
    work_order_repository = AsyncMock()
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_assigned_work_order(uuid4(), actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    work_order_repository.get_by_id.assert_not_awaited()


def test_get_assigned_work_order_rejects_missing_actor() -> None:
    actor_id = uuid4()
    work_order_repository = AsyncMock()
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = None
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_assigned_work_order(uuid4(), actor_id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "WORK_ORDER_ACTOR_NOT_FOUND"
    user_repository.get_by_id.assert_awaited_once_with(actor_id)
    work_order_repository.get_by_id.assert_not_awaited()


def test_get_assigned_work_order_raises_not_found_when_missing() -> None:
    actor = user()
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = None
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_assigned_work_order(uuid4(), actor.id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "WORK_ORDER_NOT_FOUND"


def test_get_assigned_work_order_rejects_wrong_editor() -> None:
    actor = user()
    assigned = work_order(uuid4())
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=None,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.get_assigned_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "WORK_ORDER_NOT_ASSIGNED"


def test_start_work_order_moves_assigned_to_in_progress_and_saves() -> None:
    actor = user()
    assigned = work_order(actor.id)
    session = FakeSession()
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor

    async def save_in_transaction(saved_work_order):
        assert session.in_transaction is True

    work_order_repository.save.side_effect = save_in_transaction
    service = WorkOrderService(
        session=session,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    result = asyncio.run(service.start_work_order(assigned.id, actor.id))

    assert result is assigned
    assert assigned.status is WorkOrderStatus.IN_PROGRESS
    assert session.begin_calls == 1
    work_order_repository.save.assert_awaited_once_with(assigned)


def test_start_work_order_rejects_repeated_start() -> None:
    actor = user()
    assigned = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    session = FakeSession()
    work_order_repository = AsyncMock()
    work_order_repository.get_by_id.return_value = assigned
    user_repository = AsyncMock()
    user_repository.get_by_id.return_value = actor
    service = WorkOrderService(
        session=session,
        repository=work_order_repository,
        user_repository=user_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.start_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "WORK_ORDER_STATE_CONFLICT"
    assert session.begin_calls == 1
    work_order_repository.save.assert_not_awaited()
