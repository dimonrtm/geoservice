from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.edit_geometry_repository_support import (
    seed_repository_context,
    snapshot_repository_state,
)
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersionCommand,
    EditVersionChangeEvent,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.use_cases.schemas.edit_version.geometry_save_in import GeometrySaveRequest
from utility_service.use_cases.services.edit_version_service import EditVersionService


BASELINE = GeometryValue(
    "LineString",
    tuple(
        tuple(Decimal(v) for v in p)
        for p in (
            ("65.52", "44.82"),
            ("65.525", "44.8205"),
            ("65.53", "44.82"),
        )
    ),
)
MOVED = replace(
    BASELINE,
    coordinates=(
        BASELINE.coordinates[0],
        (Decimal("65.525"), Decimal("44.8215")),
        BASELINE.coordinates[2],
    ),
)


async def seed_save_context(connection):
    ids = await seed_repository_context(connection)
    await connection.execute(
        User.__table__.insert().values(
            id=ids["actor_user_id"],
            email=f"{ids['actor_user_id']}@save.test",
            role=UserRole.EDITOR,
            is_active=True,
        )
    )
    return ids


def build_save_service(session):
    return EditVersionService(
        session,
        UserRepository(session),
        WorkOrderRepository(session),
        DefaultStateRepository(session),
        geometry_policy=GeometryPolicy(Decimal("0.0000001")),
        edit_version_repository=EditVersionRepository(session),
    )


async def save(
    service,
    ids,
    request,
):
    return await service.save_geometry(
        work_order_id=ids["work_order_id"],
        edit_version_id=ids["edit_version_id"],
        feature_id=ids["feature_id"],
        actor_id=ids["actor_user_id"],
        request=request,
    )


def request(
    geometry=MOVED,
    token="1",
    command_id=None,
):
    return GeometrySaveRequest(
        command_id or uuid4(),
        token,
        geometry,
    )


async def call_save(
    engine,
    ids,
    value,
):
    async with AsyncSession(engine) as session:
        return await save(
            build_save_service(session),
            ids,
            value,
        )


async def snapshot_save_state(
    connection,
    ids,
):
    snapshot = await snapshot_repository_state(
        connection,
        ids,
    )
    snapshot["commands"] = [
        dict(row)
        for row in (
            await connection.execute(
                select(EditVersionCommand.__table__)
                .where(EditVersionCommand.edit_version_id == ids["edit_version_id"])
                .order_by(EditVersionCommand.command_id)
            )
        ).mappings()
    ]
    snapshot["events"] = [
        dict(row)
        for row in (
            await connection.execute(
                select(EditVersionChangeEvent.__table__)
                .where(EditVersionChangeEvent.edit_version_id == ids["edit_version_id"])
                .order_by(EditVersionChangeEvent.command_id)
            )
        ).mappings()
    ]
    return snapshot
