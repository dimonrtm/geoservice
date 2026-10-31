import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from tests.integration_tests.first_save_schema_support import run_committed_scenario
from utility_service.infrastructure.postgresql.models.auth_session import AuthSession
from utility_service.infrastructure.postgresql.models.browser_auth_session import BrowserAuthSession
from utility_service.infrastructure.postgresql.models.user import User, UserRole
from utility_service.infrastructure.postgresql.repositories.browser_auth_session_repository import (
    BrowserAuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.deps import get_auth_session_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.mappers import to_auth_user_dto
from utility_service.use_cases.services.auth_service import AuthService
from utility_service.use_cases.services import auth_session_service
from utility_service.utils.passwords import hash_password


@asynccontextmanager
async def browser_context(engine):
    user_id = uuid4()
    async with AsyncSession(engine) as setup, setup.begin():
        user = await UserRepository(setup).create_user(
            email=f"ar01-{user_id}@example.local",
            role=UserRole.EDITOR,
            password_hash=hash_password("correct-password"),
            user_id=user_id,
        )
        dto = to_auth_user_dto(user)
    try:
        yield dto
    finally:
        async with AsyncSession(engine) as cleanup, cleanup.begin():
            await cleanup.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
            await cleanup.execute(
                delete(BrowserAuthSession).where(BrowserAuthSession.user_id == user_id)
            )
            await cleanup.execute(delete(User).where(User.id == user_id))


async def issue(
    engine,
    user,
    previous_token=None,
):
    async with AsyncSession(engine) as session:
        return await get_auth_session_service(session).issue_session(
            user,
            previous_token=previous_token,
        )


async def refresh(
    engine,
    token,
    expected_session_id=None,
):
    async with AsyncSession(engine) as session:
        return await get_auth_session_service(session).refresh_session(
            token,
            expected_session_id=expected_session_id,
        )


async def reject_refresh(
    engine,
    token,
):
    with pytest.raises(AuthApiError) as error:
        await refresh(
            engine,
            token,
        )
    assert error.value.code == "AUTH_REQUIRED"


def test_refresh_keeps_sid_and_rejects_old_token():
    async def scenario(engine):
        async with browser_context(engine) as user:
            first = await issue(
                engine,
                user,
            )
            second = await refresh(
                engine,
                first.token,
                first.session_id,
            )
            assert second.session_id == first.session_id
            assert second.token != first.token
            assert second.user == user
            await reject_refresh(
                engine,
                first.token,
            )
            third = await refresh(
                engine,
                second.token,
            )
            assert third.session_id == first.session_id
            async with AsyncSession(engine) as session:
                parent = await session.get(
                    BrowserAuthSession,
                    first.session_id,
                )
                assert parent.expires_at == third.expires_at
                assert parent.expires_at > first.expires_at

    run_committed_scenario(scenario)


def test_login_replaces_only_cookie_session():
    async def scenario(engine):
        async with browser_context(engine) as user:
            first = await issue(
                engine,
                user,
            )
            other = await issue(
                engine,
                user,
            )
            rotated = await refresh(
                engine,
                first.token,
            )
            # Cookie может содержать уже использованное поколение.
            replacement = await issue(
                engine,
                user,
                first.token,
            )
            assert len({first.session_id, other.session_id, replacement.session_id}) == 3
            await reject_refresh(
                engine,
                rotated.token,
            )
            assert (
                await refresh(
                    engine,
                    other.token,
                )
            ).session_id == other.session_id
            assert (
                await refresh(
                    engine,
                    replacement.token,
                )
            ).session_id == replacement.session_id

    run_committed_scenario(scenario)


def test_failed_password_does_not_revoke_session():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            async with AsyncSession(
                engine,
                expire_on_commit=False,
            ) as session:
                service = AuthService(
                    session,
                    UserRepository(session),
                )
                with pytest.raises(AuthApiError) as error:
                    await service.authenticate_user(
                        user.email,
                        "wrong-password",
                    )
                assert error.value.code == "INVALID_CREDENTIALS"
            assert (
                await refresh(
                    engine,
                    issued.token,
                )
            ).session_id == issued.session_id

    run_committed_scenario(scenario)


def test_refresh_rejects_expected_sid_mismatch():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            with pytest.raises(AuthApiError) as error:
                await refresh(
                    engine,
                    issued.token,
                    uuid4(),
                )
            assert error.value.code == "AUTH_REQUIRED"
            assert (
                await refresh(
                    engine,
                    issued.token,
                )
            ).session_id == issued.session_id

    run_committed_scenario(scenario)


class LockBarrierRepository(BrowserAuthSessionRepository):
    """Барьер удерживает настоящий FOR UPDATE до наблюдения блокировки конкурента."""

    def __init__(
        self,
        session,
        acquired,
        release,
    ):
        super().__init__(session)
        self.acquired = acquired
        self.release = release

    async def get_session(
        self,
        session_id,
        *,
        for_update=False,
    ):
        row = await super().get_session(
            session_id,
            for_update=for_update,
        )
        if for_update:
            self.acquired.set()
            await self.release.wait()
        return row


async def wait_for_db_block(
    engine,
    waiting_pid,
):
    async def observe():
        async with engine.connect() as connection:
            while True:
                blockers = await connection.scalar(
                    text("SELECT cardinality(pg_blocking_pids(:pid))"),
                    {"pid": waiting_pid},
                )
                if blockers:
                    return

    await asyncio.wait_for(
        observe(),
        timeout=5,
    )


async def concurrent_operations(
    engine,
    issued,
    first_operation,
    second_operation,
):
    async with engine.connect() as first_connection, engine.connect() as second_connection:
        async with (
            AsyncSession(first_connection) as first,
            AsyncSession(second_connection) as second,
        ):
            return await locked_operations(
                engine,
                issued,
                first_operation,
                second_operation,
                first,
                second,
            )


async def locked_operations(
    engine,
    issued,
    first_operation,
    second_operation,
    first,
    second,
):
    acquired = asyncio.Event()
    release = asyncio.Event()
    # PID получаем до запуска service.begin(), завершая read transaction.
    async with second.begin():
        waiting_pid = await second.scalar(text("SELECT pg_backend_pid()"))
    first_service = get_auth_session_service(first)
    first_service.browser_session_repository = LockBarrierRepository(
        first,
        acquired,
        release,
    )
    second_service = get_auth_session_service(second)

    async def invoke(
        service,
        operation,
    ):
        if operation == "refresh":
            return await service.refresh_session(issued.token)
        await service.revoke_browser_session(issued.session_id)

    first_task = asyncio.create_task(
        invoke(
            first_service,
            first_operation,
        )
    )
    second_task = None
    try:
        await asyncio.wait_for(
            acquired.wait(),
            timeout=5,
        )
        second_task = asyncio.create_task(
            invoke(
                second_service,
                second_operation,
            )
        )
        await wait_for_db_block(
            engine,
            waiting_pid,
        )
    finally:
        release.set()
        results = await asyncio.gather(
            first_task,
            *([second_task] if second_task is not None else []),
            return_exceptions=True,
        )
    return results


def test_refresh_refresh_has_one_winner():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            results = await concurrent_operations(
                engine,
                issued,
                "refresh",
                "refresh",
            )
            winner, loser = results
            assert winner.session_id == issued.session_id
            assert isinstance(
                loser,
                AuthApiError,
            )
            assert loser.code == "AUTH_REQUIRED"
            assert (
                await refresh(
                    engine,
                    winner.token,
                )
            ).session_id == issued.session_id
            await reject_refresh(
                engine,
                issued.token,
            )

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "first_operation",
    ["refresh", "logout"],
)
def test_refresh_and_logout_never_leave_active_descendant(first_operation):
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            other = await issue(
                engine,
                user,
            )
            second_operation = "logout" if first_operation == "refresh" else "refresh"
            first_result, second_result = await concurrent_operations(
                engine,
                issued,
                first_operation,
                second_operation,
            )
            if first_operation == "refresh":
                assert first_result.session_id == issued.session_id
                assert second_result is None
                await reject_refresh(
                    engine,
                    first_result.token,
                )
            else:
                assert first_result is None
                assert isinstance(
                    second_result,
                    AuthApiError,
                )
                assert second_result.code == "AUTH_REQUIRED"
            await reject_refresh(
                engine,
                issued.token,
            )
            assert (
                await refresh(
                    engine,
                    other.token,
                )
            ).session_id == other.session_id
            async with AsyncSession(engine) as session:
                parent = await session.get(
                    BrowserAuthSession,
                    issued.session_id,
                )
                assert parent.revoked_at is not None
                expiry = parent.expires_at
            # Повторный logout не продлевает сессию и сохраняет timestamp.
            async with AsyncSession(engine) as session:
                await get_auth_session_service(session).revoke_browser_session(issued.session_id)
            async with AsyncSession(engine) as session:
                parent_after = await session.get(
                    BrowserAuthSession,
                    issued.session_id,
                )
                assert parent_after.expires_at == expiry
                assert parent_after.revoked_at == parent.revoked_at

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "failure",
    ["inactive_user", "missing_user", "credential_insert"],
)
def test_failed_rotation_rolls_back_parent_and_credential(failure):
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            async with AsyncSession(engine) as setup, setup.begin():
                if failure == "inactive_user":
                    await setup.execute(
                        update(User).where(User.id == user.id).values(is_active=False)
                    )
                elif failure == "missing_user":
                    await setup.execute(delete(User).where(User.id == user.id))
            async with AsyncSession(engine) as session:
                service = get_auth_session_service(session)
                if failure == "credential_insert":

                    async def fail_insert(**kwargs):
                        raise RuntimeError("Ошибка создания credential")

                    service.session_repository.create_session = fail_insert
                expected_error = RuntimeError if failure == "credential_insert" else AuthApiError
                with pytest.raises(expected_error):
                    await service.refresh_session(issued.token)
            async with AsyncSession(engine) as check:
                parent = await check.get(
                    BrowserAuthSession,
                    issued.session_id,
                )
                credential = await check.scalar(
                    select(AuthSession).where(AuthSession.browser_session_id == issued.session_id)
                )
                assert parent.expires_at == issued.expires_at
                assert parent.revoked_at is None
                assert credential.revoked_at is None
                assert credential.rotated_at is None
                assert credential.last_used_at is None

    run_committed_scenario(scenario)


