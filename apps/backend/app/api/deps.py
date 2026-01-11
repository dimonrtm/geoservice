# -*- coding: utf-8 -*-
"""
Created on Fri Jan  9 12:15:56 2026

@author: dimon
"""

from fastapi import Depends
from db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from services.auth_service import AuthService
from services.feature_service import FeatureService
from repositories.user_repository import UserRepository
from repositories.layer_repository import LayerRepository


def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(session, UserRepository(session))


def get_feature_service(session: AsyncSession = Depends(get_session)) -> FeatureService:
    return FeatureService(session, LayerRepository(session))
