from alembic import context
from sqlalchemy import Connection, create_engine, pool

import app.models  # noqa: F401  registra los modelos en Base.metadata
from app.core.config import get_settings
from app.db.base import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Genera SQL sin conectar (alembic upgrade head --sql)."""
    context.configure(
        url=get_settings().sqlalchemy_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Los tests inyectan su propia conexión mediante config.attributes["connection"].
    injected: Connection | None = config.attributes.get("connection")
    if injected is not None:
        _run(injected)
        return
    engine = create_engine(get_settings().sqlalchemy_database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
