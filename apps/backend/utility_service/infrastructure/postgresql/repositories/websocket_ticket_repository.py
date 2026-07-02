from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.models.websocket_ticket import WebSocketTicket


class WebSocketTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(
        self,
        *,
        ticket_hash: str,
        user_id: UUID,
        layer_id: UUID,
        expires_at: datetime,
    ) -> WebSocketTicket:
        stmt = (
            insert(WebSocketTicket)
            .values(
                ticket_hash=ticket_hash,
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
            .values(used_at=now)
            .returning(WebSocketTicket)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
