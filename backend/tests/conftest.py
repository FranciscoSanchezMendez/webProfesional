"""Fixtures de base de datos.

Los tests marcados con `db` necesitan TEST_DATABASE_URL apuntando a una base cuyo nombre termine en
`_test`; si no existe se crea. Sin la variable, esos tests se omiten.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.orm import Session

from app.core.config import to_psycopg_url

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if TEST_DATABASE_URL:
        return
    skip = pytest.mark.skip(reason="requiere TEST_DATABASE_URL")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)


def alembic_config() -> Config:
    return Config(toml_file=str(BACKEND_DIR / "pyproject.toml"))


def _ensure_database(url: str) -> None:
    target = make_url(url)
    admin = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        found = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": target.database}
        )
        if not found:
            conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """Engine sobre una base de test vacía con todas las migraciones aplicadas."""
    from alembic import command

    assert TEST_DATABASE_URL is not None
    url = to_psycopg_url(TEST_DATABASE_URL)
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        pytest.exit(f"TEST_DATABASE_URL debe apuntar a una base *_test (recibido: {database!r})")
    _ensure_database(url)

    test_engine = create_engine(url)
    with test_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    with test_engine.begin() as conn:
        cfg = alembic_config()
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """Sesión dentro de una transacción que se deshace al terminar el test."""
    with engine.connect() as conn:
        trans = conn.begin()
        session = Session(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            trans.rollback()
