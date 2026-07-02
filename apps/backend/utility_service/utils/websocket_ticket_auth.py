from __future__ import annotations

from uuid import UUID

from fastapi import WebSocketException, status

from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    INVALID_WEBSOCKET_TICKET_MESSAGE,
    WebSocketTicketError,
)
from utility_service.use_cases.services.realtime_connection_manager import WebSocketUserContext
from utility_service.use_cases.services.websocket_ticket_service import WebSocketTicketService


def _websocket_ticket_error(reason: str) -> WebSocketException:
    return WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason=reason)


async def authenticate_websocket_ticket(
    ticket: str | None,
    layer_id: UUID,
    ticket_service: WebSocketTicketService,
) -> WebSocketUserContext:
    if ticket is None or not ticket.strip():
        raise _websocket_ticket_error("Realtime ticket отсутствует")

    try:
        return await ticket_service.consume_ticket(ticket, layer_id)
    except WebSocketTicketError as exc:
        raise _websocket_ticket_error(INVALID_WEBSOCKET_TICKET_MESSAGE) from exc