def test_failed_login_insert_keeps_previous_browser_session():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            async with AsyncSession(engine) as session:
                service = get_auth_session_service(session)

                async def fail_insert(**kwargs):
                    raise RuntimeError("Ошибка создания credential")

                service.session_repository.create_session = fail_insert
                with pytest.raises(RuntimeError):
                    await service.issue_session(
                        user,
                        previous_token=issued.token,
                    )
            assert (
                await refresh(
                    engine,
                    issued.token,
                )
            ).session_id == issued.session_id
            async with AsyncSession(engine) as check:
                parents = (
                    await check.scalars(
                        select(BrowserAuthSession).where(BrowserAuthSession.user_id == user.id)
                    )
                ).all()
                assert len(parents) == 1

    run_committed_scenario(scenario)


@pytest.mark.parametrize(
    "target",
    ["parent_expired", "credential_expired", "credential_revoked"],
)
def test_refresh_rechecks_state_after_waiting_for_parent_lock(target):
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            async with (
                engine.connect() as blocker_connection,
                engine.connect() as waiting_connection,
            ):
                async with (
                    AsyncSession(blocker_connection) as blocker,
                    AsyncSession(
                        waiting_connection,
                        expire_on_commit=False,
                    ) as waiting,
                ):
                    await waiting_state_scenario(
                        engine,
                        issued,
                        blocker,
                        waiting,
                        target,
                    )

    run_committed_scenario(scenario)


