# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 10:39:38 2026

@author: dimon
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.utils.passwords import verify_password
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.infrastructure.postgresql.models.user import User
from utility_service.infrastructure.postgresql.repositories.user_repository import UserRepository
from utility_service.use_cases.schemas.auth.dev_login_in import DevLoginIn


class AuthService:
    def __init__(self, session: AsyncSession, user_repository: UserRepository):
        self.session = session
        self.user_repository = user_repository

    async def get_dev_user(self, body: DevLoginIn) -> User:
        async with self.session.begin():
            user = await self.user_repository.get_by_email(body.email)
            if not user:
                user = await self.user_repository.create_user(
                    email=body.email, role=body.role, password_hash=None
                )
            return user

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверная электронная почта или пароль",
                headers={"WWW-Authenticate": "Bearer"},
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
