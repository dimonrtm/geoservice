from utility_service.infrastructure.postgresql.models.user import User, UserRole


def test_user_role_contains_only_editor_and_reviewer() -> None:
    assert {role.value for role in UserRole} == {"editor", "reviewer"}


def test_user_is_active_by_default() -> None:
    assert User.__table__.c.is_active.default.arg is True
