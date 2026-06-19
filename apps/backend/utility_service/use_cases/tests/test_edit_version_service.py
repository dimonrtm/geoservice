import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersionStatus,
    WorkOrderStatus,
)
from utility_service.use_cases.domain.exceptions.work_order_api_error import WorkOrderApiError
from utility_service.use_cases.services.edit_version_service import EditVersionService


def user(role: UserRole = UserRole.EDITOR, *, is_active: bool = True) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), role=role, is_active=is_active)


def work_order(
    assignee_id,
    *,
    status: WorkOrderStatus = WorkOrderStatus.ASSIGNED,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        code="WO-001",
        assignee_id=assignee_id,
        status=status,
    )


def default_state(current_revision: int = 12) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), name="default", current_revision=current_revision)


def edit_version(work_order_id, owner_id, *, base_revision: int = 12) -> SimpleNamespace:
    now = datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid4(),
        work_order_id=work_order_id,
        owner_id=owner_id,
        base_revision=base_revision,
        status=EditVersionStatus.OPEN,
        created_at=now,
        last_opened_at=now,
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


def repository(**methods):
    fake = SimpleNamespace()
    for name, return_value in methods.items():
        setattr(fake, name, AsyncMock(return_value=return_value))
    return fake


def build_service(
    *,
    session: FakeSession | None = None,
    user_repository=None,
    work_order_repository=None,
    edit_version_repository=None,
    default_state_repository=None,
) -> EditVersionService:
    return EditVersionService(
        session=session or FakeSession(),
        user_repository=user_repository or repository(get_by_id=None),
        work_order_repository=work_order_repository or repository(get_by_id=None, save=None),
        edit_version_repository=edit_version_repository
        or repository(get_open_by_work_order_id=None, create_open=None, touch_last_opened=None),
        default_state_repository=default_state_repository or repository(get_default=None),
    )


def test_open_assigned_work_order_creates_edit_version_and_starts_work_order() -> None:
    actor = user()
    assigned = work_order(actor.id)
    created = edit_version(assigned.id, actor.id)
    session = FakeSession()
    user_repository = repository(get_by_id=actor)
    work_order_repository = repository(get_by_id=assigned, save=None)
    edit_version_repository = repository(
        get_open_by_work_order_id=None,
        create_open=created,
        touch_last_opened=None,
    )
    default_state_repository = repository(get_default=default_state(12))
    service = build_service(
        session=session,
        user_repository=user_repository,
        work_order_repository=work_order_repository,
        edit_version_repository=edit_version_repository,
        default_state_repository=default_state_repository,
    )

    result = asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert result.created is True
    assert result.edit_version is created
    assert assigned.status is WorkOrderStatus.IN_PROGRESS
    assert session.begin_calls == 1
    edit_version_repository.create_open.assert_awaited_once_with(
        work_order_id=assigned.id,
        owner_id=actor.id,
        base_revision=12,
    )
    work_order_repository.save.assert_awaited_once_with(assigned)


def test_open_in_progress_work_order_returns_existing_edit_version() -> None:
    actor = user()
    started = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    existing = edit_version(started.id, actor.id)
    edit_version_repository = repository(
        get_open_by_work_order_id=existing,
        create_open=None,
        touch_last_opened=None,
    )
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_by_id=started, save=None),
        edit_version_repository=edit_version_repository,
        default_state_repository=repository(get_default=None),
    )

    result = asyncio.run(service.open_for_work_order(started.id, actor.id))

    assert result.created is False
    assert result.edit_version is existing
    edit_version_repository.touch_last_opened.assert_awaited_once_with(existing)
    edit_version_repository.create_open.assert_not_awaited()


@pytest.mark.parametrize(
    "actor",
    [
        user(UserRole.REVIEWER),
        user(UserRole.EDITOR, is_active=False),
    ],
)
def test_open_rejects_non_active_editor(actor: SimpleNamespace) -> None:
    work_order_repository = repository(get_by_id=None, save=None)
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=work_order_repository,
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(uuid4(), actor.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    work_order_repository.get_by_id.assert_not_awaited()


def test_open_masks_wrong_assignee_as_not_found() -> None:
    actor = user()
    assigned_to_other = work_order(uuid4())
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_by_id=assigned_to_other, save=None),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned_to_other.id, actor.id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "WORK_ORDER_NOT_FOUND"


def test_open_rejects_missing_default_state() -> None:
    actor = user()
    assigned = work_order(actor.id)
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_by_id=assigned, save=None),
        edit_version_repository=repository(
            get_open_by_work_order_id=None,
            create_open=None,
            touch_last_opened=None,
        ),
        default_state_repository=repository(get_default=None),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"


def test_open_rejects_assigned_work_order_with_existing_open_version() -> None:
    actor = user()
    assigned = work_order(actor.id)
    existing = edit_version(assigned.id, actor.id)
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_by_id=assigned, save=None),
        edit_version_repository=repository(
            get_open_by_work_order_id=existing,
            create_open=None,
            touch_last_opened=None,
        ),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(assigned.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"


def test_open_rejects_in_progress_work_order_without_existing_open_version() -> None:
    actor = user()
    started = work_order(actor.id, status=WorkOrderStatus.IN_PROGRESS)
    service = build_service(
        user_repository=repository(get_by_id=actor),
        work_order_repository=repository(get_by_id=started, save=None),
        edit_version_repository=repository(
            get_open_by_work_order_id=None,
            create_open=None,
            touch_last_opened=None,
        ),
    )

    with pytest.raises(WorkOrderApiError) as exc_info:
        asyncio.run(service.open_for_work_order(started.id, actor.id))

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "WORK_ORDER_CONTEXT_INVALID"
