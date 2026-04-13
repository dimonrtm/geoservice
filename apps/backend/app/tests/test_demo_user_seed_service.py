import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from models.user import UserRole
from services.demo_user_seed_service import DEMO_USER_SPECS, DemoUserSeedService
from services.password_service import hash_password, verify_password


class FakeSession:
    def __init__(self) -> None:
        self.flush = AsyncMock()
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def test_ensure_demo_users_creates_missing_demo_users() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_by_email.side_effect = [None, None]
    repository.create_user.side_effect = [
        SimpleNamespace(
            id=uuid4(),
            email=spec.email,
            role=spec.role,
            password_hash=hash_password(spec.password),
        )
        for spec in DEMO_USER_SPECS
    ]
    service = DemoUserSeedService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert session.begin_calls == 1
    assert len(users) == 2
    assert repository.create_user.await_count == 2
    session.flush.assert_not_awaited()


def test_ensure_demo_users_updates_existing_user_to_demo_baseline() -> None:
    session = FakeSession()
    editor = SimpleNamespace(
        id=uuid4(),
        email="editor@example.com",
        role=UserRole.VIEWER,
        password_hash=None,
    )
    viewer = SimpleNamespace(
        id=uuid4(),
        email="viewer@example.com",
        role=UserRole.VIEWER,
        password_hash=hash_password("viewer-password"),
    )
    repository = AsyncMock()
    repository.get_by_email.side_effect = [editor, viewer]
    service = DemoUserSeedService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert users == [editor, viewer]
    assert editor.role == UserRole.EDITOR
    assert verify_password("editor-password", editor.password_hash)
    assert viewer.role == UserRole.VIEWER
    assert verify_password("viewer-password", viewer.password_hash)
    session.flush.assert_awaited_once()
    repository.create_user.assert_not_awaited()


def test_ensure_demo_users_is_stable_when_demo_users_are_already_seeded() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_by_email.side_effect = [
        SimpleNamespace(
            id=uuid4(),
            email=spec.email,
            role=spec.role,
            password_hash=hash_password(spec.password),
        )
        for spec in DEMO_USER_SPECS
    ]
    service = DemoUserSeedService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert len(users) == 2
    session.flush.assert_not_awaited()
    repository.create_user.assert_not_awaited()
