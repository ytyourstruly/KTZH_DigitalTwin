from functools import lru_cache
from typing import Literal

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    session_ttl_hours: float = 168.0
    session_cookie_name: str = "session"
    session_cookie_path: str = "/"
    session_cookie_domain: str | None = None
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cors_allow_origins: str = "http://localhost:3000"
    database_url: str = ""
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: str = "5432"
    postgres_db: str = "app"

    simulator_ingest_enabled: bool = True
    simulator_ws_url: str = "ws://127.0.0.1:8080/telemetry"
    simulator_reconnect_delay_sec: float = 3.0
    telemetry_snapshot_interval_sec: float = 1.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("session_cookie_domain", mode="before")
    @classmethod
    def empty_cookie_domain_none(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @computed_field
    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url.strip():
            return self.database_url.strip()
        if self.postgres_password:
            return (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return (
            f"postgresql+psycopg://{self.postgres_user}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
