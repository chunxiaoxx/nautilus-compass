from __future__ import annotations

from pathlib import Path

from alembic.config import Config

from alembic import command
from platform_protocol.database import platform_database_url
from platform_protocol.models import PLATFORM_PROTOCOL_TABLES

PLATFORM_MIGRATION_HEAD = "20260809_01_r1a_evidence"
PLATFORM_VERSION_TABLE = "platform_schema_version"
PLATFORM_MIGRATION_TABLES = frozenset(
    {PLATFORM_VERSION_TABLE, *PLATFORM_PROTOCOL_TABLES}
)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_MIGRATION_ROOT = _BACKEND_ROOT / "platform_migrations"


def migration_config() -> Config:
    config = Config(str(_BACKEND_ROOT / "platform_migrations.ini"))
    config.set_main_option("script_location", str(_MIGRATION_ROOT))
    return config


def upgrade_platform_database() -> None:
    platform_database_url()
    command.upgrade(migration_config(), "head")


def downgrade_platform_database() -> None:
    platform_database_url()
    command.downgrade(migration_config(), "base")
