import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import get_type_hints
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.browser_auth_session_repository import (
    BrowserAuthSessionRepository,
)
from utility_service.use_cases.deps import get_auth_session_service
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)
from utility_service.use_cases.schemas.auth.refreshed_auth_session_out import (
    RefreshedAuthSessionOut,
)
from utility_service.use_cases.services.auth_session_service import (
    AuthSessionService,
    hash_auth_session_token,
)

EXPECTED_AUTH_REQUIRED_MESSAGE = "Сессия недействительна."
EXPECTED_USER_INACTIVE_MESSAGE = "Учетная запись отключена."


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


class FakeAuthSessionRepository:
    def __init__(self, events):
        self.events = events
        self.active_session = None
        self.rotated_session = None
        self.created = []
        self.get_active_calls = []
        self.history_calls = []
        self.rotate_calls = []
        self.revoke_calls = []

    async def create_session(
        self,
        *,
        session_token_hash,
        user_id,
        browser_session_id,
        expires_at,
    ):
        self.events.append("create_session")
        row = SimpleNamespace(
            session_token_hash=session_token_hash,
            user_id=user_id,
            browser_session_id=browser_session_id,
            expires_at=expires_at,
        )
        self.created.append(row)
        return row

    async def get_session_by_hash(
        self,
        *,
        session_token_hash,
    ):
        self.events.append("get_history")
        self.history_calls.append(session_token_hash)
        return self.active_session

    async def get_active_session_by_hash(self, *, session_token_hash, now):
        self.events.append("get_active_session")
        self.get_active_calls.append(
            SimpleNamespace(session_token_hash=session_token_hash, now=now)
        )
        return self.active_session

    async def mark_session_rotated(self, *, session_token_hash, now):
        self.events.append("mark_session_rotated")
        self.rotate_calls.append(SimpleNamespace(session_token_hash=session_token_hash, now=now))
        return self.rotated_session

    async def revoke_session_hash(self, *, session_token_hash, now):
        self.events.append("revoke_session_hash")
        self.revoke_calls.append(SimpleNamespace(session_token_hash=session_token_hash, now=now))


class FakeUserRepository:
    def __init__(self, users=None, session=None, events=None):
        self.users_by_id = {user.id: user for user in users or []}
        self.session = session
        self.events = events if events is not None else []
        self.get_by_id_calls = []
        self.get_by_id_in_transaction = []

    async def get_by_id(self, user_id):
        self.events.append("get_user")
        self.get_by_id_calls.append(user_id)
        if self.session is not None:
            self.get_by_id_in_transaction.append(self.session.in_transaction)
        return self.users_by_id.get(user_id)


class FakeBrowserSessionRepository:
    def __init__(
        self,
        events,
        user_id,
    ):
        self.events = events
        self.parent = SimpleNamespace(
            id=uuid4(),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
            revoked_at=None,
        )

    async def create_session(
        self,
        *,
        user_id,
        expires_at,
    ):
        self.parent.user_id = user_id
        self.parent.expires_at = expires_at
        return self.parent

    async def get_session(
        self,
        session_id,
        *,
        for_update=False,
    ):
        self.events.append("lock_parent" if for_update else "get_parent")
        return self.parent if session_id == self.parent.id else None

    async def extend_session(
        self,
        session_id,
        *,
        expires_at,
    ):
        self.events.append("extend_parent")
        assert session_id == self.parent.id
        self.parent.expires_at = expires_at

    async def revoke_session(
        self,
        session_id,
        *,
        now,
    ):
        assert session_id == self.parent.id
        self.parent.revoked_at = now


def make_user(*, is_active: bool = True):
    return SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=UserRole.EDITOR,
        is_active=is_active,
    )


def auth_user_dto(user) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        email=user.email,
        role="editor",
        is_active=user.is_active,
    )


