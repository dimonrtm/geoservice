from decimal import Decimal
import os

import pytest
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/geo"
os.environ["DEV_MODE"] = "true"
os.environ["JWT_SECRET"] = "local-dev-secret"

from utility_service.utils.settings import Settings, UtilityGeometryRoundingMode


def test_settings_defaults_utility_geometry_grid() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("0.0000001")
    assert (
        settings.utility_geometry_rounding_mode is UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO
    )


def test_settings_read_utility_geometry_grid_from_env_aliases() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        UTILITY_GEOMETRY_XY_RESOLUTION="0.00000025",
        UTILITY_GEOMETRY_ROUNDING_MODE="ROUND_HALF_AWAY_FROM_ZERO",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("0.00000025")
    assert (
        settings.utility_geometry_rounding_mode is UtilityGeometryRoundingMode.HALF_AWAY_FROM_ZERO
    )


def test_settings_accepts_any_large_finite_positive_resolution() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        UTILITY_GEOMETRY_XY_RESOLUTION="1E+1000",
    )

    assert settings.utility_geometry_xy_resolution == Decimal("1E+1000")


@pytest.mark.parametrize(
    "resolution",
    ["0", "-0.0000001", "NaN", "Infinity", "-Infinity", "", "not-a-number"],
)
def test_settings_reject_invalid_utility_geometry_resolution(resolution: str) -> None:
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            UTILITY_GEOMETRY_XY_RESOLUTION=resolution,
        )


@pytest.mark.parametrize(
    "rounding_mode",
    ["ROUND_HALF_UP", "round_half_away_from_zero", "ROUND_HALF_TO_EVEN"],
)
def test_settings_reject_unsupported_utility_geometry_rounding_mode(
    rounding_mode: str,
) -> None:
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            UTILITY_GEOMETRY_ROUNDING_MODE=rounding_mode,
        )


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


def test_settings_defaults_legacy_gis_api_enabled_to_false() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.legacy_gis_api_enabled is False


def test_settings_reads_legacy_gis_api_enabled_from_env_alias() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        LEGACY_GIS_API_ENABLED=True,
    )

    assert settings.legacy_gis_api_enabled is True


def test_settings_defaults_auth_session_cookie_values() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
    )

    assert settings.auth_session_ttl_hours == 12
    assert settings.auth_session_cookie_name == "geoservice_session"
    assert settings.auth_session_cookie_secure is False
    assert settings.auth_session_cookie_samesite == "lax"


def test_settings_reads_auth_session_values_from_env_aliases() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        AUTH_SESSION_TTL_HOURS=8,
        AUTH_SESSION_COOKIE_NAME="custom_session",
        AUTH_SESSION_COOKIE_SECURE=True,
        AUTH_SESSION_COOKIE_SAMESITE="strict",
    )

    assert settings.auth_session_ttl_hours == 8
    assert settings.auth_session_cookie_name == "custom_session"
    assert settings.auth_session_cookie_secure is True
    assert settings.auth_session_cookie_samesite == "strict"


def test_settings_rejects_invalid_auth_session_cookie_samesite() -> None:
    with pytest.raises(
        ValidationError,
        match="AUTH_SESSION_COOKIE_SAMESITE должно быть одним из значений",
    ):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            AUTH_SESSION_COOKIE_SAMESITE="loose",
        )


def test_settings_normalizes_auth_session_cookie_samesite_to_lowercase() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=True,
        JWT_SECRET="CHANGE_ME_IN_ENV",
        AUTH_SESSION_COOKIE_SAMESITE="Strict",
    )

    assert settings.auth_session_cookie_samesite == "strict"


def test_settings_rejects_insecure_auth_session_cookie_in_production() -> None:
    with pytest.raises(
        ValidationError,
        match="AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false",
    ):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=False,
            JWT_SECRET="production-secret",
            AUTH_SESSION_COOKIE_SECURE=False,
            AUTH_SESSION_COOKIE_SAMESITE="lax",
        )


def test_settings_allows_secure_auth_session_cookie_in_production() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
        DEV_MODE=False,
        JWT_SECRET="production-secret",
        AUTH_SESSION_COOKIE_SECURE=True,
        AUTH_SESSION_COOKIE_SAMESITE="lax",
    )

    assert settings.dev_auth_enabled is False
    assert settings.auth_session_cookie_secure is True


def test_settings_rejects_samesite_none_without_secure_cookie() -> None:
    with pytest.raises(
        ValidationError,
        match=(
            "AUTH_SESSION_COOKIE_SECURE должно быть true, если " "AUTH_SESSION_COOKIE_SAMESITE=none"
        ),
    ):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            AUTH_SESSION_COOKIE_SECURE=False,
            AUTH_SESSION_COOKIE_SAMESITE="none",
        )


def test_settings_rejects_wildcard_cors_origin_with_credentials() -> None:
    with pytest.raises(
        ValidationError,
        match=r"CORS_ORIGINS не может содержать '\*', когда CORS включен",
    ):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            CORS_ORIGINS="*",
        )


def test_settings_rejects_wildcard_cors_origin_in_json_list_with_credentials() -> None:
    with pytest.raises(
        ValidationError,
        match=r"CORS_ORIGINS не может содержать '\*', когда CORS включен",
    ):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=True,
            JWT_SECRET="CHANGE_ME_IN_ENV",
            CORS_ORIGINS='["http://localhost:5173", "*"]',
        )


@pytest.mark.parametrize("jwt_secret", ["", "CHANGE_ME_IN_ENV"])
def test_settings_reject_default_or_empty_secret_when_dev_mode_disabled(jwt_secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET должен быть явно задан"):
        Settings(
            DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geo",
            DEV_MODE=False,
            JWT_SECRET=jwt_secret,
        )
