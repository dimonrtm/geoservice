from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
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
        ttl_hours: int | None = None,
    ):
        self.session = session
        self.session_repository = session_repository
        self.user_repository = user_repository
        self.ttl_hours = ttl_hours if ttl_hours is not None else settings.auth_session_ttl_hours

    async def issue_session(self, user: Any) -> IssuedAuthSessionOut:
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.ttl_hours)

        async with self.session.begin():
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(token),
                user_id=user.id,
                expires_at=expires_at,
            )

        return IssuedAuthSessionOut(token=token, expires_at=expires_at)

    async def refresh_session(self, token: str | None) -> RefreshedAuthSessionOut:
        if not token:
            raise _auth_required_error()

        token_hash = hash_auth_session_token(token)
        now = datetime.now(timezone.utc)

        async with self.session.begin():
            session_row = await self.session_repository.get_active_session_by_hash(
                session_token_hash=token_hash,
                now=now,
            )
            if session_row is None:
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

            if rotated_session.user_id != session_row.user_id:
                user = await self.user_repository.get_by_id(rotated_session.user_id)
                if user is None:
                    raise _auth_required_error()
                if not user.is_active:
                    raise _user_inactive_error()

            new_token = secrets.token_urlsafe(32)
            expires_at = now + timedelta(hours=self.ttl_hours)
            await self.session_repository.create_session(
                session_token_hash=hash_auth_session_token(new_token),
                user_id=rotated_session.user_id,
                expires_at=expires_at,
            )

        return RefreshedAuthSessionOut(
            token=new_token,
            expires_at=expires_at,
            user=user,
        )

    async def revoke_session(self, token: str | None) -> None:
        if not token:
            return

        token_hash = hash_auth_session_token(token)
        now = datetime.now(timezone.utc)

        async with self.session.begin():
            await self.session_repository.revoke_session_hash(
                session_token_hash=token_hash,
                now=now,
            )