def build_service(*, user=None, users=None, ttl_hours=12):
    session = DummySession()
    events = []
    repository_users = users if users is not None else ([user] if user is not None else [])
    session_repository = FakeAuthSessionRepository(events)
    user_repository = FakeUserRepository(repository_users, session, events)
    browser_repository = FakeBrowserSessionRepository(
        events,
        repository_users[0].id if repository_users else uuid4(),
    )
    session_repository.parent = browser_repository.parent
    service = AuthSessionService(
        session=session,
        session_repository=session_repository,
        user_repository=user_repository,
        browser_session_repository=browser_repository,
        ttl_hours=ttl_hours,
    )
    return service, session, session_repository, user_repository, events


def make_credential(
    repository,
    user_id,
):
    return SimpleNamespace(
        id=uuid4(),
        browser_session_id=repository.parent.id,
        user_id=user_id,
        session_token_hash="a" * 64,
        expires_at=repository.parent.expires_at,
        created_at=datetime.now(timezone.utc),
        revoked_at=None,
        rotated_at=None,
        last_used_at=None,
    )


def assert_auth_required(exc_info) -> None:
    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "AUTH_REQUIRED"
    assert exc_info.value.message == EXPECTED_AUTH_REQUIRED_MESSAGE


def test_hash_auth_session_token_is_sha256_hex() -> None:
    value = hash_auth_session_token("session-token")

    assert value == "c101e911469c969171040b50d70543313cf968fdef5bacc780776f8fb399ab36"
    assert len(value) == 64


def test_auth_session_service_uses_auth_user_dto_contract() -> None:
    assert get_type_hints(AuthSessionService.issue_session)["user"] is AuthUserDTO
    assert RefreshedAuthSessionOut.model_fields["user"].annotation is AuthUserDTO


def test_refresh_rejects_expected_sid_mismatch() -> None:
    user = make_user()
    service, _session, repository, _users, _events = build_service(user=user)
    repository.active_session = make_credential(
        repository,
        user.id,
    )

    with pytest.raises(AuthApiError) as error:
        asyncio.run(
            service.refresh_session(
                "old-token",
                expected_session_id=uuid4(),
            )
        )

    assert_auth_required(error)
    assert repository.created == []


def test_issue_session_creates_hash_and_12_hour_expiry() -> None:
    user = make_user()
    service, session, repository, _user_repository, _events = build_service(user=user)

    before = datetime.now(timezone.utc)
    result = asyncio.run(service.issue_session(auth_user_dto(user)))
    after = datetime.now(timezone.utc)

    assert isinstance(result, IssuedAuthSessionOut)
    assert result.token
    assert before + timedelta(hours=12) <= result.expires_at <= after + timedelta(hours=12)
    assert repository.created[0].session_token_hash == hash_auth_session_token(result.token)
    assert repository.created[0].session_token_hash != result.token
    assert repository.created[0].user_id == user.id
    assert repository.created[0].expires_at == result.expires_at
    assert repository.created[0].browser_session_id == result.session_id
    assert session.begin_calls == 1
    assert session.completed_begin_calls == 1


def test_refresh_session_rotates_old_hash_and_creates_new_session() -> None:
    user = make_user()
    service, session, repository, user_repository, events = build_service(user=user)
    old_token = "old-session-token"
    old_hash = hash_auth_session_token(old_token)
    old_session = make_credential(
        repository,
        user.id,
    )
    repository.active_session = old_session
    repository.rotated_session = old_session

    result = asyncio.run(service.refresh_session(old_token))

    assert isinstance(result, RefreshedAuthSessionOut)
    assert result.user == auth_user_dto(user)
    assert result.token
    assert result.token != old_token
    assert repository.get_active_calls[0].session_token_hash == old_hash
    assert repository.rotate_calls[0].session_token_hash == old_hash
    assert repository.created[0].session_token_hash == hash_auth_session_token(result.token)
    assert repository.created[0].session_token_hash != result.token
    assert repository.created[0].session_token_hash != old_hash
    assert repository.created[0].user_id == user.id
    assert repository.created[0].expires_at == result.expires_at
    assert result.expires_at - repository.rotate_calls[0].now == timedelta(hours=12)
    assert user_repository.get_by_id_calls == [user.id]
    assert user_repository.get_by_id_in_transaction == [True]
    assert events == [
        "get_history",
        "lock_parent",
        "get_active_session",
        "get_user",
        "mark_session_rotated",
        "create_session",
        "extend_parent",
    ]
    assert session.begin_calls == 1
    assert session.completed_begin_calls == 1


