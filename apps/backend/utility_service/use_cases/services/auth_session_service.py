from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.infrastructure.postgresql.repositories.browser_auth_session_repository import (
    BrowserAuthSessionRepository,
)
from utility_service.use_cases.dtos import AuthUserDTO
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.mappers import to_auth_user_dto
from utility_service.use_cases.schemas.auth.issued_auth_session_out import (
    IssuedAuthSessionOut,
)
from utility_service.use_cases.schemas.auth.refreshed_auth_session_out import (
    RefreshedAuthSessionOut,
)
from utility_service.utils.settings import settings


AUTH_REQUIRED_CODE = "AUTH_REQUIRED"
AUTH_REQUIRED_MESSAGE = "Сессия недействительна."
USER_INACTIVE_CODE = "USER_INACTIVE"
USER_INACTIVE_MESSAGE = "Учетная запись отключена."


def hash_auth_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _auth_required_error() -> AuthApiError:
    return AuthApiError(
        status.HTTP_401_UNAUTHORIZED,
        AUTH_REQUIRED_CODE,
        AUTH_REQUIRED_MESSAGE,
    )


def _user_inactive_error() -> AuthApiError:
    return AuthApiError(
        status.HTTP_403_FORBIDDEN,
        USER_INACTIVE_CODE,
        USER_INACTIVE_MESSAGE,
    )


class AuthSessionService:
    def __init__(
        self,
        session: AsyncSession,
        session_repository: AuthSessionRepository,
        user_repository: UserRepository,
        browser_session_repository: BrowserAuthSessionRepository,
        ttl_hours: int | None = None,
    ):
        self.session = session
        self.session_repository = session_repository
        self.user_repository = user_repository
        self.browser_session_repository = browser_session_repository
        self.ttl_hours = ttl_hours if ttl_hours is not None else settings.auth_session_ttl_hours

    async def issue_session(
        self,
        user: AuthUserDTO,
        previous_token: str | None = None,
    ) -> IssuedAuthSessionOut:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.ttl_hours)

        async with self.session.begin():
            if previous_token:
                await self._revoke_cookie_session(previous_token)
            parent = await self.browser_session_repository.create_session(
                user_id=user.id,
                expires_at=expires_at,
            )
            session_id = parent.id
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(token),
                user_id=user.id,
                browser_session_id=session_id,
                expires_at=expires_at,
            )

        return IssuedAuthSessionOut(
            token=token,
            session_id=session_id,
            expires_at=expires_at,
        )

    async def refresh_session(
        self,
        token: str | None,
        expected_session_id: UUID | None = None,
    ) -> RefreshedAuthSessionOut:
        if not token:
            raise _auth_required_error()

        token_hash = hash_auth_session_token(token)

        async with self.session.begin():
            credential = await self.session_repository.get_session_by_hash(
                session_token_hash=token_hash,
            )
            if credential is None:
                raise _auth_required_error()
            session_id = credential.browser_session_id
            if expected_session_id is not None and expected_session_id != session_id:
                raise _auth_required_error()

            parent = await self.browser_session_repository.get_session(
                session_id,
                for_update=True,
            )
            # Время и credential перечитываются после ожидания parent lock.
            now = datetime.now(timezone.utc)
            if parent is None or parent.revoked_at is not None or parent.expires_at <= now:
                raise _auth_required_error()
            session_row = await self.session_repository.get_active_session_by_hash(
                session_token_hash=token_hash,
                now=now,
            )
            if (
                session_row is None
                or session_row.browser_session_id != session_id
                or session_row.user_id != parent.user_id
            ):
                raise _auth_required_error()

            user = await self.user_repository.get_by_id(session_row.user_id)
            if user is None:
                raise _auth_required_error()
            if not user.is_active:
                raise _user_inactive_error()

            rotated_session = await self.session_repository.mark_session_rotated(
                session_token_hash=token_hash,
                now=now,
            )
            if rotated_session is None:
                raise _auth_required_error()

            new_token = secrets.token_urlsafe(32)
            expires_at = now + timedelta(hours=self.ttl_hours)
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(new_token),
                user_id=rotated_session.user_id,
                browser_session_id=session_id,
                expires_at=expires_at,
            )
            await self.browser_session_repository.extend_session(
                session_id,
                expires_at=expires_at,
            )
            user_dto = to_auth_user_dto(user)

        return RefreshedAuthSessionOut(
            token=new_token,
            session_id=session_id,
            expires_at=expires_at,
            user=user_dto,
        )

    async def revoke_session(self, token: str | None) -> None:
        if not token:
            return

        async with self.session.begin():
            await self._revoke_cookie_session(token)

    async def _revoke_cookie_session(self, token: str) -> None:
        credential = await self.session_repository.get_session_by_hash(
            session_token_hash=hash_auth_session_token(token),
        )
        if credential is not None:
            await self._revoke_browser_session(credential.browser_session_id)

    async def _revoke_browser_session(self, session_id: UUID) -> None:
        parent = await self.browser_session_repository.get_session(
            session_id,
            for_update=True,
        )
        if parent is not None:
            await self.browser_session_repository.revoke_session(
                session_id,
                now=datetime.now(timezone.utc),
            )

    async def revoke_browser_session(self, session_id: UUID) -> None:
        async with self.session.begin():
            await self._revoke_browser_session(session_id)
