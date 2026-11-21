import asyncio
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import EditVersion, WorkOrder
from utility_service.infrastructure.postgresql.open_edit_version import (
    OpenVersionConflict,
    PostgresOpenEditVersionTransactions,
)

INDEX = "uq_edit_versions_open_work_order"


def test_open_operations_use_repository_models():
    async def run():
        async with AsyncSession() as session:
            tx = PostgresOpenEditVersionTransactions(session, GeometryPolicy(Decimal("0.0000001")))
            user = User(id=uuid4(), role=UserRole.EDITOR, is_active=True)
            order = WorkOrder(id=uuid4(), assignee_user_id=user.id)
            version = EditVersion(id=uuid4(), work_order_id=order.id)
            tx.users.get_by_id = AsyncMock(return_value=user)
            tx.orders.get_by_id_for_update = AsyncMock(return_value=order)
            tx.versions.get_open_edit_version = AsyncMock(return_value=version)
            tx.versions.touch_edit_version = AsyncMock()
            async with tx.first_attempt() as ops:
                assert await ops.get_actor(user.id) is user
                assert await ops.lock_work_order(order.id) is order
                assert await ops.find_open_version(order.id) == version.id
                assert await ops.touch_open_version(version.id) is version
            tx.versions.touch_edit_version.assert_awaited_once_with(version)

    asyncio.run(run())


def db_error(state, name, message, *, nested=False):
    original = Exception(message)
    original.pgcode = state
    details = Exception(message)
    if nested:
        details.constraint_name = name
        original.__cause__ = details
    else:
        original.diag = SimpleNamespace(constraint_name=name)
    return IntegrityError("insert", {}, original)


@pytest.mark.parametrize(
    ("state", "name", "message", "nested", "recover"),
    [
        ("23505", INDEX, "", False, True),
        ("23505", INDEX, "", True, True),
        ("23505", "other", INDEX, False, False),
        ("23505", "other", INDEX, True, False),
        ("23505", None, INDEX, False, True),
        ("23505", None, "other", False, False),
        ("23503", INDEX, INDEX, False, False),
        (None, INDEX, INDEX, False, False),
    ],
)
def test_first_attempt_classifies_driver_diagnostics(state, name, message, nested, recover):
    failure = db_error(state, name, message, nested=nested)
    session = AsyncSession()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    tx = PostgresOpenEditVersionTransactions(session, GeometryPolicy(Decimal("0.0000001")))

    async def run():
        async with tx.first_attempt():
            raise failure

    with pytest.raises(OpenVersionConflict if recover else IntegrityError) as caught:
        asyncio.run(run())
    assert (caught.value.__cause__ if recover else caught.value) is failure
    session.rollback.assert_awaited_once()


@pytest.mark.parametrize("stage", ["commit", "rollback", "recovery"])
def test_translation_is_limited_to_rolled_back_first_attempt(stage):
    failure = db_error("23505", INDEX, INDEX)
    session = AsyncSession()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    tx = PostgresOpenEditVersionTransactions(session, GeometryPolicy(Decimal("0.0000001")))
    if stage == "commit":
        session.commit.side_effect = failure
    elif stage == "rollback":
        session.rollback.side_effect = failure

    async def run():
        async with tx.recovery_attempt() if stage == "recovery" else tx.first_attempt():
            if stage == "rollback":
                raise db_error("23505", INDEX, INDEX)
            if stage == "recovery":
                raise failure

    with pytest.raises(OpenVersionConflict if stage == "commit" else IntegrityError) as caught:
        asyncio.run(run())
    assert (caught.value.__cause__ if stage == "commit" else caught.value) is failure
