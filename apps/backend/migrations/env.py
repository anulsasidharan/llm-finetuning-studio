import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

# CI and Docker set DATABASE_URL_SYNC; alembic.ini is the local fallback.
_database_url = os.getenv("DATABASE_URL_SYNC") or config.get_main_option("sqlalchemy.url")
if not _database_url:
    raise RuntimeError(
        "DATABASE_URL_SYNC environment variable or sqlalchemy.url in alembic.ini must be set"
    )
config.set_main_option("sqlalchemy.url", _database_url)


def get_database_url() -> str:
    return config.get_main_option("sqlalchemy.url")


# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # get_section() reads the .ini file only; inject the resolved URL explicitly.
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
