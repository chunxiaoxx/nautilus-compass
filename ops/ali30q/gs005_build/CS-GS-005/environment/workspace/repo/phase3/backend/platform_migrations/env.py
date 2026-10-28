from __future__ import annotations

from sqlalchemy import create_engine, pool

from alembic import context
from platform_protocol.database import platform_database_url
from platform_protocol.models import PlatformBase

config = context.config
target_metadata = PlatformBase.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=platform_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="platform_schema_version",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(platform_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="platform_schema_version",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
