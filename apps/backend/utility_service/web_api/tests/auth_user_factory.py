from uuid import UUID, uuid4

from utility_service.use_cases.dtos import AuthRole, AuthUserDTO


_parents = {}


def create_test_access_token(
    user_id,
    role,
):
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace
    from utility_service.web_api.api.auth import create_access_token

    session_id = uuid4()
    _parents[session_id] = SimpleNamespace(
        id=session_id,
        user_id=UUID(user_id),
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    return create_access_token(
        user_id,
        role,
        session_id,
    )


def access_service_for(auth_service):
    from types import SimpleNamespace
    from utility_service.use_cases.services.auth_session_access_service import (
        AuthSessionAccessService,
    )
    from utility_service.use_cases.tests.test_auth_session_service import DummySession

    class Parents:
        async def get_session(
            self,
            session_id,
            *,
            for_update=False,
        ):
            return _parents.get(session_id)

    class Users:
        async def get_by_id(
            self,
            user_id,
        ):
            user = await auth_service.get_user_by_id(user_id)
            if user is None:
                return None
            return SimpleNamespace(
                id=user.id,
                email=user.email,
                role=SimpleNamespace(value=user.role),
                is_active=user.is_active,
            )

    return AuthSessionAccessService(
        DummySession(),
        Parents(),
        None,
        Users(),
    )


def auth_user(
    role: AuthRole = "editor",
    *,
    user_id: UUID | None = None,
    is_active: bool = True,
) -> AuthUserDTO:
    resolved_user_id = user_id or uuid4()
    return AuthUserDTO(
        id=resolved_user_id,
        email=f"{role}@example.local",
        role=role,
        is_active=is_active,
    )
