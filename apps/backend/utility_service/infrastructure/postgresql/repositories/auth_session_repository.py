from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self,
        *,
        session_token_hash: str,
        user_id: UUID,
        expires_at: datetime,
    ) -> AuthSession:
        stmt = (
            insert(AuthSession)
            .values(
                session_token_hash=session_token_hash,
                user_id=user_id,
                expires_at=expires_at,
            )
            .returning(AuthSession)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_active_session_by_hash(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> AuthSession | None:
        stmt = (
            select(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .where(AuthSession.expires_at > now)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_session_hash(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.session.execute(stmt)

    async def mark_session_used(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .where(AuthSession.expires_at > now)
            .values(last_used_at=now)
        )
        await self.session.execute(stmt)

    async def mark_session_rotated(
        self,
        *,
        session_token_hash: str,
        now: datetime,
    ) -> AuthSession | None:
        stmt = (
            update(AuthSession)
            .where(AuthSession.session_token_hash == session_token_hash)
            .where(AuthSession.revoked_at.is_(None))
            .where(AuthSession.expires_at > now)
            .values(revoked_at=now, rotated_at=now, last_used_at=now)
            .returning(AuthSession)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
