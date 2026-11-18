"""Configuración de la aplicación leída de variables de entorno."""

from functools import lru_cache
from typing import Annotated, Literal, Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]

_LOCAL_DATABASE_URL = "postgresql://localhost:5432/personalprofile"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Environment = "development"
    # SecretStr: la URL incluye la contraseña y no debe aparecer en logs ni repr.
    database_url: SecretStr = SecretStr(_LOCAL_DATABASE_URL)
    # Variable CORS_ORIGINS separada por comas: "http://localhost:4200,https://example.com".
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def check_deployed_environment(self) -> Self:
        if self.environment in ("staging", "production"):
            if self.database_url.get_secret_value() == _LOCAL_DATABASE_URL:
                raise ValueError(f"DATABASE_URL es obligatoria en {self.environment}")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS no admite '*' en entornos desplegados")
        return self

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "production"

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL con el driver psycopg 3 explícito (los proveedores suelen dar `postgresql://`)."""
        return to_psycopg_url(self.database_url.get_secret_value())


def to_psycopg_url(url: str) -> str:
    for prefix in ("postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url.removeprefix(prefix)
    raise ValueError("DATABASE_URL debe ser una URL de PostgreSQL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
