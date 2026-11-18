"""Comprobación de conectividad con PostgreSQL."""

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError


def check_database(engine: Engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
