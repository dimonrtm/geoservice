import os

import pytest
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/geo"
os.environ["DEV_MODE"] = "true"
os.environ["JWT_SECRET"] = "local-dev-secret"

from utility_service.utils.settings import Settings


def test_settings_allow_dev_mode_with_explicit_local_runtime_marker() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.dev_auth_enabled is True


def test_settings_defaults_websocket_ticket_ttl_seconds_to_60() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.websocket_ticket_ttl_seconds == 60


def test_settings_reads_websocket_ticket_ttl_seconds_from_env_alias() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        WEBSOCKET_TICKET_TTL_SECONDS=45,
    )

    assert settings.websocket_ticket_ttl_seconds == 45


@pytest.mark.parametrize("jwt_secret", ["", "CHANGE_ME_IN_ENV"])
def test_settings_reject_default_or_empty_secret_when_dev_mode_disabled(jwt_secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET must be explicitly set"):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=False,
            JWT_SECRET=jwt_secret,
        )
