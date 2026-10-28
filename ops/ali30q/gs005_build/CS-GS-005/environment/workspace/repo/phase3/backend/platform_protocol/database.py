from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine

PLATFORM_DATABASE_ENV = "NAUTILUS_PLATFORM_DATABASE_URL"


class PlatformDatabaseConfigurationError(RuntimeError):
    """Raised before a connection when the Platform database URL is absent."""


def platform_database_url() -> str:
    database_url = os.environ.get(PLATFORM_DATABASE_ENV)
    if not database_url:
        raise PlatformDatabaseConfigurationError(
            f"{PLATFORM_DATABASE_ENV} must be explicitly provided by the calling process"
        )
    return database_url


def create_platform_engine() -> Engine:
    return create_engine(platform_database_url(), pool_pre_ping=True)
