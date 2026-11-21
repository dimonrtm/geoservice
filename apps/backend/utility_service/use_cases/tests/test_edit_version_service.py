import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, call
from uuid import UUID, uuid4

import pytest

from utility_service.use_cases.domain.exceptions.work_order_operation_error import (
    WorkOrderOperationError,
)
from utility_service.use_cases.services.open_edit_version import (
    OpenEditVersionSnapshot,
    OpenEditVersionService,
)


@dataclass
class ActorRow:
    role: str
    is_active: bool


@dataclass
class WorkOrderRow:
    assignee_user_id: UUID
    status: str


class CompetingOpen(Exception):
    pass


class Attempts:
    open_version_conflict = CompetingOpen

    def __init__(self):
        self.actor_id = uuid4()
        self.order_id = uuid4()
        now = datetime.now(timezone.utc)
        self.snapshot = OpenEditVersionSnapshot(
            uuid4(), self.order_id, self.actor_id, "open", 12, now, now
        )
        self.first = self.operations("assigned", None)
        self.second = self.operations("in_progress", self.snapshot.id)
        self.events = []
        self.commit_error = None

    def operations(self, status, existing):
        ops = AsyncMock()
        ops.get_actor.return_value = ActorRow("editor", True)
        ops.lock_work_order.return_value = WorkOrderRow(self.actor_id, status)
        ops.find_open_version.return_value = existing
        ops.create_from_active_default.return_value = self.snapshot
        ops.touch_open_version.return_value = self.snapshot
        return ops

    @asynccontextmanager
    async def first_attempt(self):
        self.events.append("first")
        try:
            yield self.first
            if self.commit_error:
                raise self.commit_error
        except BaseException:
            self.events.append("rollback")
            raise
        self.events.append("commit")

    @asynccontextmanager
    async def recovery_attempt(self):
        self.events.append("recover")
        yield self.second
        self.events.append("commit")

    def open(self):
        return asyncio.run(
            OpenEditVersionService(self).open_for_work_order(self.order_id, self.actor_id)
        )


def test_create_and_start_in_same_transaction():
    tx = Attempts()
    result = tx.open()
    assert result.created and result.edit_version == tx.snapshot
    assert tx.events == ["first", "commit"]
    assert tx.first.mock_calls == [
        call.get_actor(tx.actor_id),
        call.lock_work_order(tx.order_id),
        call.find_open_version(tx.order_id),
        call.create_from_active_default(tx.order_id, tx.actor_id),
        call.mark_in_progress(tx.order_id),
    ]


def test_reopen_without_creating_a_new_snapshot():
    tx = Attempts()
    tx.first = tx.second
    result = tx.open()
    assert not result.created and result.edit_version == tx.snapshot
    tx.first.touch_open_version.assert_awaited_once_with(tx.snapshot.id)
    tx.first.mark_in_progress.assert_not_awaited()
    tx.first.create_from_active_default.assert_not_awaited()


@pytest.mark.parametrize("reopening", [False, True])
def test_result_copies_version_fields_inside_transaction(reopening):
    tx = Attempts()
    record = SimpleNamespace(**vars(tx.snapshot))
    if reopening:
        tx.first = tx.second
    tx.first.create_from_active_default.return_value = record
    tx.first.touch_open_version.return_value = record
    original_attempt = tx.first_attempt

    @asynccontextmanager
    async def expiring_attempt():
        async with original_attempt() as operations:
            yield operations
        vars(record).clear()

    tx.first_attempt = expiring_attempt
    result = tx.open()
    assert result.edit_version == tx.snapshot
    assert result.created is (not reopening)


@pytest.mark.parametrize(
    ("status", "existing", "code"),
    [
        ("assigned", True, "WORK_ORDER_CONTEXT_INVALID"),
        ("assigned", False, "WORK_ORDER_CONTEXT_INVALID"),
        ("in_progress", False, "WORK_ORDER_CONTEXT_INVALID"),
        ("closed", True, "WORK_ORDER_STATE_CONFLICT"),
    ],
)
def test_invalid_creation_context(status, existing, code):
    tx = Attempts()
    tx.first.lock_work_order.return_value = WorkOrderRow(tx.actor_id, status)
    tx.first.find_open_version.return_value = tx.snapshot.id if existing else None
    tx.first.create_from_active_default.return_value = None
    with pytest.raises(WorkOrderOperationError) as error:
        tx.open()
    assert error.value.code.value == code
    tx.first.mark_in_progress.assert_not_awaited()


@pytest.mark.parametrize("during_commit", [False, True])
def test_recovery_after_rollback(during_commit):
    tx = Attempts()
    if during_commit:
        tx.commit_error = CompetingOpen()
    else:
        tx.first.create_from_active_default.side_effect = CompetingOpen()
    # Recovery uses access and version existence, even if the order status is unexpected.
    tx.second.lock_work_order.return_value = WorkOrderRow(tx.actor_id, "assigned")
    result = tx.open()
    assert not result.created and result.edit_version == tx.snapshot
    assert tx.events == ["first", "rollback", "recover", "commit"]
    assert tx.second.mock_calls == [
        call.get_actor(tx.actor_id),
        call.lock_work_order(tx.order_id),
        call.find_open_version(tx.order_id),
        call.touch_open_version(tx.snapshot.id),
    ]


@pytest.mark.parametrize("recovering", [False, True])
@pytest.mark.parametrize(
    ("actor", "assignment", "code"),
    [
        (None, "own", "WORK_ORDER_ACTOR_NOT_FOUND"),
        (ActorRow("editor", False), "own", "ROLE_NOT_ALLOWED"),
        (ActorRow("viewer", True), "own", "ROLE_NOT_ALLOWED"),
        (ActorRow("editor", True), "missing", "WORK_ORDER_NOT_FOUND"),
        (ActorRow("editor", True), "other", "WORK_ORDER_NOT_FOUND"),
    ],
)
def test_access_checked_before_reading_version(actor, assignment, code, recovering):
    tx = Attempts()
    ops = tx.first
    if recovering:
        tx.commit_error = CompetingOpen()
        ops = tx.second
    ops.get_actor.return_value = actor
    ops.lock_work_order.return_value = (
        None
        if assignment == "missing"
        else WorkOrderRow(tx.actor_id if assignment == "own" else uuid4(), "assigned")
    )
    with pytest.raises(WorkOrderOperationError) as error:
        tx.open()
    assert error.value.code.value == code
    ops.find_open_version.assert_not_awaited()
    ops.touch_open_version.assert_not_awaited()


def test_no_open_version_after_rollback():
    tx = Attempts()
    tx.commit_error = CompetingOpen()
    tx.second.find_open_version.return_value = None
    with pytest.raises(WorkOrderOperationError) as error:
        tx.open()
    assert error.value.code.value == "WORK_ORDER_CONTEXT_INVALID"
    tx.second.create_from_active_default.assert_not_awaited()


@pytest.mark.parametrize("recovery_failure", [False, True])
def test_no_retry_on_unrelated_commit_or_recovery_failure(recovery_failure):
    tx = Attempts()
    failure = RuntimeError("failed")
    tx.commit_error = CompetingOpen() if recovery_failure else failure
    tx.second.touch_open_version.side_effect = failure
    with pytest.raises(RuntimeError) as error:
        tx.open()
    assert error.value is failure
    assert tx.events == ["first", "rollback"] + (["recover"] if recovery_failure else [])
