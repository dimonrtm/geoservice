from typing import cast

from utility_service.infrastructure.postgresql.models.user import User
from utility_service.use_cases.dtos import AuthRole, AuthUserDTO


def to_auth_user_dto(user: User) -> AuthUserDTO:
    return AuthUserDTO(
        id=user.id,
        email=user.email,
        role=cast(AuthRole, user.role.value),
        is_active=user.is_active,
    )
