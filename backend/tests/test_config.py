import pytest
from pydantic import ValidationError

from app.core.config import Settings, to_psycopg_url
from app.core.normalization import normalize_email, normalize_nickname


@pytest.mark.parametrize(
    "url",
    ["postgresql://u:p@h:5432/d", "postgres://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"],
)
def test_database_url_uses_psycopg_driver(url: str) -> None:
    assert to_psycopg_url(url) == "postgresql+psycopg://u:p@h:5432/d"


def test_non_postgres_url_is_rejected() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        to_psycopg_url("sqlite:///x.db")


def test_database_url_is_not_exposed_in_repr() -> None:
    settings = Settings(database_url="postgresql://u:supersecret@h/d")
    assert "supersecret" not in repr(settings)


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_deployed_environments_require_database_url(
    environment: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(environment=environment, _env_file=None)


def test_wildcard_cors_rejected_in_production() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(environment="production", database_url="postgresql://h/d", cors_origins="*")


def test_cors_origins_parsed_from_comma_separated_string() -> None:
    settings = Settings(cors_origins="http://a.test, http://b.test,")
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_normalization() -> None:
    assert normalize_email("  Ana@Example.COM ") == "ana@example.com"
    assert normalize_nickname(" @Ana-Dev ") == "ana-dev"
