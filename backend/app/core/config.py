from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    fal_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
