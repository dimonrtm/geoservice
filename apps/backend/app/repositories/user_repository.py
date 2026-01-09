# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 23:25:15 2026

@author: dimon
"""

from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from sqlalchemy import select, insert


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        res = await self.session.execute(stmt)
        return res.scalars().one_or_none()

    async def create_user(
        self, email: str, role: UserRole, password_hash: str = None
    ) -> User | None:
        stmt = (
            insert(User).values(email=email, role=role, password_hash=password_hash).returning(User)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()
