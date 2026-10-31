from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.websocket_ticket import WebSocketTicket
from utility_service.infrastructure.postgresql.models.browser_auth_session import BrowserAuthSession


class WebSocketTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(
        self,
        *,
        ticket_hash: str,
        browser_session_id: UUID,
        user_id: UUID,
        layer_id: UUID,
        expires_at: datetime,
    ) -> WebSocketTicket:
        stmt = (
            insert(WebSocketTicket)
            .values(
                ticket_hash=ticket_hash,
                browser_session_id=browser_session_id,
                user_id=user_id,
                layer_id=layer_id,
                expires_at=expires_at,
            )
            .returning(WebSocketTicket)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def consume_ticket_hash(
        self,
        *,
        ticket_hash: str,
        layer_id: UUID,
        now: datetime,
    ) -> WebSocketTicket | None:
        stmt = (
            update(WebSocketTicket)
            .where(WebSocketTicket.ticket_hash == ticket_hash)
            .where(WebSocketTicket.layer_id == layer_id)
            .where(WebSocketTicket.used_at.is_(None))
            .where(WebSocketTicket.expires_at > now)
            .where(
                exists(
                    select(BrowserAuthSession.id)
                    .where(BrowserAuthSession.id == WebSocketTicket.browser_session_id)
                    .where(BrowserAuthSession.user_id == WebSocketTicket.user_id)
                    .where(BrowserAuthSession.revoked_at.is_(None))
                    .where(BrowserAuthSession.expires_at > now)
                )
            )
            .values(used_at=now)
            .returning(WebSocketTicket)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
