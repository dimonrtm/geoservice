# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 22:52:16 2026

@author: dimon
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .deps import get_auth_service
from core.settings import settings
from domain.exceptions.auth_api_error import AuthApiError
from models.user import User, UserRole
from schemas.auth_login_in import AuthLoginIn
from schemas.auth_me_out import AuthMeOut
from schemas.auth_success_out import AuthSuccessOut
from schemas.auth_user_out import AuthUserOut
from schemas.dev_login_in import DevLoginIn
from services.auth_service import AuthService


bearer = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
SUPPORTED_AUTH_ROLES = {role.value for role in UserRole}


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
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен недействителен или срок его действия истёк",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if cred is None or not cred.credentials:
        raise AuthApiError(401, "AUTH_REQUIRED", "Требуется вход в систему.")

    try:
        payload = decode_token(cred.credentials)
    except HTTPException as exc:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.") from exc

    if "sub" not in payload or payload.get("role") not in SUPPORTED_AUTH_ROLES:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")

    try:
        user_id = UUID(str(payload["sub"]))
    except ValueError as exc:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.") from exc

    current_user = await auth_service.get_user_by_id(user_id)
    if current_user is None:
        raise AuthApiError(401, "AUTH_REQUIRED", "Сессия недействительна.")
    if not current_user.is_active:
        raise AuthApiError(403, "USER_INACTIVE", "Учетная запись отключена.")
    return current_user


def require_editor(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.EDITOR:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Editor.",
        )
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    if user.role is not UserRole.REVIEWER:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Reviewer.",
        )
    return user


if settings.dev_auth_enabled:

    @auth_router.post("/dev-login")
    async def dev_login(
        body: DevLoginIn, auth_service: AuthService = Depends(get_auth_service)
    ) -> dict[str, Any]:
        user = await auth_service.get_dev_user(body)
        token = create_access_token(str(user.id), user.role.value)
        return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/login", response_model=AuthSuccessOut)
async def login(
    body: AuthLoginIn, auth_service: AuthService = Depends(get_auth_service)
) -> AuthSuccessOut:
    user = await auth_service.authenticate_user(body.email, body.password)
    token = create_access_token(str(user.id), user.role.value)
    return AuthSuccessOut(
        access_token=token,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
        ),
    )


@auth_router.get("/me", response_model=AuthMeOut)
async def me(user: User = Depends(get_current_user)) -> AuthMeOut:
    return AuthMeOut(
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role.value,
        )
    )
