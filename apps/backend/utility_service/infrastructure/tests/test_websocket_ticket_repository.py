import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from utility_service.infrastructure.postgresql.repositories.websocket_ticket_repository import (
    WebSocketTicketRepository,
)


class _ExecuteResult:
    def scalar_one_or_none(self):
        return None


class CapturingSession:
    def __init__(self) -> None:
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _ExecuteResult()


def test_consume_ticket_hash_updates_matching_unused_unexpired_ticket() -> None:
    session = CapturingSession()
    repository = WebSocketTicketRepository(session)
    layer_id = uuid4()
    now = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)

    result = asyncio.run(
        repository.consume_ticket_hash(
            ticket_hash="ticket-hash",
            layer_id=layer_id,
            now=now,
        )
    )

    assert result is None
    assert session.statement is not None

    compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    sql = str(compiled)

    assert 'UPDATE "user".websocket_tickets SET used_at=' in sql
    assert '"user".websocket_tickets.ticket_hash =' in sql
    assert '"user".websocket_tickets.layer_id =' in sql
    assert '"user".websocket_tickets.used_at IS NULL' in sql
    assert '"user".websocket_tickets.expires_at >' in sql
    assert 'RETURNING "user".websocket_tickets.id' in sql
    assert '"user".websocket_tickets.ticket_hash' in sql
    assert compiled.params["ticket_hash_1"] == "ticket-hash"
    assert compiled.params["layer_id_1"] == layer_id
    assert compiled.params["used_at"] == now
    assert compiled.params["expires_at_1"] == now
