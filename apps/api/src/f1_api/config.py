from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://f1:f1@localhost:5432/f1"
    redis_url: str = "redis://localhost:6379/0"
    auth_issuer: str = "http://localhost:3000"
    auth_jwks_url: str = "http://localhost:3000/api/auth/jwks"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    sentry_dsn: str = ""
    # X-Forwarded-For entries appended by our proxies. Railway sends "<client>, <edge>" = 2.
    trusted_proxy_hops: int = 0
    otlp_endpoint: str = Field(default="", validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
