from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import (
    EditVersion,
    EditVersionStatus,
)


class EditVersionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_open_by_work_order_id(self, work_order_id: UUID) -> EditVersion | None:
        result = await self.session.execute(
            select(EditVersion).where(
                EditVersion.work_order_id == work_order_id,
                EditVersion.status == EditVersionStatus.OPEN,
            )
        )
        return result.scalars().one_or_none()

    async def create_open(
        self,
        *,
        work_order_id: UUID,
        owner_id: UUID,
        base_revision: int,
    ) -> EditVersion:
        edit_version = EditVersion(
            work_order_id=work_order_id,
            owner_id=owner_id,
            base_revision=base_revision,
            status=EditVersionStatus.OPEN,
        )
        self.session.add(edit_version)
        await self.session.flush()
        return edit_version

    async def touch_last_opened(self, edit_version: EditVersion) -> None:
        edit_version.last_opened_at = datetime.now(timezone.utc)
        self.session.add(edit_version)
        await self.session.flush()
