# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 10:39:38 2026

@author: dimon
"""

from sqlalchemy.ext.asyncio import AsyncSession
from repositories.user_repository import UserRepository
from schemas.dev_login_in import DevLoginIn
from models.user import User
import os


def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_ENV")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_TTL_MIN = env_int("ACCESS_TOKEN_TTL_MIN", 30)


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
