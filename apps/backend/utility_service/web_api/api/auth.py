# -*- coding: utf-8 -*-
"""
Created on Thu Jan  8 22:52:16 2026

@author: dimon
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from utility_service.use_cases.deps import (
    get_auth_service,
    get_auth_session_service,
    get_auth_session_access_service,
    get_websocket_connection_manager,
)
from utility_service.use_cases.dtos import AuthUserDTO, AuthenticatedSession
from utility_service.use_cases.domain.exceptions.auth_api_error import AuthApiError
from utility_service.use_cases.schemas.auth.auth_login_in import AuthLoginIn
from utility_service.use_cases.schemas.auth.auth_me_out import AuthMeOut
from utility_service.use_cases.schemas.auth.auth_success_out import AuthSuccessOut
from utility_service.use_cases.schemas.auth.auth_user_out import AuthUserOut
from utility_service.use_cases.schemas.auth.browser_session_in import BrowserSessionIn
from utility_service.use_cases.schemas.auth.browser_session_out import (
    BrowserSessionStatusOut,
    BrowserSessionLogoutOut,
)
from utility_service.use_cases.services.auth_session_access_service import AuthSessionAccessService
from utility_service.use_cases.services.auth_session_service import AuthSessionService
from utility_service.use_cases.services.auth_service import AuthService
from utility_service.use_cases.services.realtime_connection_manager import (
    WebSocketConnectionManager,
)
from utility_service.utils.settings import settings


bearer = HTTPBearer(auto_error=False)
auth_router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)
EDITOR_ROLE = "editor"
REVIEWER_ROLE = "reviewer"
LEGACY_GIS_API_DISABLED_CODE = "LEGACY_GIS_API_DISABLED"
LEGACY_GIS_API_DISABLED_MESSAGE = "Legacy GIS API отключен."
SESSION_COOKIE_PATH = "/api/v1/auth"


def _cookie_max_age_seconds() -> int:
    return settings.auth_session_ttl_hours * 60 * 60


def set_session_cookie(
    response: Response,
    token: str,
) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=token,
        max_age=_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.auth_session_cookie_secure,
        samesite=settings.auth_session_cookie_samesite,
        path=SESSION_COOKIE_PATH,
    )


def create_access_token(
    user_id: str,
    role: str,
    session_id: UUID,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "sid": str(session_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_min)).timestamp()),
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


async def get_auth_context(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    access_service: AuthSessionAccessService = Depends(get_auth_session_access_service),
) -> AuthenticatedSession:
    if cred is None or not cred.credentials:
        raise AuthApiError(
            401,
            "AUTH_REQUIRED",
            "Требуется вход в систему.",
        )
    return await access_service.authenticate(cred.credentials)


async def get_current_user(
    context: AuthenticatedSession = Depends(get_auth_context),
) -> AuthUserDTO:
    return context.user


def require_editor(user: AuthUserDTO = Depends(get_current_user)) -> AuthUserDTO:
    if user.role != EDITOR_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Editor.",
        )
    return user


def require_legacy_gis_editor(
    user: AuthUserDTO = Depends(get_current_user),
) -> AuthUserDTO:
    if not settings.legacy_gis_api_enabled:
        raise AuthApiError(
            status.HTTP_403_FORBIDDEN,
            LEGACY_GIS_API_DISABLED_CODE,
            LEGACY_GIS_API_DISABLED_MESSAGE,
        )
    return require_editor(user)


def require_reviewer(user: AuthUserDTO = Depends(get_current_user)) -> AuthUserDTO:
    if user.role != REVIEWER_ROLE:
        raise AuthApiError(
            403,
            "ROLE_NOT_ALLOWED",
            "Операция доступна только пользователю с ролью Reviewer.",
        )
    return user


@auth_router.post(
    "/login",
    response_model=AuthSuccessOut,
)
async def login(
    body: AuthLoginIn,
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_service: AuthService = Depends(get_auth_service),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    user = await auth_service.authenticate_user(
        body.email,
        body.password,
    )
    session = await auth_session_service.issue_session(
        user,
        previous_token=session_token,
    )
    set_session_cookie(
        response,
        session.token,
    )
    token = create_access_token(
        str(user.id),
        user.role,
        session.session_id,
    )
    return AuthSuccessOut(
        access_token=token,
        session_id=session.session_id,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role,
        ),
    )


@auth_router.post(
    "/session/refresh",
    response_model=AuthSuccessOut,
)
async def refresh_session(
    response: Response,
    expected_session_id: UUID | None = Header(
        default=None,
        alias="X-Expected-Session-Id",
    ),
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service),
) -> AuthSuccessOut:
    session = await auth_session_service.refresh_session(
        session_token,
        expected_session_id=expected_session_id,
    )
    set_session_cookie(
        response,
        session.token,
    )
    user = session.user
    token = create_access_token(
        str(user.id),
        user.role,
        session.session_id,
    )
    return AuthSuccessOut(
        access_token=token,
        session_id=session.session_id,
        token_type="bearer",
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role,
        ),
    )


@auth_router.post(
    "/logout",
    response_model=BrowserSessionLogoutOut,
)
async def logout(
    body: BrowserSessionIn,
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    access_service: AuthSessionAccessService = Depends(get_auth_session_access_service),
    connection_manager: WebSocketConnectionManager = Depends(get_websocket_connection_manager),
) -> BrowserSessionLogoutOut:
    await access_service.logout(
        body.session_id,
        cred.credentials if cred else None,
        session_token,
    )
    # Commit отзыва уже завершён; transport failure не меняет результат logout.
    try:
        await connection_manager.disconnect_session(body.session_id)
    except Exception:
        pass
    return BrowserSessionLogoutOut(session_id=body.session_id)


@auth_router.post(
    "/session/status",
    response_model=BrowserSessionStatusOut,
)
async def session_status(
    body: BrowserSessionIn,
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    session_token: str | None = Cookie(
        default=None,
        alias=settings.auth_session_cookie_name,
    ),
    access_service: AuthSessionAccessService = Depends(get_auth_session_access_service),
) -> BrowserSessionStatusOut:
    state = await access_service.status(
        body.session_id,
        cred.credentials if cred else None,
        session_token,
    )
    return BrowserSessionStatusOut(
        session_id=body.session_id,
        state=state,
    )


@auth_router.get(
    "/me",
    response_model=AuthMeOut,
)
async def me(user: AuthUserDTO = Depends(get_current_user)) -> AuthMeOut:
    return AuthMeOut(
        user=AuthUserOut(
            id=str(user.id),
            email=user.email,
            role=user.role,
        )
    )
