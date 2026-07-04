from functools import lru_cache
import json

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(..., alias="DATABASE_URL")
    cors_origins_raw: str = Field(
        "http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )
    jwt_secret: str = Field("CHANGE_ME_IN_ENV", alias="JWT_SECRET")
    jwt_alg: str = Field("HS256", alias="JWT_ALG")
    access_token_ttl_min: int = Field(30, alias="ACCESS_TOKEN_TTL_MIN")
    websocket_ticket_ttl_seconds: int = Field(60, alias="WEBSOCKET_TICKET_TTL_SECONDS")
    auth_session_ttl_hours: int = Field(12, alias="AUTH_SESSION_TTL_HOURS")
    auth_session_cookie_name: str = Field(
        "geoservice_session",
        alias="AUTH_SESSION_COOKIE_NAME",
    )
    auth_session_cookie_secure: bool = Field(
        False,
        alias="AUTH_SESSION_COOKIE_SECURE",
    )
    auth_session_cookie_samesite: str = Field(
        "lax",
        alias="AUTH_SESSION_COOKIE_SAMESITE",
    )
    dev_auth_enabled: bool = Field(False, alias="DEV_MODE")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        samesite = self.auth_session_cookie_samesite.strip().lower()
        if samesite not in {"lax", "strict", "none"}:
            raise ValueError(
                "AUTH_SESSION_COOKIE_SAMESITE должно быть одним из значений: " "lax, strict, none"
            )
        self.auth_session_cookie_samesite = samesite

        if samesite == "none" and not self.auth_session_cookie_secure:
            raise ValueError(
                "AUTH_SESSION_COOKIE_SECURE должно быть true, если "
                "AUTH_SESSION_COOKIE_SAMESITE=none"
            )

        if "*" in self.cors_origins:
            raise ValueError(
                "CORS_ORIGINS не может содержать '*', когда CORS включен "
                "с передачей учетных данных"
            )

        if self.dev_auth_enabled:
            return self

        secret = self.jwt_secret.strip()
        if not secret or secret == "CHANGE_ME_IN_ENV":
            raise ValueError(
                "JWT_SECRET должен быть явно задан и отличаться от значения "
                "по умолчанию, если DEV_MODE=false"
            )

        if not self.auth_session_cookie_secure:
            raise ValueError("AUTH_SESSION_COOKIE_SECURE должно быть true, если DEV_MODE=false")
        return self

    @property
    def cors_origins(self) -> list[str]:
        raw_value = self.cors_origins_raw.strip()
        if not raw_value:
            return []

        if raw_value.startswith("["):
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]

        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
