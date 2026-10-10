from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario, seed_context
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import EditVersion
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.use_cases.services.edit_version_service import EditVersionService


async def seed_unopened(connection):
    ids = await seed_context(connection)
    for table in ("edit_version_associations", "edit_version_features", "edit_versions"):
        key = "id" if table == "edit_versions" else "edit_version_id"
        await connection.execute(
            text(f"DELETE FROM work_order.{table} WHERE {key}=:id"),
            {
                "id": ids["edit_version_id"],
            },
        )
    return ids


def service(
    session,
    ids,
    grid,
    repository=None,
):
    return EditVersionService(
        session,
        SimpleNamespace(
            get_by_id=AsyncMock(
                return_value=SimpleNamespace(
                    id=ids["actor_user_id"],
                    role=UserRole.EDITOR,
                    is_active=True,
                )
            )
        ),
        repository or WorkOrderRepository(session),
        DefaultStateRepository(session),
        edit_version_repository=EditVersionRepository(session),
        geometry_policy=GeometryPolicy(Decimal(grid)),
    )


def test_open_snapshots_policy_and_reopen_keeps_it_across_sessions():
    async def scenario(engine):
        async with engine.begin() as connection:
            first = await seed_unopened(connection)
            second = await seed_unopened(connection)
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            opened = await service(
                session,
                first,
                "0.0000001",
            ).open_for_work_order(
                first["work_order_id"],
                first["actor_user_id"],
            )
            version_id = opened.edit_version.id
            assert opened.created
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            reopened = await service(
                session,
                first,
                "0.00000025",
            ).open_for_work_order(
                first["work_order_id"],
                first["actor_user_id"],
            )
            assert not reopened.created
            assert reopened.edit_version.id == version_id
            assert reopened.edit_version.geometry_xy_resolution == Decimal("0.0000001")
        async with AsyncSession(
            engine,
            expire_on_commit=False,
        ) as session:
            created = await service(
                session,
                second,
                "0.00000025",
            ).open_for_work_order(
                second["work_order_id"],
                second["actor_user_id"],
            )
            second_id = created.edit_version.id
        async with AsyncSession(engine) as session:
            assert (
                await session.get(
                    EditVersion,
                    version_id,
                )
            ).geometry_xy_resolution == Decimal("0.0000001")
            assert (
                await session.get(
                    EditVersion,
                    second_id,
                )
            ).geometry_xy_resolution == Decimal("0.00000025")

    run_committed_scenario(scenario)


def test_failed_open_rolls_back_policy_root_and_snapshot():
    class FailingRepository(WorkOrderRepository):
        async def save(
            self,
            work_order,
        ):
            raise RuntimeError("after snapshot")

    async def scenario(engine):
        async with engine.begin() as connection:
            ids = await seed_unopened(connection)
        async with AsyncSession(engine) as session:
            with pytest.raises(
                RuntimeError,
                match="after snapshot",
            ):
                await service(
                    session,
                    ids,
                    "0.00000025",
                    FailingRepository(session),
                ).open_for_work_order(
                    ids["work_order_id"],
                    ids["actor_user_id"],
                )
        async with engine.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM work_order.edit_versions WHERE work_order_id=:id"),
                    {
                        "id": ids["work_order_id"],
                    },
                )
                == 0
            )
            assert (
                await connection.scalar(
                    text("SELECT status FROM work_order.work_orders WHERE id=:id"),
                    {
                        "id": ids["work_order_id"],
                    },
                )
                == "assigned"
            )

    run_committed_scenario(scenario)
