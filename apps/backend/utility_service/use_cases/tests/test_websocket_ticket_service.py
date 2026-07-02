import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.domain.exceptions.websocket_ticket_error import (
    WebSocketTicketError,
)
from utility_service.use_cases.services.websocket_ticket_service import (
    WebSocketTicketService,
    hash_websocket_ticket,
)


class DummyTransaction:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        self.session.in_transaction = True
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.session.completed_begin_calls += 1
        self.session.in_transaction = False
        return False


class DummySession:
    def __init__(self):
        self.begin_calls = 0
        self.completed_begin_calls = 0
        self.in_transaction = False

    def begin(self):
        self.begin_calls += 1
        return DummyTransaction(self)


class FakeTicketRepository:
    def __init__(self):
        self.created = []
        self.consumed_hashes = set()

    async def create_ticket(self, *, ticket_hash, user_id, layer_id, expires_at):
        self.created.append(
            SimpleNamespace(
                ticket_hash=ticket_hash,
                user_id=user_id,
                layer_id=layer_id,
                expires_at=expires_at,
            )
        )
        return self.created[-1]

    async def consume_ticket_hash(self, *, ticket_hash, layer_id, now):
        if ticket_hash in self.consumed_hashes:
            return None
        matching = [
            row
            for row in self.created
            if row.ticket_hash == ticket_hash and row.layer_id == layer_id and row.expires_at > now
        ]
        if not matching:
            return None
        self.consumed_hashes.add(ticket_hash)
        return matching[0]


class FakeLayerRepository:
    def __init__(self, layer):
        self.layer = layer

    async def get_layer_by_id(self, layer_id):
        if self.layer and self.layer.id == layer_id:
            return self.layer
        return None


class FakeUserRepository:
    def __init__(self, user, session=None):
        self.user = user
        self.session = session
        self.get_by_id_in_transaction = []

    async def get_by_id(self, user_id):
        if self.session is not None:
            self.get_by_id_in_transaction.append(self.session.in_transaction)
        if self.user and self.user.id == user_id:
            return self.user
        return None


def make_user(role="editor", is_active=True):
    return SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=SimpleNamespace(value=role),
        is_active=is_active,
    )


def build_service(user, layer, ticket_repository=None):
    repository = ticket_repository or FakeTicketRepository()
    session = DummySession()
    user_repository = FakeUserRepository(user, session)
    service = WebSocketTicketService(
        session,
        repository,
        FakeLayerRepository(layer),
        user_repository,
        ticket_ttl_seconds=60,
    )
    return service, repository


def test_hash_websocket_ticket_uses_sha_256_hex() -> None:
    assert (
        hash_websocket_ticket("ticket-1")
        == "737ce60fccf9da889f4605c0a20479b502eb8ed97e7bf3b5db1295ccd350b1bb"
    )


def test_issue_ticket_stores_hash_and_returns_raw_ticket() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    service, repository = build_service(user, layer)

    result = asyncio.run(service.issue_ticket(user, layer.id))

    assert result.ticket
    assert result.expires_at > datetime.now(timezone.utc)
    assert repository.created[0].ticket_hash == hash_websocket_ticket(result.ticket)
    assert repository.created[0].ticket_hash != result.ticket
    assert repository.created[0].user_id == user.id
    assert repository.created[0].layer_id == layer.id
    assert service.session.begin_calls == 1
    assert service.session.completed_begin_calls == 1


def test_issue_ticket_rejects_role_not_allowed() -> None:
    user = make_user(role="viewer")
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.issue_ticket(user, layer.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ROLE_NOT_ALLOWED"
    assert service.session.begin_calls == 0
    assert service.session.completed_begin_calls == 0


def test_issue_ticket_rejects_inactive_user() -> None:
    user = make_user(is_active=False)
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.issue_ticket(user, layer.id))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"
    assert service.session.begin_calls == 0
    assert service.session.completed_begin_calls == 0


def test_issue_ticket_rejects_missing_layer_with_structured_404() -> None:
    user = make_user()
    layer_id = uuid4()
    service, _repository = build_service(user, None)

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.issue_ticket(user, layer_id))

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "LAYER_NOT_FOUND"
    assert service.session.begin_calls == 1
    assert service.session.completed_begin_calls == 1


def test_consume_ticket_returns_user_context_once() -> None:
    user = make_user(role="reviewer")
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))

    context = asyncio.run(service.consume_ticket(issued.ticket, layer.id))

    assert context.user_id == user.id
    assert context.email == user.email
    assert context.role == "reviewer"
    assert service.session.begin_calls == 2
    assert service.session.completed_begin_calls == 2
    assert service.user_repository.get_by_id_in_transaction == [False]

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, layer.id))
    assert service.session.begin_calls == 3
    assert service.session.completed_begin_calls == 3
    assert service.user_repository.get_by_id_in_transaction == [False]


def test_consume_ticket_rejects_wrong_layer() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    service, _repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, uuid4()))


def test_consume_ticket_rejects_inactive_user_after_issue() -> None:
    user = make_user(is_active=True)
    layer = SimpleNamespace(id=uuid4())
    service, repository = build_service(user, layer)
    issued = asyncio.run(service.issue_ticket(user, layer.id))
    user.is_active = False

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(issued.ticket, layer.id))

    assert hash_websocket_ticket(issued.ticket) in repository.consumed_hashes
    assert service.user_repository.get_by_id_in_transaction == [False]


def test_consume_ticket_rejects_expired_ticket() -> None:
    user = make_user()
    layer = SimpleNamespace(id=uuid4())
    repository = FakeTicketRepository()
    service = WebSocketTicketService(
        DummySession(),
        repository,
        FakeLayerRepository(layer),
        FakeUserRepository(user),
        ticket_ttl_seconds=60,
    )
    ticket = "expired-ticket"
    repository.created.append(
        SimpleNamespace(
            ticket_hash=hash_websocket_ticket(ticket),
            user_id=user.id,
            layer_id=layer.id,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )

    with pytest.raises(WebSocketTicketError):
        asyncio.run(service.consume_ticket(ticket, layer.id))
