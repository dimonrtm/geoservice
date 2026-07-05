from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.layer_repository import LayerRepository
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.websocket_ticket_repository import (
    WebSocketTicketRepository,
)
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    INVALID_WEBSOCKET_TICKET_MESSAGE,
    WebSocketTicketError,
)
from utility_service.use_cases.schemas.realtime import WebSocketTicketOut
from utility_service.use_cases.services.realtime_connection_manager import WebSocketUserContext
from utility_service.utils.settings import settings


ALLOWED_REALTIME_ROLES = {"editor"}


def hash_websocket_ticket(ticket: str) -> str:
    return hashlib.sha256(ticket.encode("utf-8")).hexdigest()


def _role_value(user: Any) -> str:
    role = getattr(user, "role", "")
    return str(getattr(role, "value", role))


class WebSocketTicketService:
    def __init__(
        self,
        session: AsyncSession,
        ticket_repository: WebSocketTicketRepository,
        layer_repository: LayerRepository,
        user_repository: UserRepository,
        ticket_ttl_seconds: int | None = None,
    ):
        self.session = session
        self.ticket_repository = ticket_repository
        self.layer_repository = layer_repository
        self.user_repository = user_repository
        self.ticket_ttl_seconds = (
            ticket_ttl_seconds
            if ticket_ttl_seconds is not None
            else settings.websocket_ticket_ttl_seconds
        )

    async def issue_ticket(self, user: Any, layer_id: UUID) -> WebSocketTicketOut:
        if _role_value(user) not in ALLOWED_REALTIME_ROLES:
            raise AuthApiError(
                status.HTTP_403_FORBIDDEN,
                "ROLE_NOT_ALLOWED",
                "Подписка на realtime недоступна для этой роли.",
            )
        if not user.is_active:
            raise AuthApiError(
                status.HTTP_403_FORBIDDEN,
                "USER_INACTIVE",
                "Учетная запись отключена.",
            )

        async with self.session.begin():
            layer = await self.layer_repository.get_layer_by_id(layer_id)
            if layer is None:
                raise AuthApiError(
                    status.HTTP_404_NOT_FOUND,
                    "LAYER_NOT_FOUND",
                    "Слой не найден.",
                )

            ticket = secrets.token_urlsafe(32)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=self.ticket_ttl_seconds)
            await self.ticket_repository.create_ticket(
                ticket_hash=hash_websocket_ticket(ticket),
                user_id=user.id,
                layer_id=layer_id,
                expires_at=expires_at,
            )

        return WebSocketTicketOut(ticket=ticket, expires_at=expires_at)

    async def consume_ticket(self, ticket: str, layer_id: UUID) -> WebSocketUserContext:
        async with self.session.begin():
            ticket_row = await self.ticket_repository.consume_ticket_hash(
                ticket_hash=hash_websocket_ticket(ticket),
                layer_id=layer_id,
                now=datetime.now(timezone.utc),
            )
            if ticket_row is None:
                raise WebSocketTicketError(INVALID_WEBSOCKET_TICKET_MESSAGE)
            user_id = ticket_row.user_id

        user = await self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active or _role_value(user) not in ALLOWED_REALTIME_ROLES:
            raise WebSocketTicketError(INVALID_WEBSOCKET_TICKET_MESSAGE)

        return WebSocketUserContext(
            user_id=user.id,
            email=user.email,
            role=_role_value(user),
        )
