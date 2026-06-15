import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

from core.passwords import hash_password, verify_password
from models.user import UserRole
from seeds.services.seed_demo_user_service import SeedDemoUserService
from seeds.specs.seed_demo_user_specs import SEED_DEMO_USER_SPECS


EXPECTED_DEMO_USERS = {
    "alexey.editor@example.local": UserRole.EDITOR,
    "bolat.editor@example.local": UserRole.EDITOR,
    "marina.reviewer@example.local": UserRole.REVIEWER,
}


class FakeSession:
    def __init__(self) -> None:
        self.flush = AsyncMock()
        self.begin_calls = 0

    @asynccontextmanager
    async def begin(self):
        self.begin_calls += 1
        yield self


def build_seeded_user(spec):
    return SimpleNamespace(
        id=spec.id,
        email=spec.email,
        role=spec.role,
        password_hash=hash_password(spec.password),
        is_active=True,
    )


def test_demo_user_specs_define_three_stable_users() -> None:
    assert {spec.email: spec.role for spec in SEED_DEMO_USER_SPECS} == EXPECTED_DEMO_USERS
    assert len({spec.id for spec in SEED_DEMO_USER_SPECS}) == 3


def test_ensure_demo_users_creates_missing_demo_users() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_by_email.side_effect = [None, None, None]
    repository.create_user.side_effect = [build_seeded_user(spec) for spec in SEED_DEMO_USER_SPECS]
    service = SeedDemoUserService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert session.begin_calls == 1
    assert len(users) == 3
    assert repository.create_user.await_count == 3
    for call, spec in zip(repository.create_user.await_args_list, SEED_DEMO_USER_SPECS):
        assert call.kwargs["user_id"] == spec.id
        assert call.kwargs["email"] == spec.email
        assert call.kwargs["role"] is spec.role
    session.flush.assert_not_awaited()


def test_seed_restores_reviewer_baseline() -> None:
    session = FakeSession()
    marina = SimpleNamespace(
        id=SEED_DEMO_USER_SPECS[2].id,
        email="marina.reviewer@example.local",
        role=UserRole.EDITOR,
        password_hash=None,
        is_active=False,
    )
    repository = AsyncMock()
    repository.get_by_email.side_effect = [
        build_seeded_user(SEED_DEMO_USER_SPECS[0]),
        build_seeded_user(SEED_DEMO_USER_SPECS[1]),
        marina,
    ]
    service = SeedDemoUserService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert users[-1] is marina
    assert marina.role is UserRole.REVIEWER
    assert verify_password("marina-reviewer-password", marina.password_hash)
    assert marina.is_active is True
    session.flush.assert_awaited_once()
    repository.create_user.assert_not_awaited()


def test_ensure_demo_users_is_stable_when_demo_users_are_already_seeded() -> None:
    session = FakeSession()
    repository = AsyncMock()
    repository.get_by_email.side_effect = [build_seeded_user(spec) for spec in SEED_DEMO_USER_SPECS]
    service = SeedDemoUserService(session, repository)

    users = asyncio.run(service.ensure_demo_users())

    assert len(users) == 3
    session.flush.assert_not_awaited()
    repository.create_user.assert_not_awaited()
