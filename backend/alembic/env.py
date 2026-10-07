from logging.config import fileConfig

from alembic import context
from sqlalchemy import Enum, String

from app.core.config import get_settings
from app.database.base import Base
import app.models  # noqa: F401 - import models so Alembic sees their metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No domain models exist in the foundation stage.  This hook is ready for them.
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", get_settings().database_url)


def compare_type(_context, _inspected_column, metadata_column, inspected_type, _metadata_type):
    """Non-native application enums deliberately persist as portable VARCHAR columns."""
    return False if isinstance(metadata_column.type, Enum) and not metadata_column.type.native_enum and isinstance(inspected_type, String) else None


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=compare_type,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import engine_from_config, pool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=compare_type)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
