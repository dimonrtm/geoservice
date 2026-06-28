import asyncio
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)


class _ScalarResult:
    def all(self):
        return []

    def one_or_none(self):
        return None


class _ExecuteResult:
    def scalars(self):
        return _ScalarResult()


class CapturingSession:
    def __init__(self) -> None:
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _ExecuteResult()


def test_list_assigned_to_user_orders_by_updated_at_desc_then_code() -> None:
    session = CapturingSession()
    repository = WorkOrderRepository(session)

    asyncio.run(repository.list_assigned_to_user(uuid4()))

    assert session.statement is not None
    compiled = str(session.statement.compile(compile_kwargs={"literal_binds": False}))
    assert (
        "ORDER BY work_order.work_orders.updated_at DESC, work_order.work_orders.code ASC"
        in compiled
    )


def test_get_by_id_for_update_locks_work_order_row() -> None:
    session = CapturingSession()
    repository = WorkOrderRepository(session)
    work_order_id = uuid4()

    result = asyncio.run(repository.get_by_id_for_update(work_order_id))

    assert result is None
    assert session.statement is not None
    compiled = str(
        session.statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )
    assert "FROM work_order.work_orders" in compiled
    assert "work_order.work_orders.id" in compiled
    assert "FOR UPDATE" in compiled