def test_refresh_session_rejects_credential_with_another_parent_owner() -> None:
    active_user = make_user()
    rotated_user = make_user()
    service, _session, repository, user_repository, _events = build_service(
        users=[active_user, rotated_user],
    )
    repository.active_session = make_credential(
        repository,
        rotated_user.id,
    )

    with pytest.raises(AuthApiError) as error:
        asyncio.run(service.refresh_session("old-session-token"))

    assert_auth_required(error)
    assert user_repository.get_by_id_calls == []
    assert repository.created == []


def test_refresh_session_rejects_missing_token_without_transaction() -> None:
    service, session, repository, _user_repository, _events = build_service()

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session(None))

    assert_auth_required(exc_info)
    assert session.begin_calls == 0
    assert repository.get_active_calls == []
    assert repository.rotate_calls == []
    assert repository.created == []


def test_refresh_session_rejects_missing_active_session() -> None:
    service, session, repository, _user_repository, _events = build_service()

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session("unknown-session-token"))

    assert_auth_required(exc_info)
    assert session.begin_calls == 1
    assert repository.rotate_calls == []
    assert repository.created == []


def test_refresh_session_rejects_replay_when_rotation_loses_race() -> None:
    user = make_user()
    service, _session, repository, user_repository, _events = build_service(user=user)
    old_token = "old-session-token"
    repository.active_session = make_credential(
        repository,
        user.id,
    )
    repository.rotated_session = None

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session(old_token))

    assert_auth_required(exc_info)
    assert repository.rotate_calls[0].session_token_hash == hash_auth_session_token(old_token)
    assert user_repository.get_by_id_calls == [user.id]
    assert repository.created == []


def test_refresh_session_rejects_missing_user_as_auth_required() -> None:
    user_id = uuid4()
    service, _session, repository, _user_repository, _events = build_service(user=None)
    old_session = make_credential(
        repository,
        user_id,
    )
    service.browser_session_repository.parent.user_id = user_id
    repository.active_session = old_session
    repository.rotated_session = old_session

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session("old-session-token"))

    assert_auth_required(exc_info)
    assert repository.rotate_calls == []
    assert repository.created == []


def test_refresh_session_rejects_inactive_user() -> None:
    user = make_user(is_active=False)
    service, _session, repository, _user_repository, _events = build_service(user=user)
    old_session = make_credential(
        repository,
        user.id,
    )
    repository.active_session = old_session
    repository.rotated_session = old_session

    with pytest.raises(AuthApiError) as exc_info:
        asyncio.run(service.refresh_session("old-session-token"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "USER_INACTIVE"
    assert exc_info.value.message == EXPECTED_USER_INACTIVE_MESSAGE
    assert repository.rotate_calls == []
    assert repository.created == []


def test_revoke_session_is_idempotent_without_token() -> None:
    service, session, repository, _user_repository, _events = build_service()

    asyncio.run(service.revoke_session(None))
    asyncio.run(service.revoke_session(""))

    assert session.begin_calls == 0
    assert repository.revoke_calls == []


def test_revoke_session_hashes_token_before_repository_revoke() -> None:
    service, session, repository, _user_repository, _events = build_service()
    token = "raw-session-token"
    repository.active_session = make_credential(
        repository,
        uuid4(),
    )

    asyncio.run(service.revoke_session(token))

    assert service.browser_session_repository.parent.revoked_at is not None
    assert repository.history_calls == [hash_auth_session_token(token)]
    assert session.begin_calls == 1
    assert session.completed_begin_calls == 1


def test_get_auth_session_service_wires_repositories() -> None:
    session = DummySession()

    service = get_auth_session_service(session=session)

    assert isinstance(service, AuthSessionService)
    assert service.session is session
    assert isinstance(service.session_repository, AuthSessionRepository)
    assert service.session_repository.session is session
    assert isinstance(service.user_repository, UserRepository)
    assert service.user_repository.session is session
    assert isinstance(service.browser_session_repository, BrowserAuthSessionRepository)
    assert service.browser_session_repository.session is session
