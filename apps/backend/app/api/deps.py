# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 12:15:56 2026

@author: dimon
"""

from fastapi import Depends
from db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import AuthService
from repositories.user_repository import UserRepository


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session, UserRepository(session))
