# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 22:52:16 2026

@author: dimon
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from schemas.dev_login_in import DevLoginIn
from services.auth_service import AuthService
from .deps import get_auth_service
from typing import Any
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError


def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or v.strip() == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


DEV_MODE = env_bool("DEV_MODE", True)
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_ENV")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_TTL_MIN = env_int("ACCESS_TOKEN_TTL_MIN", 30)


bearer = HTTPBearer(auto_error=True)
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def create_access_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
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


@auth_router.post("/dev-login")
async def dev_login(
    body: DevLoginIn, auth_service: AuthService = Depends(get_auth_service)
) -> dict[str, Any]:
    if not DEV_MODE:
        print(DEV_MODE)
        raise HTTPException(status_code=404, detail="not found DEV_MODE")
    user = await auth_service.get_dev_user(body)
    token = create_access_token(str(user.id), user.role.value)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"user_id": user["sub"], "user_role": user["role"]}
