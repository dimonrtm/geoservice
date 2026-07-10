from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from utility_service.infrastructure.postgresql.models.user import User, UserRole


def load_auth_user_contract():
    try:
        from utility_service.use_cases.dtos import AuthUserDTO
        from utility_service.use_cases.mappers import to_auth_user_dto
    except ModuleNotFoundError as exc:
        pytest.fail(f"Auth user DTO modules must exist: {exc}")
    return AuthUserDTO, to_auth_user_dto


@pytest.mark.parametrize(
    ("user_role", "expected_role"),
    [
        (UserRole.EDITOR, "editor"),
        (UserRole.REVIEWER, "reviewer"),
    ],
)
def test_to_auth_user_dto_maps_identity_role_and_activity(
    user_role: UserRole,
    expected_role: str,
) -> None:
    AuthUserDTO, to_auth_user_dto = load_auth_user_contract()
    user_id = uuid4()
    user = User(
        id=user_id,
        email=f"{expected_role}@example.local",
        role=user_role,
        is_active=False,
    )

    result = to_auth_user_dto(user)

    assert result == AuthUserDTO(
        id=user_id,
        email=f"{expected_role}@example.local",
        role=expected_role,
        is_active=False,
    )


def test_auth_user_dto_is_immutable() -> None:
    AuthUserDTO, _to_auth_user_dto = load_auth_user_contract()
    result = AuthUserDTO(
        id=uuid4(),
        email="editor@example.local",
        role="editor",
        is_active=True,
    )

    with pytest.raises(FrozenInstanceError):
        result.email = "changed@example.local"
