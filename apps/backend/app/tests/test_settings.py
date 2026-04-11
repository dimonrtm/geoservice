import os

import pytest
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/geo"
os.environ["DEV_MODE"] = "true"
os.environ["JWT_SECRET"] = "local-dev-secret"

from core.settings import Settings


def test_settings_allow_dev_mode_with_local_secret() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.dev_auth_enabled is True


@pytest.mark.parametrize("jwt_secret", ["", "CHANGE_ME_IN_ENV"])
def test_settings_reject_default_or_empty_secret_when_dev_mode_disabled(jwt_secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET must be explicitly set"):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=False,
            JWT_SECRET=jwt_secret,
        )
