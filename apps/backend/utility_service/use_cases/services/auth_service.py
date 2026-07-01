# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 10:39:38 2026

@author: dimon
"""

from uuid import UUID

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.utils.passwords import verify_password
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository


INVALID_CREDENTIALS_CODE = "INVALID_CREDENTIALS"
INVALID_CREDENTIALS_MESSAGE = "Неверная электронная почта или пароль"


class AuthService:
    def __init__(self, session: AsyncSession, user_repository: UserRepository):
        self.session = session
        self.user_repository = user_repository

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=INVALID_CREDENTIALS_CODE,
                message=INVALID_CREDENTIALS_MESSAGE,
            )
        if not user.is_active:
            raise AuthApiError(
                status_code=status.HTTP_403_FORBIDDEN,
                code="USER_INACTIVE",
                message="Учетная запись отключена.",
            )
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        async with self.session.begin():
            return await self.user_repository.get_by_id(user_id)