async def waiting_state_scenario(
    engine,
    issued,
    blocker,
    waiting,
    target,
):
    async with waiting.begin():
        waiting_pid = await waiting.scalar(text("SELECT pg_backend_pid()"))
        # Сохраняем stale ORM snapshot через начало следующей transaction.
        snapshot = await waiting.scalar(
            select(AuthSession).where(AuthSession.browser_session_id == issued.session_id)
        )
    async with blocker.begin():
        await BrowserAuthSessionRepository(blocker).get_session(
            issued.session_id,
            for_update=True,
        )
        task = asyncio.create_task(get_auth_session_service(waiting).refresh_session(issued.token))
        try:
            await wait_for_db_block(
                engine,
                waiting_pid,
            )
            past = datetime.now(timezone.utc) - timedelta(seconds=1)
            if target == "parent_expired":
                await blocker.execute(
                    update(BrowserAuthSession)
                    .where(BrowserAuthSession.id == issued.session_id)
                    .values(expires_at=past)
                )
            else:
                values = (
                    {"expires_at": past}
                    if target == "credential_expired"
                    else {
                        "revoked_at": datetime.now(timezone.utc),
                    }
                )
                await blocker.execute(
                    update(AuthSession)
                    .where(AuthSession.browser_session_id == issued.session_id)
                    .values(**values)
                )
        except BaseException:
            await blocker.rollback()
            await asyncio.gather(
                task,
                return_exceptions=True,
            )
            raise
    with pytest.raises(AuthApiError) as error:
        await task
    assert error.value.code == "AUTH_REQUIRED"
    assert snapshot is not None


