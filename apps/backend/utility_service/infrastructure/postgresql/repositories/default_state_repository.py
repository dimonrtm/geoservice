from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.utility_network import DefaultState


class DefaultStateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_default(self) -> DefaultState | None:
        result = await self.session.execute(
            select(DefaultState).where(DefaultState.name == "default")
        )
        return result.scalars().one_or_none()
