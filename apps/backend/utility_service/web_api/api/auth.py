# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 22:52:16 2026

@author: dimon
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from utility_service.use_cases.deps import get_auth_service, get_auth_session_service
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.auth_login_in import AuthLoginIn
from utility_service.use_cases.schemas.auth.auth_me_out import AuthMeOut
from utility_service.use_cases.schemas.auth.auth_success_out import AuthSuccessOut
from utility_service.use_cases.schemas.auth.auth_user_out import AuthUserOut
from utility_service.use_cases.services.auth_session_service import AuthSessionService
from utility_service.use_cases.services.auth_service import AuthService
from utility_service.utils.settings import settings


bearer = HTTPBearer(auto_error=False)
auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
EDITOR_ROLE = "editor"
REVIEWER_ROLE = "reviewer"
LEGACY_GIS_API_DISABLED_CODE = "LEGACY_GIS_API_DISABLED"
LEGACY_GIS_API_DISABLED_MESSAGE = "Legacy GIS API отключен."
SUPPORTED_AUTH_ROLES = {EDITOR_ROLE, REVIEWER_ROLE}
SESSION_COOKIE_PATH = "/api/v1/auth"


def _cookie_max_age_seconds() -> int:
    return settings.auth_session_ttl_hours * 60 * 60


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=token,
        max_age=_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
        path=SESSION_COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
    )


def _role_value(user: Any) -> str:
    role = getattr(user, "role", "")
    return str(getattr(role, "value", role))


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
) -> Any:
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


def require_editor(user: Any = Depends(get_current_user)) -> Any:
    if _role_value(user) != EDITOR_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Editor.",
        )
    return user


def require_legacy_gis_editor(user: Any = Depends(get_current_user)) -> Any:
    if not settings.legacy_gis_api_enabled:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            LEGACY_GIS_API_DISABLED_CODE,
            LEGACY_GIS_API_DISABLED_MESSAGE,
        )
    return require_editor(user)


def require_reviewer(user: Any = Depends(get_current_user)) -> Any:
    if _role_value(user) != REVIEWER_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Reviewer.",
        )
    return user


@auth_router.post("/login", response_model=AuthSuccessOut)
async def login(
    body: AuthLoginIn,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    user = await auth_service.authenticate_user(body.email, body.password)
    session = await auth_session_service.issue_session(user)
    set_session_cookie(response, session.token)
    token = create_access_token(str(user.id), _role_value(user))
    return AuthSuccessOut(
        access_token=token,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=_role_value(user),
        ),
    )


@auth_router.post("/session/refresh", response_model=AuthSuccessOut)
async def refresh_session(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    session = await auth_session_service.refresh_session(session_token)
    set_session_cookie(response, session.token)
    user = session.user
    token = create_access_token(str(user.id), _role_value(user))
    return AuthSuccessOut(
        access_token=token,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=_role_value(user),
        ),
    )


@auth_router.post("/logout")
async def logout(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> dict[str, bool]:
    await auth_session_service.revoke_session(session_token)
    clear_session_cookie(response)
    return {"ok": True}


@auth_router.get("/me", response_model=AuthMeOut)
async def me(user: Any = Depends(get_current_user)) -> AuthMeOut:
    return AuthMeOut(
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=_role_value(user),
        )
    )
