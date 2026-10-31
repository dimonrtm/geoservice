from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.browser_auth_session_repository import (
    BrowserAuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.dtos import AuthenticatedSession
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.mappers import to_auth_user_dto
from utility_service.use_cases.services.auth_session_service import (
    _auth_required_error,
    _user_inactive_error,
    hash_auth_session_token,
)
from utility_service.utils.settings import settings


def decode_access_claims(
    token: str,
    *,
    allow_expired: bool = False,
) -> tuple[UUID, UUID]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            options={
                "verify_exp": not allow_expired,
                "require_exp": not allow_expired,
                "require_iat": True,
                "require_sub": True,
            },
        )
        if payload.get("role") not in {"editor", "reviewer"}:
            raise ValueError("Роль недействительна")
        if type(payload["exp"]) is not int or type(payload["iat"]) is not int:
            raise ValueError("Формат времени недействителен")
        return UUID(payload["sub"]), UUID(payload["sid"])
    except (JWTError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise _auth_required_error() from exc


class AuthSessionAccessService:
    def __init__(
        self,
        session: AsyncSession,
        browser_session_repository: BrowserAuthSessionRepository,
        session_repository: AuthSessionRepository,
        user_repository: UserRepository,
    ):
        self.session = session
        self.browser_session_repository = browser_session_repository
        self.session_repository = session_repository
        self.user_repository = user_repository

    async def authenticate(
        self,
        token: str,
    ) -> AuthenticatedSession:
        user_id, session_id = decode_access_claims(token)
        async with self.session.begin():
            parent = await self.browser_session_repository.get_session(session_id)
            if parent is None or parent.user_id != user_id or not self._active(parent):
                raise _auth_required_error()
            user = await self.user_repository.get_by_id(user_id)
            if user is None:
                raise _auth_required_error()
            if not user.is_active:
                raise _user_inactive_error()
            context = AuthenticatedSession(
                user=to_auth_user_dto(user),
                session_id=session_id,
            )
        return context

    @staticmethod
    def _active(parent) -> bool:
        return parent.revoked_at is None and parent.expires_at > datetime.now(timezone.utc)

    async def _owner_active(
        self,
        parent,
    ) -> bool:
        if parent is None or not self._active(parent):
            return False
        user = await self.user_repository.get_by_id(parent.user_id)
        return user is not None and user.is_active

    async def is_session_active(
        self,
        session_id: UUID,
    ) -> bool:
        """Свежая проверка уже доказанного sid для admission и отправки realtime."""
        async with self.session.begin():
            parent = await self.browser_session_repository.get_session(session_id)
            return await self._owner_active(parent)

    async def _proof(
        self,
        session_id,
        access_token,
        cookie,
        *,
        allow_expired,
        for_update=False,
    ):
        user_id = None
        if access_token:
            try:
                token_user_id, token_sid = decode_access_claims(
                    access_token,
                    allow_expired=allow_expired,
                )
                if token_sid == session_id:
                    user_id = token_user_id
            except AuthApiError:
                # Cookie является независимым proof, а не обходом срока JWT.
                pass
        parent = await self.browser_session_repository.get_session(
            session_id,
            for_update=for_update,
        )
        if user_id is not None and (parent is None or parent.user_id == user_id):
            return parent
        if cookie:
            credential = await self.session_repository.get_session_by_hash(
                session_token_hash=hash_auth_session_token(cookie),
            )
            if (
                credential is not None
                and credential.browser_session_id == session_id
                and (parent is None or parent.user_id == credential.user_id)
            ):
                return parent
        raise _auth_required_error()

    async def status(
        self,
        session_id: UUID,
        access_token: str | None,
        cookie: str | None,
    ) -> Literal["active", "ended"]:
        async with self.session.begin():
            parent = await self._proof(
                session_id,
                access_token,
                cookie,
                allow_expired=True,
            )
            return "active" if await self._owner_active(parent) else "ended"

    async def logout(
        self,
        session_id: UUID,
        access_token: str | None,
        cookie: str | None,
    ) -> None:
        async with self.session.begin():
            parent = await self._proof(
                session_id,
                access_token,
                cookie,
                allow_expired=False,
                for_update=True,
            )
            if parent is None or parent.expires_at <= datetime.now(timezone.utc):
                raise _auth_required_error()
            await self.browser_session_repository.revoke_session(
                session_id,
                now=datetime.now(timezone.utc),
            )
