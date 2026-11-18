import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine, inspect

import app.models  # noqa: F401
from app.db.base import Base
from app.db.health import check_database
from tests.conftest import alembic_config

pytestmark = pytest.mark.db

TABLES = {"users", "profiles", "sessions", "rate_limits"}


def test_database_is_reachable(engine: Engine) -> None:
    assert check_database(engine)


def test_models_match_migrations(engine: Engine) -> None:
    """Si falla, falta una migración: `alembic revision --autogenerate`."""
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []


def test_downgrade_and_upgrade_are_reproducible(engine: Engine) -> None:
    cfg = alembic_config()
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.downgrade(cfg, "base")
    assert TABLES.isdisjoint(inspect(engine).get_table_names())

    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
    assert TABLES <= set(inspect(engine).get_table_names())
