from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario, seed_context
from tests.integration_tests.save_geometry_support import seed_save_context
from utility_service.use_cases.domain.exceptions.work_order_operation_error import (
    WorkOrderOperationError,
)
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.infrastructure.postgresql.models.work_order import EditVersion, WorkOrder
from utility_service.infrastructure.postgresql.open_edit_version import (
    OpenVersionConflict,
    PostgresOpenEditVersionTransactions,
)
from utility_service.use_cases.services.open_edit_version import OpenEditVersionService


def test_unique_insert_rolls_back_before_recovery_on_same_session():
    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_context(setup)
        order_id = ids["work_order_id"]
        async with AsyncSession(engine) as session:
            tx = PostgresOpenEditVersionTransactions(session, GeometryPolicy(Decimal("0.0000001")))
            with pytest.raises(OpenVersionConflict):
                async with tx.first_attempt() as ops:
                    await ops.lock_work_order(order_id)
                    await ops.create_from_active_default(order_id, ids["actor_user_id"])
            assert not session.in_transaction()
            async with tx.recovery_attempt() as ops:
                await ops.lock_work_order(order_id)
                existing = await ops.find_open_version(order_id)
                assert existing == ids["edit_version_id"]
                version = await ops.touch_open_version(existing)
                assert isinstance(version, EditVersion)
                updated_at = version.last_opened_at
        async with AsyncSession(engine) as verify:
            row = (
                await verify.scalars(
                    select(EditVersion).where(EditVersion.work_order_id == order_id)
                )
            ).one()
            assert row.id == existing
            assert row.last_opened_at == updated_at

    run_committed_scenario(scenario)


def test_open_reads_current_assignment_after_lock_with_retained_order():
    async def scenario(engine):
        async with engine.begin() as setup:
            ids = await seed_save_context(setup)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            async with session.begin():
                retained = await session.get(WorkOrder, ids["work_order_id"])
            async with engine.begin() as other:
                await other.execute(
                    update(WorkOrder)
                    .where(WorkOrder.id == retained.id)
                    .values(assignee_user_id=uuid4())
                )
            tx = PostgresOpenEditVersionTransactions(session, GeometryPolicy(Decimal("0.0000001")))
            with pytest.raises(WorkOrderOperationError) as caught:
                await OpenEditVersionService(tx).open_for_work_order(
                    ids["work_order_id"], ids["actor_user_id"]
                )
            assert caught.value.code.value == "WORK_ORDER_NOT_FOUND"

    run_committed_scenario(scenario)
