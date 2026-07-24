from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Canonical Art City production hosts (never foreign / blockchain domains)
ARTCITY_FRONTEND_ORIGIN = "https://frontend-production-6380.up.railway.app"
ARTCITY_BACKEND_ORIGIN = "https://backend-production-9533.up.railway.app"
BLOCKED_CORS_HOST_FRAGMENTS = (
    "blockchainsystem.com",
    "alltra",
    "alltraverse",
    "nova.",
    ".nova",
)


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _is_blocked_origin(origin: str) -> bool:
    lowered = origin.lower()
    return any(fragment in lowered for fragment in BLOCKED_CORS_HOST_FRAGMENTS)


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
    # Local default; production Railway sets CORS_ORIGINS to ARTCITY_FRONTEND_ORIGIN
    cors_origins: str = f"http://localhost:3000,{ARTCITY_FRONTEND_ORIGIN}"
    public_app_url: str = ARTCITY_FRONTEND_ORIGIN
    public_api_url: str = ARTCITY_BACKEND_ORIGIN
    environment: str = "development"
    auth_required: bool = True
    external_providers_enabled: bool = True
    default_admin_email: str = "admin@artcity.ai"
    default_admin_password: str = "ArtCityAdmin!2026"

    fal_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""

    asr_engine: str = "pilot"
    asr_model_name: str = "AC-KURDISH-ASR-v1"

    # Art City Edit — billing (Stripe optional; invoice path always available)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    edit_feature_publishing: bool = False
    edit_feature_trend_intelligence: bool = False
    edit_feature_multi_cam: bool = False
    # Customer signup: expose email token + phone code in API until SMTP/SMS providers are wired
    signup_expose_codes: bool = True
    signup_require_phone: bool = True
    signup_require_email_verify: bool = True
    signup_require_phone_verify: bool = True

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return _normalize_database_url(value)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_blocked_cors_origins(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        kept = [o.strip() for o in value.split(",") if o.strip() and not _is_blocked_origin(o.strip())]
        return ",".join(kept) if kept else f"http://localhost:3000,{ARTCITY_FRONTEND_ORIGIN}"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return [o for o in origins if not _is_blocked_origin(o)]


@lru_cache
def get_settings() -> Settings:
    return Settings()
