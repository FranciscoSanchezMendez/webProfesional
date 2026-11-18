"""Comprobación mínima de conectividad con PostgreSQL.

Fase 0: se usa psycopg directamente. En la Fase 1 se sustituirá por el engine de SQLAlchemy.
"""

import psycopg


def check_database(database_url: str, timeout_seconds: int = 3) -> bool:
    try:
        with psycopg.connect(database_url, connect_timeout=timeout_seconds) as conn:
            conn.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False
