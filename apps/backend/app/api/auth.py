# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 22:52:16 2026

@author: dimon
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.dev_login_in import DevLoginIn
from services.auth_service import AuthService
from .deps import get_auth_service
from typing import Any
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from core.settings import settings


bearer = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не валидный или устаревший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if cred is None or not cred.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(cred.credentials)

    # жёстко требуем поля, иначе 401 (иначе потом будет странная логика)
    if "sub" not in payload or "role" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_editor(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "editor":
        raise HTTPException(status_code=403, detail="Требуется роль editor")
    return user


if settings.dev_auth_enabled:

    @auth_router.post("/dev-login")
    async def dev_login(
        body: DevLoginIn, auth_service: AuthService = Depends(get_auth_service)
    ) -> dict[str, Any]:
        user = await auth_service.get_dev_user(body)
        token = create_access_token(str(user.id), user.role.value)
        return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"user_id": user["sub"], "user_role": user["role"]}
