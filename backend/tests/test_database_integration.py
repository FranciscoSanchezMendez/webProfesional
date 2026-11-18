"""Prueba contra un PostgreSQL real. Se omite si RUN_DB_TESTS no está activo."""

import os

import pytest

from app.core.config import get_settings
from app.db.health import check_database

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="requiere PostgreSQL (RUN_DB_TESTS=1)"
)


def test_database_is_reachable() -> None:
    assert check_database(get_settings().database_url)
