import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from jose import jwt

from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.services.auth_session_access_service import AuthSessionAccessService
from utility_service.use_cases.services.auth_session_service import hash_auth_session_token
from utility_service.use_cases.tests.test_auth_session_service import DummySession
from utility_service.utils.settings import settings


class MemoryParents:
    def __init__(
        self,
        parent,
    ):
        self.parent = parent

    async def get_session(
        self,
        session_id,
        *,
        for_update=False,
    ):
        return self.parent if self.parent and self.parent.id == session_id else None

    async def revoke_session(
        self,
        session_id,
        *,
        now,
    ):
        if self.parent.id == session_id and self.parent.revoked_at is None:
            self.parent.revoked_at = now


class MemoryCredentials:
    def __init__(
        self,
        credential=None,
    ):
        self.credential = credential

    async def get_session_by_hash(
        self,
        *,
        session_token_hash,
    ):
        return self.credential if session_token_hash == hash_auth_session_token("known") else None


class MemoryUsers:
    def __init__(
        self,
        user,
    ):
        self.user = user

    async def get_by_id(
        self,
        user_id,
    ):
        return self.user if self.user and self.user.id == user_id else None


def access_fixture():
    from utility_service.infrastructure.postgresql.models.user import UserRole

    user = SimpleNamespace(
        id=uuid4(),
        email="editor@example.local",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    parent = SimpleNamespace(
        id=uuid4(),
        user_id=user.id,
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    credential = SimpleNamespace(
        browser_session_id=parent.id,
        user_id=user.id,
    )
    session = DummySession()
    service = AuthSessionAccessService(
        session,
        MemoryParents(parent),
        MemoryCredentials(credential),
        MemoryUsers(user),
    )
    return service, parent, user


def signed(
    user,
    parent,
    *,
    expired=False,
    **overrides,
):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "sid": str(parent.id),
        "role": "editor",
        "iat": int((now - timedelta(minutes=5)).timestamp()),
        "exp": int((now + timedelta(seconds=-1 if expired else 60)).timestamp()),
    }
    payload.update(overrides)
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def test_all_access_tokens_rejected_after_logout_commit():
    async def scenario():
        service, parent, user = access_fixture()
        tokens = [
            signed(
                user,
                parent,
            ),
            signed(
                user,
                parent,
            ),
        ]
        assert (await service.authenticate(tokens[0])).user.role == "reviewer"
        assert not service.session.in_transaction
        await service.logout(
            parent.id,
            tokens[0],
            None,
        )
        for token in tokens:
            with pytest.raises(AuthApiError) as error:
                await service.authenticate(token)
            assert error.value.status_code == 401
        assert (
            await service.status(
                parent.id,
                tokens[0],
                None,
            )
            == "ended"
        )

    asyncio.run(scenario())


def test_expired_jwt_can_only_read_own_status():
    async def scenario():
        service, parent, user = access_fixture()
        token = signed(
            user,
            parent,
            expired=True,
        )
        assert (
            await service.status(
                parent.id,
                token,
                None,
            )
            == "active"
        )
        for operation in (
            lambda: service.authenticate(token),
            lambda: service.logout(
                parent.id,
                token,
                None,
            ),
            lambda: service.status(
                uuid4(),
                token,
                None,
            ),
        ):
            with pytest.raises(AuthApiError):
                await operation()
        assert parent.revoked_at is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "proof",
    [None, "unknown"],
)
def test_status_requires_proof(proof):
    async def scenario():
        service, parent, _ = access_fixture()
        with pytest.raises(AuthApiError):
            await service.status(
                parent.id,
                None,
                proof,
            )

    asyncio.run(scenario())


def test_legacy_jwt_without_sid_is_rejected():
    async def scenario():
        service, parent, user = access_fixture()
        token = signed(
            user,
            parent,
            sid=None,
        )
        with pytest.raises(AuthApiError):
            await service.authenticate(token)

    asyncio.run(scenario())


def test_status_database_error_is_not_ended():
    async def scenario():
        service, parent, user = access_fixture()

        async def fail(*args, **kwargs):
            raise RuntimeError("База недоступна")

        service.browser_session_repository.get_session = fail
        with pytest.raises(RuntimeError):
            await service.status(
                parent.id,
                signed(
                    user,
                    parent,
                ),
                None,
            )

    asyncio.run(scenario())


def test_sid_read_has_no_positive_cache_and_ends_transaction():
    async def scenario():
        service, parent, user = access_fixture()
        assert await service.is_session_active(parent.id) is True
        assert not service.session.in_transaction
        user.is_active = False
        assert await service.is_session_active(parent.id) is False
        user.is_active = True
        await service.logout(
            parent.id,
            signed(
                user,
                parent,
            ),
            None,
        )
        assert await service.is_session_active(parent.id) is False
        assert await service.is_session_active(uuid4()) is False
        assert not service.session.in_transaction

    asyncio.run(scenario())


def test_logout_cannot_revoke_other_sid_and_accepts_known_rotated_cookie():
    async def scenario():
        service, parent, user = access_fixture()
        with pytest.raises(AuthApiError):
            await service.logout(
                uuid4(),
                None,
                "known",
            )
        assert parent.revoked_at is None
        await service.logout(
            parent.id,
            None,
            "known",
        )
        first = parent.revoked_at
        await service.logout(
            parent.id,
            None,
            "known",
        )
        assert parent.revoked_at == first

    asyncio.run(scenario())


@pytest.mark.parametrize("matching_cookie", [True, False])
def test_logout_accepts_matching_cookie_independently_of_expired_bearer(matching_cookie):
    async def scenario():
        service, parent, user = access_fixture()
        if not matching_cookie:
            service.session_repository.credential.browser_session_id = uuid4()
        operation = service.logout(parent.id, signed(user, parent, expired=True), "known")
        if matching_cookie:
            await operation
            assert parent.revoked_at is not None
        else:
            with pytest.raises(AuthApiError):
                await operation
            assert parent.revoked_at is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "kind",
    ["signature", "algorithm", "sub", "sid", "missing_exp", "iat_string", "iat_bool"],
)
def test_invalid_signed_claims_are_never_proof(kind):
    async def scenario():
        service, parent, user = access_fixture()
        payload = jwt.get_unverified_claims(
            signed(
                user,
                parent,
            )
        )
        secret = settings.jwt_secret
        algorithm = settings.jwt_alg
        if kind == "signature":
            secret += "wrong"
        elif kind == "algorithm":
            algorithm = "HS512" if settings.jwt_alg != "HS512" else "HS256"
        elif kind == "missing_exp":
            del payload["exp"]
        elif kind == "iat_string":
            payload["iat"] = "123"
        elif kind == "iat_bool":
            payload["iat"] = True
        else:
            payload[kind] = str(uuid4())
        token = jwt.encode(
            payload,
            secret,
            algorithm=algorithm,
        )
        for operation in (
            lambda: service.authenticate(token),
            lambda: service.status(
                parent.id,
                token,
                None,
            ),
            lambda: service.logout(
                parent.id,
                token,
                None,
            ),
        ):
            with pytest.raises(AuthApiError):
                await operation()
        assert parent.revoked_at is None

    asyncio.run(scenario())
