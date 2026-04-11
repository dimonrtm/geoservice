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
    dev_auth_enabled: bool = Field(False, alias="DEV_MODE")

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.dev_auth_enabled:
            return self

        secret = self.jwt_secret.strip()
        if not secret or secret == "CHANGE_ME_IN_ENV":
            raise ValueError(
                "JWT_SECRET must be explicitly set to a non-default value when DEV_MODE=false"
            )
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
