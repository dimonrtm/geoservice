from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import WebSocketException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from tests.integration_tests.test_browser_auth_session_races import browser_context, issue
from tests.integration_tests.workspace_api_support import build_workspace_api
from utility_service.infrastructure.postgresql.models.layer import Layer
from utility_service.infrastructure.postgresql.models.websocket_ticket import WebSocketTicket
from utility_service.use_cases.deps import (
    get_auth_session_access_service,
    get_websocket_ticket_service,
    get_realtime_session_checker,
)
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import WebSocketTicketError
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.use_cases.tests.test_realtime_connection_manager import DummyWebSocket
from utility_service.web_api.api.auth import create_access_token
from utility_service.utils.settings import settings


@asynccontextmanager
async def realtime_context(engine):
    async with browser_context(engine) as user:
        layer_id = uuid4()
        async with AsyncSession(engine) as session, session.begin():
            session.add(
                Layer(
                    id=layer_id,
                    name=str(layer_id),
                    title="Тест",
                    geometry_type="Point",
                    storage_table="test",
                )
            )
        try:
            yield user, layer_id
        finally:
            async with AsyncSession(engine) as session, session.begin():
                await session.execute(
                    delete(WebSocketTicket).where(WebSocketTicket.user_id == user.id)
                )
                await session.execute(delete(Layer).where(Layer.id == layer_id))


async def ticket_for(engine, user, layer, sid):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        return await get_websocket_ticket_service(session).issue_ticket(user, layer, sid)


async def consume(engine, ticket, layer):
    async with AsyncSession(engine, expire_on_commit=False) as session:
        return await get_websocket_ticket_service(session).consume_ticket(ticket.ticket, layer)


async def logout(engine, user, sid):
    async with AsyncSession(engine) as session:
        await get_auth_session_access_service(session).logout(
            sid, create_access_token(str(user.id), user.role, sid), None
        )


def manager_for(engine):
    return WebSocketConnectionManager(
        get_realtime_session_checker(async_sessionmaker(engine, expire_on_commit=False))
    )


def test_revoked_session_ticket_cannot_connect():
    async def scenario(engine):
        async with realtime_context(engine) as (user, layer):
            first, other = await issue(engine, user), await issue(engine, user)
            ticket = await ticket_for(engine, user, layer, first.session_id)
            other_ticket = await ticket_for(engine, user, layer, other.session_id)
            await logout(engine, user, first.session_id)
            with pytest.raises(WebSocketTicketError):
                await consume(engine, ticket, layer)
            context = await consume(engine, other_ticket, layer)
            manager, socket = manager_for(engine), DummyWebSocket()
            await manager.connect(layer, socket, context)
            assert socket.accepted
            with pytest.raises(WebSocketTicketError):
                await consume(engine, other_ticket, layer)

    run_committed_scenario(scenario)


def test_logout_between_consume_and_connect_is_rechecked():
    async def scenario(engine):
        async with realtime_context(engine) as (user, layer):
            issued = await issue(engine, user)
            ticket = await ticket_for(engine, user, layer, issued.session_id)
            context = await consume(engine, ticket, layer)
            # Consume ещё не допускает соединение. Logout commit предшествует
            # свежему parent-read manager.connect — это точка допуска connect.
            await logout(engine, user, issued.session_id)
            manager, socket = manager_for(engine), DummyWebSocket()
            with pytest.raises(WebSocketException) as error:
                await manager.connect(layer, socket, context)
            assert error.value.code == 1008
            assert not socket.accepted
            assert manager.get_connection_count(layer) == 0

    run_committed_scenario(scenario)


def test_revoked_session_receives_no_new_admitted_event():
    async def scenario(engine):
        async with realtime_context(engine) as (user, layer):
            issued = await issue(engine, user)
            ticket = await ticket_for(engine, user, layer, issued.session_id)
            context = await consume(engine, ticket, layer)
            manager, socket = manager_for(engine), DummyWebSocket()
            await manager.connect(layer, socket, context)
            await manager.broadcast_to_layer(layer, {"type": "before"})
            await logout(engine, user, issued.session_id)
            # Другой manager/worker не получил active close, но fresh send admission
            # после commit отвергает отправку без положительного cache.
            await manager.broadcast_to_layer(layer, {"type": "after"})
            assert socket.sent_json == [{"type": "before"}]
            assert manager.get_connection_count(layer) == 0

    run_committed_scenario(scenario)


@pytest.mark.parametrize("close_failure", [False, True])
@pytest.mark.parametrize("legacy_enabled", [False, True])
def test_disconnect_session_preserves_other_browser(close_failure, legacy_enabled, monkeypatch):
    monkeypatch.setattr(settings, "legacy_gis_api_enabled", legacy_enabled)

    async def scenario(engine):
        async with realtime_context(engine) as (user, layer):
            first, other = await issue(engine, user), await issue(engine, user)

            class Socket(DummyWebSocket):
                async def close(self, code=1000, reason=None):
                    if close_failure:
                        raise RuntimeError("Ошибка закрытия")
                    await super().close(code, reason)

            manager = manager_for(engine)
            first_socket, other_socket = Socket(), DummyWebSocket()
            for issued, socket in [(first, first_socket), (other, other_socket)]:
                ticket = await ticket_for(engine, user, layer, issued.session_id)
                await manager.connect(layer, socket, await consume(engine, ticket, layer))
            app = build_workspace_api(engine)
            app.state.websocket_connection_manager = manager
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                result = await client.post(
                    "/api/v1/auth/logout",
                    json={"session_id": str(first.session_id)},
                    headers={
                        "Authorization": f"Bearer {create_access_token(str(user.id), user.role, first.session_id)}"
                    },
                )
                assert result.status_code == 200
                assert "set-cookie" not in result.headers
            assert manager.get_connection_count(layer) == 1
            assert not other_socket.closed
            await manager.broadcast_to_layer(layer, {"type": "after"})
            assert first_socket.sent_json == []
            assert other_socket.sent_json == [{"type": "after"}]
            async with AsyncSession(engine) as session:
                assert not await get_auth_session_access_service(session).is_session_active(
                    first.session_id
                )

    run_committed_scenario(scenario)


def test_expired_ticket_does_not_revoke_active_parent_or_sibling_ticket():
    async def scenario(engine):
        async with realtime_context(engine) as (user, layer):
            issued = await issue(engine, user)
            expired = await ticket_for(engine, user, layer, issued.session_id)
            sibling = await ticket_for(engine, user, layer, issued.session_id)
            from utility_service.use_cases.services.websocket_ticket_service import (
                hash_websocket_ticket,
            )

            async with AsyncSession(engine) as session, session.begin():
                await session.execute(
                    update(WebSocketTicket)
                    .where(WebSocketTicket.ticket_hash == hash_websocket_ticket(expired.ticket))
                    .values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
                )
            with pytest.raises(WebSocketTicketError):
                await consume(engine, expired, layer)
            context = await consume(engine, sibling, layer)
            assert context.session_id == issued.session_id
            async with AsyncSession(engine) as session:
                assert await get_auth_session_access_service(session).is_session_active(
                    issued.session_id
                )

    run_committed_scenario(scenario)