def test_refresh_recomputes_time_after_parent_lock(monkeypatch):
    clock = [datetime.now(timezone.utc)]

    class Clock:
        @classmethod
        def now(
            cls,
            tz,
        ):
            return clock[0]

    monkeypatch.setattr(
        auth_session_service,
        "datetime",
        Clock,
    )

    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            deadline = clock[0] + timedelta(seconds=1)
            async with AsyncSession(engine) as setup, setup.begin():
                await setup.execute(
                    update(BrowserAuthSession)
                    .where(BrowserAuthSession.id == issued.session_id)
                    .values(expires_at=deadline)
                )
                await setup.execute(
                    update(AuthSession)
                    .where(AuthSession.browser_session_id == issued.session_id)
                    .values(expires_at=deadline)
                )
            async with (
                engine.connect() as holder_connection,
                engine.connect() as waiting_connection,
            ):
                async with (
                    AsyncSession(holder_connection) as holder,
                    AsyncSession(waiting_connection) as waiting,
                ):
                    async with waiting.begin():
                        pid = await waiting.scalar(text("SELECT pg_backend_pid()"))
                    async with holder.begin():
                        await BrowserAuthSessionRepository(holder).get_session(
                            issued.session_id,
                            for_update=True,
                        )
                        task = asyncio.create_task(
                            get_auth_session_service(waiting).refresh_session(issued.token)
                        )
                        try:
                            await wait_for_db_block(
                                engine,
                                pid,
                            )
                            clock[0] = deadline + timedelta(seconds=1)
                        except BaseException:
                            await holder.rollback()
                            await asyncio.gather(
                                task,
                                return_exceptions=True,
                            )
                            raise
                    with pytest.raises(AuthApiError) as error:
                        await task
                    assert error.value.code == "AUTH_REQUIRED"
            async with AsyncSession(engine) as check:
                parent = await check.get(
                    BrowserAuthSession,
                    issued.session_id,
                )
                assert parent.expires_at == deadline

    run_committed_scenario(scenario)


def test_legacy_revoke_uses_history_to_end_current_generation():
    async def scenario(engine):
        async with browser_context(engine) as user:
            issued = await issue(
                engine,
                user,
            )
            rotated = await refresh(
                engine,
                issued.token,
            )
            async with AsyncSession(engine) as session:
                service = get_auth_session_service(session)
                await service.revoke_session(issued.token)
                await service.revoke_session(issued.token)
                await service.revoke_session("unknown-cookie")
                await service.revoke_browser_session(uuid4())
            await reject_refresh(
                engine,
                rotated.token,
            )

    run_committed_scenario(scenario)
