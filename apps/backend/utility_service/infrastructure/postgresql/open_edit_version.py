from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.models.work_order import (
    EditVersion,
    WorkOrder,
    WorkOrderStatus,
)
from utility_service.infrastructure.postgresql.repositories.default_state_repository import (
    DefaultStateRepository,
)
from utility_service.infrastructure.postgresql.repositories.edit_version_repository import (
    EditVersionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.work_order_repository import (
    WorkOrderRepository,
)

_OPEN_VERSION_INDEX = "uq_edit_versions_open_work_order"


class OpenVersionConflict(Exception):
    """PostgreSQL rejected a duplicate open version and the transaction rolled back."""


def _open_version_conflict(error: IntegrityError) -> bool:
    # SQLAlchemy's asyncpg wrapper carries the SQLSTATE; asyncpg carries the index name.
    original = error.orig
    driver = getattr(original, "__cause__", None)
    state = None
    name = None
    for diagnostic in (driver, original):
        state = (
            state or getattr(diagnostic, "sqlstate", None) or getattr(diagnostic, "pgcode", None)
        )
        name = (
            name
            or getattr(getattr(diagnostic, "diag", None), "constraint_name", None)
            or getattr(diagnostic, "constraint_name", None)
        )
    if state != "23505":
        return False
    if name:
        return name == _OPEN_VERSION_INDEX
    return _OPEN_VERSION_INDEX in str(error)


class _OpenOperations:
    def __init__(self, storage: "PostgresOpenEditVersionTransactions"):
        self.storage = storage
        self.order: WorkOrder | None = None
        self.version: EditVersion | None = None

    async def get_actor(self, actor_id: UUID) -> User | None:
        return await self.storage.users.get_by_id(actor_id)

    async def lock_work_order(self, work_order_id: UUID) -> WorkOrder | None:
        self.order = await self.storage.orders.get_by_id_for_update(work_order_id)
        return self.order

    async def find_open_version(self, work_order_id: UUID) -> UUID | None:
        self.version = await self.storage.versions.get_open_edit_version(work_order_id)
        return self.version.id if self.version is not None else None

    async def create_from_active_default(
        self, work_order_id: UUID, owner_user_id: UUID
    ) -> EditVersion | None:
        baseline = await self.storage.defaults.get_active_aggregate_by_work_order_id(work_order_id)
        if baseline is None:
            return None
        return await self.storage.versions.create_open_edit_version(
            geometry_policy=self.storage.geometry_policy,
            work_order_id=work_order_id,
            default_state_id=baseline.state.id,
            base_network_revision=baseline.state.base_network_revision,
            default_features=baseline.features,
            default_associations=baseline.associations,
            owner_user_id=owner_user_id,
        )

    async def mark_in_progress(self, work_order_id: UUID) -> None:
        if self.order is None or self.order.id != work_order_id:
            raise RuntimeError("Work order must be locked before starting it")
        self.order.status = WorkOrderStatus.IN_PROGRESS
        await self.storage.orders.save(self.order)

    async def touch_open_version(self, edit_version_id: UUID) -> EditVersion:
        if self.version is None or self.version.id != edit_version_id:
            raise RuntimeError("Open version must be read before updating it")
        await self.storage.versions.touch_edit_version(self.version)
        return self.version


class PostgresOpenEditVersionTransactions:
    open_version_conflict = OpenVersionConflict

    def __init__(self, session: AsyncSession, geometry_policy: GeometryPolicy):
        self.session = session
        self.geometry_policy = geometry_policy
        self.users = UserRepository(session)
        self.orders = WorkOrderRepository(session)
        self.defaults = DefaultStateRepository(session)
        self.versions = EditVersionRepository(session)

    @asynccontextmanager
    async def first_attempt(self) -> AsyncIterator[_OpenOperations]:
        await self.session.begin()
        try:
            yield _OpenOperations(self)
            await self.session.commit()
        except BaseException as error:
            await self.session.rollback()
            if isinstance(error, IntegrityError) and _open_version_conflict(error):
                raise OpenVersionConflict() from error
            raise

    @asynccontextmanager
    async def recovery_attempt(self) -> AsyncIterator[_OpenOperations]:
        async with self.session.begin():
            yield _OpenOperations(self)
