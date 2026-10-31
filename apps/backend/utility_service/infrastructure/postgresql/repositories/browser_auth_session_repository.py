from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.browser_auth_session import BrowserAuthSession


class BrowserAuthSessionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_session(
        self,
        *,
        user_id: UUID,
        expires_at: datetime,
    ) -> BrowserAuthSession:
        result = await self.session.execute(
            insert(BrowserAuthSession)
            .values(
                user_id=user_id,
                expires_at=expires_at,
            )
            .returning(BrowserAuthSession)
        )
        return result.scalar_one()

    async def get_session(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> BrowserAuthSession | None:
        statement = select(BrowserAuthSession).where(BrowserAuthSession.id == session_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self.session.execute(statement.execution_options(populate_existing=True))
        return result.scalar_one_or_none()

    async def revoke_session(
        self,
        session_id: UUID,
        *,
        now: datetime,
    ) -> None:
        await self.session.execute(
            update(BrowserAuthSession)
            .where(BrowserAuthSession.id == session_id)
            .where(BrowserAuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def extend_session(
        self,
        session_id: UUID,
        *,
        expires_at: datetime,
    ) -> None:
        await self.session.execute(
            update(BrowserAuthSession)
            .where(BrowserAuthSession.id == session_id)
            .where(BrowserAuthSession.revoked_at.is_(None))
            .values(expires_at=expires_at)
        )
