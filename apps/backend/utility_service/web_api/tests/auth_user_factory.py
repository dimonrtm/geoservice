from uuid import UUID, uuid4

from utility_service.use_cases.dtos import AuthRole, AuthUserDTO


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
