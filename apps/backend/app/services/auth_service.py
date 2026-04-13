# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 10:39:38 2026

@author: dimon
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User
from repositories.user_repository import UserRepository
from schemas.dev_login_in import DevLoginIn
from services.password_service import verify_password


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
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await self.user_repository.get_by_id(user_id)
