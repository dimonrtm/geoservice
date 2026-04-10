from functools import lru_cache

from pydantic import Field, field_validator
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

    cors_origins: list[str] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def build_cors_origins(cls, value: object, info) -> list[str]:
        if isinstance(value, list) and value:
            return value

        raw_value = info.data.get("cors_origins_raw", "")
        return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
