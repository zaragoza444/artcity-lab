from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://artcity:artcity_local@localhost:5432/artcity"
    redis_url: str = "redis://localhost:6379/0"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "artcity_minio"
    minio_secret_key: str = "artcity_minio_secret"
    minio_bucket: str = "art-city-assets"
    minio_secure: bool = False

    secret_key: str = "change-me-local-dev-secret"
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    auth_required: bool = True
    external_providers_enabled: bool = True
    default_admin_email: str = "admin@artcity.ai"
    default_admin_password: str = "ArtCityAdmin!2026"

    fal_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_database_url(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
